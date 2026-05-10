from app.services.printer import PrinterInterface, EscposPrinter
from app.config import PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID

_printer: PrinterInterface | None = None


def get_printer() -> PrinterInterface:
    global _printer
    if _printer is None:
        _printer = EscposPrinter(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)
    return _printer
