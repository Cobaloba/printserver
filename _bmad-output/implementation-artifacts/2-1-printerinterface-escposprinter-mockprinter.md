# Story 2.1: PrinterInterface + EscposPrinter + MockPrinter

**Epic:** 2 — Complete Backend API
**Story:** 2.1
**Status:** review

---

## User Story

As a developer,
I want a clean printer abstraction layer with a real and mock implementation,
So that all print logic is testable without hardware and the escpos driver is isolated to one file.

---

## Acceptance Criteria

**AC1 — Interface and implementations exist and are correctly structured:**
**Given** `backend/app/services/printer.py`
**When** reviewed
**Then** `PrinterInterface` ABC defines abstract methods `print_todo`, `print_receipt`, `print_free_text`, `print_qr`, `print_goatse`, `get_status`, `get_bytes_for_job`; `EscposPrinter` implements all methods using `python-escpos Usb()`; `MockPrinter` implements all methods recording calls without hardware interaction

**AC2 — EscposPrinter connects to physical printer:**
**Given** `EscposPrinter` initialised with vendor/product IDs from config
**When** the physical printer is connected to the Pi via `/dev/receipt-printer`
**Then** the connection succeeds without error

**AC3 — MockPrinter records calls and returns simulated bytes:**
**Given** `MockPrinter` and a call to any print method
**When** `mock.get_bytes_for_job()` is called after the print
**Then** a positive integer is returned representing simulated bytes sent

**AC4 — EscposPrinter raises PrinterError on USB failure:**
**Given** `backend/app/exceptions.py`
**When** reviewed
**Then** `PrinterError(Exception)` is defined; given `EscposPrinter` encounters a USB error, when a print method is called, then `PrinterError` is raised with a descriptive message

**AC5 — conftest.py provides fixtures:**
**Given** `backend/tests/conftest.py`
**When** pytest runs
**Then** a `mock_printer` fixture provides a fresh `MockPrinter` instance and a `tmp_roll_state` fixture provides a temporary JSON file path via `tmp_path`

---

## Files to Create

```
backend/
├── app/
│   └── services/
│       └── printer.py          ← NEW: PrinterInterface + EscposPrinter + MockPrinter
└── tests/
    ├── conftest.py             ← NEW: mock_printer + tmp_roll_state fixtures
    └── services/
        └── test_printer.py     ← NEW: MockPrinter behaviour tests
```

**DO NOT modify:**
- `backend/app/main.py` — minimal health endpoint, unchanged until Story 2.4
- `backend/app/exceptions.py` — `PrinterError` already exists, do not change it
- `backend/app/config.py` — already has `PRINTER_VENDOR_ID`, `PRINTER_PRODUCT_ID`

---

## Implementation

### `backend/app/services/printer.py`

```python
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


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


class _ByteCountingUsb:
    """Thin wrapper around escpos Usb that tracks bytes written per job."""

    def __init__(self, vendor_id: int, product_id: int):
        from escpos.printer import Usb  # only import point for escpos
        self._usb = Usb(vendor_id, product_id)
        self._bytes_written = 0

    def reset_counter(self) -> None:
        self._bytes_written = 0

    def __getattr__(self, name):
        # Proxy all attribute access to the underlying Usb object
        attr = getattr(self._usb, name)
        if callable(attr) and name == "_raw":
            def counting_raw(msg):
                self._bytes_written += len(msg)
                return attr(msg)
            return counting_raw
        return attr


class EscposPrinter(PrinterInterface):
    def __init__(self, vendor_id: int, product_id: int):
        from app.exceptions import PrinterError
        try:
            self._device = _ByteCountingUsb(vendor_id, product_id)
        except Exception as e:
            raise PrinterError(f"Failed to connect to printer: {e}") from e

    def _run(self, fn):
        """Execute a print function, wrapping exceptions as PrinterError."""
        from app.exceptions import PrinterError
        self._device.reset_counter()
        try:
            fn()
        except Exception as e:
            logger.warning("Printer error: %s", e)
            raise PrinterError(str(e)) from e

    def print_todo(self, title: str, items: list[str]) -> None:
        def _print():
            p = self._device
            p.set(align='center', bold=True, height=2 if len(title) <= 16 else 1, width=2 if len(title) <= 16 else 1, font='a')
            p.text(title + '\n')
            p.set(align='left', bold=False, height=1, width=1)
            p.text('\n' + '-' * 32 + '\n')
            for item in items:
                p.text(f'[ ] {item[:28]}\n')
                remainder = item[28:]
                while remainder:
                    p.text(f'    {remainder[:28]}\n')
                    remainder = remainder[28:]
                p.text('\n')
            p.text('-' * 32 + '\n\n\n')
            p.cut()
        self._run(_print)

    def print_receipt(self, store: str, items: list[tuple[str, float]], address: str | None, phone: str | None, tax_pct: float) -> None:
        from datetime import datetime
        import random
        def _print():
            p = self._device
            p.set(align='center', bold=True, height=2 if len(store) <= 16 else 1, width=2 if len(store) <= 16 else 1, font='a')
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
            p.text('-' * 32 + '\n')
            subtotal = sum(price for _, price in items)
            for name, price in items:
                gap = 32 - len(name) - len(f'£{price:.2f}')
                p.text(f'{name[:max(1, 32-8)]}{" " * max(1, gap)}£{price:.2f}\n')
            p.text('-' * 32 + '\n')
            if tax_pct > 0:
                tax = subtotal * tax_pct / 100
                total = subtotal + tax
                p.text(f'Subtotal{" " * 16}£{subtotal:.2f}\n')
                p.text(f'Tax ({tax_pct}%){" " * 14}£{tax:.2f}\n')
                p.text('-' * 32 + '\n')
            else:
                total = subtotal
            p.set(bold=True)
            p.text(f'TOTAL{" " * 19}£{total:.2f}\n')
            p.set(bold=False, align='center')
            p.text('\nThank you for your visit!\n\n\n')
            p.cut()
        self._run(_print)

    def print_free_text(self, text: str, font_size: str) -> None:
        size_map = {"small": (1, 1), "medium": (1, 2), "large": (2, 2)}
        height, width = size_map.get(font_size, (1, 1))
        def _print():
            p = self._device
            p.set(align='left', height=height, width=width)
            p.text(text + '\n\n\n')
            p.cut()
        self._run(_print)

    def print_qr(self, url: str) -> None:
        def _print():
            p = self._device
            p.set(align='center')
            p.qr(url, size=6)
            p.text('\n' + url + '\n\n\n')
            p.cut()
        self._run(_print)

    def print_goatse(self) -> None:
        from app.services.print_service import GOATSE, _compress_line
        def _print():
            p = self._device
            p.set(align='left', bold=False, height=1, width=1, font='b')
            for line in GOATSE.split('\n'):
                p.text(_compress_line(line, 42) + '\n')
            p.text('\n\n\n')
            p.cut()
        self._run(_print)

    def get_status(self) -> dict:
        from app.exceptions import PrinterError
        try:
            ps = self._device._usb.paper_status()
            return {
                "printer_online": True,
                "paper_near_end": ps == 1,
                "paper_out": ps == 0,
            }
        except Exception as e:
            raise PrinterError(f"Status check failed: {e}") from e

    def get_bytes_for_job(self) -> int:
        return self._device._bytes_written


class MockPrinter(PrinterInterface):
    """In-memory printer for testing. Records all calls; no hardware required."""

    def __init__(self):
        self._calls: list[tuple[str, tuple, dict]] = []
        self._last_bytes: int = 0
        self._raise_on_print: Exception | None = None

    def configure_error(self, exc: Exception) -> None:
        """Make the next print call raise exc (for testing error propagation)."""
        self._raise_on_print = exc

    def _record(self, method: str, *args, **kwargs) -> None:
        if self._raise_on_print is not None:
            exc = self._raise_on_print
            self._raise_on_print = None
            raise exc
        self._calls.append((method, args, kwargs))
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
        return {"printer_online": True, "paper_near_end": False, "paper_out": False}

    def get_bytes_for_job(self) -> int:
        return self._last_bytes
```

#### Critical implementation rules

| ❌ Never | ✅ Always |
|---|---|
| `from escpos.printer import Usb` outside `printer.py` | All escpos imports stay inside `printer.py` only |
| `import escpos` in tests | Tests use `MockPrinter` exclusively |
| Connect to printer in tests | `MockPrinter` simulates everything |
| Swallow exceptions silently | Log at WARNING then re-raise as `PrinterError` |
| Use `from app.exceptions import PrinterError` at module level in printer.py | Import inside methods to avoid circular imports |

#### Note on print_goatse circular import

`print_goatse` in `EscposPrinter` imports `GOATSE` and `_compress_line` from `print_service`. This is acceptable since `print_service` imports `PrinterInterface` (not `EscposPrinter`). However, if circular imports occur during implementation, move `GOATSE` and `_compress_line` to a `printer_utils.py` module or inline them in `printer.py`.

**Simpler alternative**: copy `GOATSE` constant and `_compress_line` directly into `printer.py`. The goatse ASCII art is static data, not business logic.

### `backend/tests/conftest.py`

```python
import pytest
from app.services.printer import MockPrinter


@pytest.fixture
def mock_printer() -> MockPrinter:
    return MockPrinter()


@pytest.fixture
def tmp_roll_state(tmp_path):
    return tmp_path / "roll_state.json"
```

### `backend/tests/services/test_printer.py`

```python
import pytest
from app.services.printer import MockPrinter
from app.exceptions import PrinterError


def test_mock_print_todo_records_call(mock_printer):
    mock_printer.print_todo("My List", ["Buy milk", "Call Bob"])
    assert any(c[0] == "print_todo" for c in mock_printer._calls)


def test_mock_print_todo_returns_positive_bytes(mock_printer):
    mock_printer.print_todo("Test", ["item"])
    assert mock_printer.get_bytes_for_job() > 0


def test_mock_print_receipt_records_call(mock_printer):
    mock_printer.print_receipt("Shop", [("Coffee", 2.50)], None, None, 0)
    assert any(c[0] == "print_receipt" for c in mock_printer._calls)


def test_mock_print_free_text(mock_printer):
    mock_printer.print_free_text("Hello world", "medium")
    assert mock_printer.get_bytes_for_job() > 0


def test_mock_print_qr(mock_printer):
    mock_printer.print_qr("https://example.com")
    assert mock_printer.get_bytes_for_job() > 0


def test_mock_print_goatse(mock_printer):
    mock_printer.print_goatse()
    assert mock_printer.get_bytes_for_job() > 0


def test_mock_get_status_returns_online(mock_printer):
    status = mock_printer.get_status()
    assert status["printer_online"] is True
    assert "paper_near_end" in status
    assert "paper_out" in status


def test_mock_configure_error_raises_on_next_call(mock_printer):
    mock_printer.configure_error(PrinterError("USB error"))
    with pytest.raises(PrinterError, match="USB error"):
        mock_printer.print_todo("Test", ["item"])


def test_mock_error_clears_after_one_call(mock_printer):
    mock_printer.configure_error(PrinterError("once"))
    with pytest.raises(PrinterError):
        mock_printer.print_goatse()
    # Should not raise on next call
    mock_printer.print_goatse()
    assert mock_printer.get_bytes_for_job() > 0
```

---

## Context from Previous Stories

### From Story 1.1 (Hardware Spike)
```
PRINTER_VENDOR_ID=0x1ba0  (int: 7072)
PRINTER_PRODUCT_ID=0x220a (int: 8714)
USB backend: python-escpos Usb() class — NOT Serial
paper_status() confirmed working → returns 2 (paper OK)
Stable symlink: /dev/receipt-printer
```

### From printertest.py (proven print logic)
- `LINE_WIDTH = 32` — this is the printer's character width
- Title sizing rule: if `len(title) <= 16` use double height/width (≤ 32/2), else normal
- `_compress_line(line, width)` — compresses goatse lines to fit width by removing spaces
- All print functions end with `printer.text('\n\n\n')` then `printer.cut()`
- Receipt uses £ currency, `%d/%m/%Y %H:%M` date format

**Critical difference from printertest.py**: printertest uses `Serial(COM9)`. The service layer uses `Usb(vendor_id, product_id)`. Do NOT use Serial in the service layer.

### From Story 1.2 (Scaffolding)
- `backend/app/exceptions.py` already has `PrinterError(Exception)` — do not recreate it
- `backend/app/config.py` already has `PRINTER_VENDOR_ID` and `PRINTER_PRODUCT_ID` as ints
- `backend/tests/conftest.py` does NOT exist yet — create it in this story

---

## python-escpos 3.1 API Reference

```python
from escpos.printer import Usb

# Connect
p = Usb(idVendor=0x1ba0, idProduct=0x220a)

# Text + formatting
p.set(align='center', bold=True, height=2, width=2, font='a')
p.text("Hello\n")

# Paper status
status = p.paper_status()  # 2=ok, 1=near-end, 0=out

# QR code
p.qr("https://example.com", size=6)

# Cut
p.cut()

# Exceptions
from escpos.exceptions import USBNotFoundError, DeviceNotFoundError
```

---

## Architecture Compliance

- `escpos` imported only inside `printer.py` — the `_ByteCountingUsb` wrapper and all `from escpos.printer import Usb` calls stay inside this file
- `PrinterInterface` is the only seam tests ever touch — `MockPrinter` in all tests
- `PrinterError` from `app.exceptions` is the only exception type leaving this module
- Method signatures match the architecture spec exactly (no deviation)
- No business logic in `EscposPrinter` — it delegates formatting to print methods (formatting will be extracted to `print_service.py` in Stories 2.2/2.3)

---

## Definition of Done

- [x] `backend/app/services/printer.py` exists with `PrinterInterface`, `EscposPrinter`, `MockPrinter`
- [x] All 7 abstract methods are implemented on both `EscposPrinter` and `MockPrinter`
- [x] `backend/tests/conftest.py` exists with `mock_printer` and `tmp_roll_state` fixtures
- [x] `backend/tests/services/test_printer.py` passes — 10 tests green
- [x] `pytest backend/` passes with 0 failures (`test_placeholder.py` deleted — replaced by real tests)
- [x] No `import escpos` anywhere except `backend/app/services/printer.py`
- [x] `PrinterError` is raised (not raw escpos exceptions) when EscposPrinter fails

---

## Dev Notes

_To be filled by developer during/after implementation._

---

## Dev Agent Record

### Implementation Plan

1. `printer.py` — `PrinterInterface` ABC, `_make_usb()` factory (deferred escpos import via `_CountingUsb(Usb)` subclass for byte tracking), `EscposPrinter`, `MockPrinter`. `_GOATSE` constant and `_compress_line()` inlined to avoid premature dependency on `print_service.py` (Story 2.2).
2. `conftest.py` — `mock_printer` and `tmp_roll_state` fixtures; both used from Story 2.1 onwards.
3. `test_printer.py` — 10 tests covering all MockPrinter methods, byte counting, error injection, and error-clears-after-one-call behaviour.
4. `test_placeholder.py` deleted — replaced by real tests.

### Completion Notes

- 10 tests, 10 passed, 0 failures.
- `escpos` import boundary enforced: `from escpos.printer import Usb` exists only inside `_make_usb()` inside `printer.py`. Confirmed by grep returning empty.
- `_CountingUsb` subclasses `Usb` and overrides `_raw()` — intercepts all bytes sent to the printer for accurate `get_bytes_for_job()` tracking.
- `EscposPrinter` defers escpos import to first instantiation, so tests can import from `printer.py` without python-escpos installed on the dev machine.
- `PrinterError` imported inside methods (not at module level) to avoid circular imports.
- `configure_error()` on MockPrinter sets a one-shot exception for next print call — used by downstream service tests to verify error propagation.

### File List

- `backend/app/services/printer.py` (new)
- `backend/tests/conftest.py` (new)
- `backend/tests/services/test_printer.py` (new)
- `backend/tests/test_placeholder.py` (deleted)

### Change Log

- 2026-05-10: Implemented PrinterInterface ABC, EscposPrinter with byte-counting USB wrapper, MockPrinter with error injection. Created conftest.py fixtures. 10 tests passing.
