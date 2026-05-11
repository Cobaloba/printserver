from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

# ── Goatse data (static, lives here to avoid circular imports with print_service) ──

_GOATSE = """\
* g o a t s e x * g o a t s e x * g o a t s e x *
g                                               g
o /     \\             \\            /    \\       o
a|       |             \\          |      |      a
t|       `.             |         |       :     t
s`        |             |        \\|       |     s
e \\       | /       /  \\\\\\   --__ \\\\       :    e
x  \\      \\/   _--~~          ~--__| \\     |    x
*   \\      \\_-~                    ~-_\\    |    *
g    \\_     \\        _.--------.______\\|   |    g
o      \\     \\______// _ ___ _ (_(__>  \\   |    o
a       \\   .  C ___)  ______ (_(____>  |  /    a
t       /\\ |   C ____)/      \\ (_____>  |_/     t
s      / /\\|   C_____)       |  (___>   /  \\    s
e     |   (   _C_____}\\______/  // _/ /     \\   e
x     |    \\  |__   \\\\_________// (__/       |  x
*    | \\    \\____)   `----   --'             |  *
g    |  \\_          ___\\       /_          _/ | g
o   |              /    |     |  \\            | o
a   |             |    /       \\  \\           | a
t   |          / /    |         |  \\           |t
s   |         / /      \\__/\\___/    |          |s
e  |           /        |    |       |         |e
x  |          |         |    |       |         |x
* g o a t s e x * g o a t s e x * g o a t s e x *"""


def _compress_line(line: str, target: int) -> str:
    if len(line) <= target:
        return line
    chars = list(line)
    while len(chars) > target:
        best_start, best_len = -1, 1
        i = 1
        while i < len(chars) - 1:
            if chars[i] == ' ':
                j = i
                while j < len(chars) - 1 and chars[j] == ' ':
                    j += 1
                if j - i > best_len:
                    best_len = j - i
                    best_start = i
                i = j
            else:
                i += 1
        if best_start == -1:
            chars = chars[:target - 1] + [chars[-1]]
            break
        del chars[best_start + best_len - 1]
    return ''.join(chars)


# ── Interface ──────────────────────────────────────────────────────────────────

class PrinterInterface(ABC):
    @abstractmethod
    def print_todo(self, title: str, items: list[str]) -> None: ...

    @abstractmethod
    def print_receipt(
        self,
        store: str,
        items: list[tuple[str, float]],
        address: str | None,
        phone: str | None,
        tax_pct: float,
    ) -> None: ...

    @abstractmethod
    def print_free_text(self, text: str, font_size: str) -> None: ...

    @abstractmethod
    def print_qr(self, url: str) -> None: ...

    @abstractmethod
    def print_goatse(self) -> None: ...

    @abstractmethod
    def get_status(self) -> dict: ...

    @abstractmethod
    def get_bytes_for_job(self) -> int: ...


# ── Real printer ───────────────────────────────────────────────────────────────

def _make_usb(vendor_id: int, product_id: int):
    """
    Returns a byte-counting subclass of escpos.Usb.
    Import is deferred so escpos is only loaded when actually connecting.
    """
    from escpos.printer import Usb  # sole import point for escpos in this codebase

    class _CountingUsb(Usb):
        def __init__(self):
            self._bytes_written = 0
            super().__init__(vendor_id, product_id)
            self._bytes_written = 0  # discard bytes sent during device initialisation

        def reset_counter(self) -> None:
            self._bytes_written = 0

        def _raw(self, msg: bytes) -> None:
            self._bytes_written += len(msg)
            super()._raw(msg)

    return _CountingUsb()


class EscposPrinter(PrinterInterface):
    LINE_WIDTH = 32

    def __init__(self, vendor_id: int, product_id: int):
        import threading
        from app.exceptions import PrinterError
        self._lock = threading.Lock()
        self._last_job_bytes: int = 0
        try:
            self._p = _make_usb(vendor_id, product_id)
        except Exception as e:
            raise PrinterError(f"Failed to connect to printer: {e}") from e

    def _run(self, fn):
        from app.exceptions import PrinterError
        with self._lock:
            self._p.reset_counter()
            try:
                fn()
            except Exception as e:
                logger.warning("Printer error: %s", e)
                self._last_job_bytes = 0
                raise PrinterError(str(e) or repr(e)) from e
            self._last_job_bytes = self._p._bytes_written

    def print_todo(self, title: str, items: list[str]) -> None:
        lw = self.LINE_WIDTH

        def _():
            p = self._p
            dbl = len(title) <= lw // 2
            p.set(align='center', bold=True, height=2 if dbl else 1, width=2 if dbl else 1, font='a')
            p.text(title + '\n')
            p.set(align='left', bold=False, height=1, width=1)
            p.text('\n' + '-' * lw + '\n')
            for item in items:
                prefix = '[ ] '
                max_text = lw - len(prefix)
                p.text(f'{prefix}{item[:max_text]}\n')
                remainder = item[max_text:]
                indent = ' ' * len(prefix)
                while remainder:
                    p.text(f'{indent}{remainder[:max_text]}\n')
                    remainder = remainder[max_text:]
                p.text('\n')
            p.text('-' * lw + '\n\n\n')
            p.cut()

        self._run(_)

    def print_receipt(self, store: str, items: list[tuple[str, float]], address: str | None, phone: str | None, tax_pct: float) -> None:
        from datetime import datetime
        import random
        lw = self.LINE_WIDTH

        def _row(left: str, right: str) -> str:
            gap = lw - len(left) - len(right)
            if gap < 1:
                left = left[:lw - len(right) - 1]
                gap = 1
            return f'{left}{" " * gap}{right}'

        def _():
            p = self._p
            dbl = len(store) <= lw // 2
            p.set(align='center', bold=True, height=2 if dbl else 1, width=2 if dbl else 1, font='a')
            p.text(store + '\n')
            p.set(align='center', bold=False, height=1, width=1)
            if address:
                for part in address.split(','):
                    p.text(part.strip() + '\n')
            if phone:
                p.text(phone + '\n')
            p.text('\n')
            p.set(align='left')
            now = datetime.now()
            p.text(f'Date:    {now.strftime("%d/%m/%Y %H:%M")}\n')
            p.text(f'Receipt: #{random.randint(10000, 99999)}\n')
            p.text('-' * lw + '\n')
            subtotal = 0.0
            for name, price in items:
                p.text(_row(name, f'£{price:.2f}') + '\n')
                subtotal += price
            p.text('-' * lw + '\n')
            if tax_pct > 0:
                tax = subtotal * tax_pct / 100
                total = subtotal + tax
                p.text(_row('Subtotal', f'£{subtotal:.2f}') + '\n')
                p.text(_row(f'Tax ({tax_pct}%)', f'£{tax:.2f}') + '\n')
                p.text('-' * lw + '\n')
            else:
                total = subtotal
            p.set(bold=True)
            p.text(_row('TOTAL', f'£{total:.2f}') + '\n')
            p.set(bold=False, align='center')
            p.text('\nThank you for your visit!\n\n\n')
            p.cut()

        self._run(_)

    def print_free_text(self, text: str, font_size: str) -> None:
        def _():
            p = self._p
            if font_size == 'small':
                p.set(align='left', font='b')           # font B is physically smaller
            elif font_size == 'large':
                p.set(align='left', font='a', custom_size=True, width=2, height=2)
            else:                                        # medium (default)
                p.set(align='left', font='a')
            p.text(text + '\n\n\n')
            p.cut()

        self._run(_)

    def print_qr(self, url: str) -> None:
        # Always use raster image — native p.qr() partially executes on this
        # printer before raising, leaving USB in a corrupt state (Errno 5).
        # box_size=6 keeps the image under ~200px wide; avoids buffer overflow.
        def _():
            import qrcode  # transitive dep of python-escpos
            qr = qrcode.QRCode(border=2, box_size=6)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            p = self._p
            p.set(align='center')
            p.image(img.get_image())
            p.text('\n' + url + '\n\n\n')
            p.cut()

        self._run(_)

    def print_goatse(self) -> None:
        def _():
            p = self._p
            p.set(align='left', bold=False, height=1, width=1, font='b')
            for line in _GOATSE.split('\n'):
                p.text(_compress_line(line, 42) + '\n')
            p.text('\n\n\n')
            p.cut()

        self._run(_)

    def get_status(self) -> dict:
        from app.exceptions import PrinterError
        try:
            ps = self._p.paper_status()
            return {
                "printer_online": True,
                "paper_near_end": ps == 1,
                "paper_out": ps == 0,
            }
        except Exception as e:
            raise PrinterError(f"Status check failed: {e}") from e

    def get_bytes_for_job(self) -> int:
        return self._last_job_bytes


# ── Mock printer ───────────────────────────────────────────────────────────────

class MockPrinter(PrinterInterface):
    """In-memory printer for tests. Records all calls; no hardware required."""

    def __init__(self):
        self._calls: list[tuple[str, tuple, dict]] = []
        self._last_bytes: int = 0
        self._raise_on_print: Exception | None = None
        self._raise_on_status: Exception | None = None

    def configure_error(self, exc: Exception) -> None:
        """Make the next print call raise exc — for testing error propagation."""
        self._raise_on_print = exc

    def configure_status_error(self, exc: Exception) -> None:
        """Make the next get_status call raise exc — for testing status polling."""
        self._raise_on_status = exc

    def _record(self, method: str, *args) -> None:
        if self._raise_on_print is not None:
            exc = self._raise_on_print
            self._raise_on_print = None
            raise exc
        self._calls.append((method, args, {}))
        self._last_bytes = max(100, sum(len(str(a)) for a in args) * 4)

    def print_todo(self, title: str, items: list[str]) -> None:
        self._record("print_todo", title, items)

    def print_receipt(self, store: str, items: list[tuple[str, float]], address: str | None, phone: str | None, tax_pct: float) -> None:
        self._record("print_receipt", store, items, address, phone, tax_pct)

    def print_free_text(self, text: str, font_size: str) -> None:
        self._record("print_free_text", text, font_size)

    def print_qr(self, url: str) -> None:
        self._record("print_qr", url)

    def print_goatse(self) -> None:
        self._record("print_goatse")

    def get_status(self) -> dict:
        if self._raise_on_status is not None:
            exc = self._raise_on_status
            self._raise_on_status = None
            raise exc
        return {"printer_online": True, "paper_near_end": False, "paper_out": False}

    def get_bytes_for_job(self) -> int:
        return self._last_bytes
