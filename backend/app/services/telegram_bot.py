import json
import logging
import sqlite3
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timezone

from app.exceptions import PrinterError
from app.services import print_service
from app.services.printer import PrinterInterface

logger = logging.getLogger(__name__)


class MessageStore:
    """Persists all bot messages to a SQLite database for permanent record-keeping."""

    def __init__(self, path: str):
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_messages (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sender_name TEXT NOT NULL,
                sender_id INTEGER NOT NULL,
                text      TEXT NOT NULL,
                status    TEXT NOT NULL
            )
        """)
        self._conn.commit()
        logger.info("Message store opened at %s", path)

    def insert(self, timestamp: str, sender_name: str, sender_id: int, text: str, status: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO bot_messages (timestamp, sender_name, sender_id, text, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (timestamp, sender_name, sender_id, text, status),
            )
            self._conn.commit()

    def get_messages(self, offset: int = 0, limit: int = 20) -> tuple[list[dict], int]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT timestamp, sender_name, sender_id, text, status "
                "FROM bot_messages ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            total = self._conn.execute("SELECT COUNT(*) FROM bot_messages").fetchone()[0]
        messages = [
            {"timestamp": r[0], "sender_name": r[1], "sender_id": r[2], "text": r[3], "status": r[4]}
            for r in rows
        ]
        return messages, total

_HELP = (
    "PrintServer bot 🖨️\n\n"
    "print: <text>  — print free text\n"
    "print todo: <title> | <item1> | <item2>  — print a todo list"
)


class TelegramBot:
    def __init__(self, token: str, allowed_ids: set[int] | None = None, db_path: str | None = None):
        self._base = f"https://api.telegram.org/bot{token}"
        self._started = False
        self._allowed_ids = allowed_ids  # None = open to all
        self._log: deque = deque(maxlen=20)
        self._log_lock = threading.Lock()
        self._store = MessageStore(db_path) if db_path else None

    def get_log(self) -> list:
        with self._log_lock:
            return list(reversed(self._log))  # newest first

    def get_stored_messages(self, page: int = 1, per_page: int = 20) -> dict:
        """Return a paginated page from the persistent DB (newest first)."""
        offset = (page - 1) * per_page
        if self._store:
            messages, total = self._store.get_messages(offset=offset, limit=per_page)
        else:
            all_msgs = self.get_log()
            total = len(all_msgs)
            messages = all_msgs[offset:offset + per_page]
        return {"messages": messages, "total": total, "page": page, "per_page": per_page}

    def _record(self, sender_name: str, sender_id: int, text: str, status: str) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sender_name": sender_name,
            "sender_id": sender_id,
            "text": text,
            "status": status,
        }
        with self._log_lock:
            self._log.append(entry)
        if self._store:
            self._store.insert(entry["timestamp"], sender_name, sender_id, text, status)

    def start(self, printer: PrinterInterface) -> None:
        if self._started:
            return
        self._started = True
        thread = threading.Thread(
            target=self._poll_loop, args=(printer,), daemon=True
        )
        thread.start()
        logger.info("Telegram bot started (allowed_ids=%s)", self._allowed_ids)

    def _poll_loop(self, printer: PrinterInterface) -> None:
        offset = 0
        ctx = ssl.create_default_context()
        while True:
            try:
                updates = self._get_updates(offset, ctx)
                for update in updates:
                    offset = update["update_id"] + 1
                    self._handle_update(update, printer, ctx)
            except Exception as e:
                logger.debug("Telegram poll error: %s", e)

    def _get_updates(self, offset: int, ctx) -> list:
        url = f"{self._base}/getUpdates?offset={offset}&timeout=30"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=35, context=ctx) as resp:
            return json.loads(resp.read()).get("result", [])

    def _send(self, chat_id: int, text: str, ctx) -> None:
        url = f"{self._base}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(url, data=data)
        try:
            with urllib.request.urlopen(req, timeout=10, context=ctx):
                pass
        except Exception as e:
            logger.debug("Telegram send failed: %s", e)

    def _handle_update(self, update: dict, printer: PrinterInterface, ctx) -> None:
        message = update.get("message", {})
        text = (message.get("text") or "").strip()
        chat_id = message.get("chat", {}).get("id")
        sender = message.get("from", {})
        sender_id = sender.get("id", 0)
        sender_name = sender.get("first_name") or sender.get("username") or str(sender_id)

        if not text or not chat_id:
            return

        # Allowlist check — silent drop if not permitted
        if self._allowed_ids is not None and sender_id not in self._allowed_ids:
            self._record(sender_name, sender_id, text, "not_allowed")
            return

        lower = text.lower()

        # print todo: Title | Item 1 | Item 2
        if lower.startswith("print todo:"):
            parts = text[len("print todo:"):].strip().split("|")
            title = parts[0].strip() or "TO DO"
            items = [p.strip() for p in parts[1:] if p.strip()]
            if not items:
                self._send(chat_id, "Usage: print todo: Title | Item 1 | Item 2", ctx)
                self._record(sender_name, sender_id, text, "help")
                return
            try:
                print_service.print_todo(printer, title, items)
                self._send(chat_id, "Printing ✓", ctx)
                self._record(sender_name, sender_id, text, "printed")
            except PrinterError as e:
                self._send(chat_id, f"Printer error: {e}", ctx)
                self._record(sender_name, sender_id, text, "error")

        # print: free text
        elif lower.startswith("print:"):
            body = text[len("print:"):].strip()
            if not body:
                self._send(chat_id, "Usage: print: Hello world", ctx)
                self._record(sender_name, sender_id, text, "help")
                return
            try:
                print_service.print_free_text(printer, body, "medium")
                self._send(chat_id, "Printing ✓", ctx)
                self._record(sender_name, sender_id, text, "printed")
            except PrinterError as e:
                self._send(chat_id, f"Printer error: {e}", ctx)
                self._record(sender_name, sender_id, text, "error")

        else:
            self._send(chat_id, _HELP, ctx)
            self._record(sender_name, sender_id, text, "help")
