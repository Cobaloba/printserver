import json
import logging
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

_HELP = (
    "PrintServer bot 🖨️\n\n"
    "print: <text>  — print free text\n"
    "print todo: <title> | <item1> | <item2>  — print a todo list"
)


class TelegramBot:
    def __init__(self, token: str, allowed_ids: set[int] | None = None):
        self._base = f"https://api.telegram.org/bot{token}"
        self._started = False
        self._allowed_ids = allowed_ids  # None = open to all
        self._log: deque = deque(maxlen=20)
        self._log_lock = threading.Lock()

    def get_log(self) -> list:
        with self._log_lock:
            return list(reversed(self._log))  # newest first

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
