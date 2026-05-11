import threading
from app.services.printer import PrinterInterface, EscposPrinter
from app.config import PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID

_printer: PrinterInterface | None = None
_status_cache = None
_roll_tracker = None
_telegram_bot = None
_init_lock = threading.Lock()


def get_printer() -> PrinterInterface:
    global _printer
    if _printer is None:
        with _init_lock:
            if _printer is None:
                _printer = EscposPrinter(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)
    return _printer


def get_status_cache():
    global _status_cache
    if _status_cache is None:
        with _init_lock:
            if _status_cache is None:
                from app.services.status_cache import StatusCache
                _status_cache = StatusCache()
    return _status_cache


def set_telegram_bot(bot) -> None:
    global _telegram_bot
    _telegram_bot = bot


def get_telegram_bot():
    return _telegram_bot  # None if bot not configured


def get_roll_tracker():
    global _roll_tracker
    if _roll_tracker is None:
        with _init_lock:
            if _roll_tracker is None:
                from app.services.roll_tracker import RollTracker
                from app.config import DATA_DIR
                import os
                _roll_tracker = RollTracker.load(os.path.join(DATA_DIR, "roll_state.json"))
    return _roll_tracker
