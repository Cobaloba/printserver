import json
import logging
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request

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
    def __init__(self, token: str):
        self._base = f"https://api.telegram.org/bot{token}"
        self._started = False

    def start(self, printer: PrinterInterface) -> None:
        if self._started:
            return
        self._started = True
        thread = threading.Thread(
            target=self._poll_loop, args=(printer,), daemon=True
        )
        thread.start()
        logger.info("Telegram bot started")

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
        if not text or not chat_id:
            return

        lower = text.lower()

        # print todo: Title | Item 1 | Item 2
        if lower.startswith("print todo:"):
            parts = text[len("print todo:"):].strip().split("|")
            title = parts[0].strip() or "TO DO"
            items = [p.strip() for p in parts[1:] if p.strip()]
            if not items:
                self._send(chat_id, "Usage: print todo: Title | Item 1 | Item 2", ctx)
                return
            try:
                print_service.print_todo(printer, title, items)
                self._send(chat_id, "Printing ✓", ctx)
            except PrinterError as e:
                self._send(chat_id, f"Printer error: {e}", ctx)

        # print: free text
        elif lower.startswith("print:"):
            body = text[len("print:"):].strip()
            if not body:
                self._send(chat_id, "Usage: print: Hello world", ctx)
                return
            try:
                print_service.print_free_text(printer, body, "medium")
                self._send(chat_id, "Printing ✓", ctx)
            except PrinterError as e:
                self._send(chat_id, f"Printer error: {e}", ctx)

        else:
            self._send(chat_id, _HELP, ctx)
