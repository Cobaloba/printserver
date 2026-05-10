from app.services.printer import PrinterInterface, EscposPrinter
from app.config import PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID

_printer: PrinterInterface | None = None
_status_cache = None


def get_printer() -> PrinterInterface:
    global _printer
    if _printer is None:
        _printer = EscposPrinter(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)
    return _printer


def get_status_cache():
    global _status_cache
    if _status_cache is None:
        from app.services.status_cache import StatusCache
        _status_cache = StatusCache()
    return _status_cache
