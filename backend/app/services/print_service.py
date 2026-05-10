from app.services.printer import PrinterInterface


def print_todo(printer: PrinterInterface, title: str, items: list[str]) -> None:
    printer.print_todo(title, items)


def print_receipt(
    printer: PrinterInterface,
    store: str,
    items: list[tuple[str, float]],
    address: str | None,
    phone: str | None,
    tax_pct: float,
) -> None:
    printer.print_receipt(store, items, address, phone, tax_pct)


def print_goatse(printer: PrinterInterface) -> None:
    printer.print_goatse()


def print_free_text(printer: PrinterInterface, text: str, font_size: str) -> None:
    printer.print_free_text(text, font_size)


def print_qr(printer: PrinterInterface, url: str) -> None:
    printer.print_qr(url)
