import unicodedata

import emoji as _emoji

from app.services.printer import PrinterInterface


def sanitize_text(text: str) -> str:
    """Prepare user text for ESC/POS printing.

    1. Replaces emojis with their English name in brackets: 😀 → [grinning face]
    2. Strips diacritics via NFKD normalisation: café → cafe
    3. Drops any remaining non-ASCII characters silently.
    """
    text = _emoji.replace_emoji(
        text,
        replace=lambda ch, data: "[" + data.get("en", "?").strip(":").replace("_", " ") + "]",
    )
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _s(text: str | None) -> str | None:
    return sanitize_text(text) if text is not None else None


def print_todo(printer: PrinterInterface, title: str, items: list[str]) -> None:
    printer.print_todo(sanitize_text(title), [sanitize_text(i) for i in items])


def print_receipt(
    printer: PrinterInterface,
    store: str,
    items: list[tuple[str, float]],
    address: str | None,
    phone: str | None,
    tax_pct: float,
) -> None:
    printer.print_receipt(
        sanitize_text(store),
        [(sanitize_text(name), price) for name, price in items],
        _s(address),
        _s(phone),
        tax_pct,
    )


def print_goatse(printer: PrinterInterface) -> None:
    printer.print_goatse()


def print_free_text(printer: PrinterInterface, text: str, font_size: str) -> None:
    printer.print_free_text(sanitize_text(text), font_size)


def print_qr(printer: PrinterInterface, url: str) -> None:
    printer.print_qr(url)  # URLs are ASCII — no sanitization needed
