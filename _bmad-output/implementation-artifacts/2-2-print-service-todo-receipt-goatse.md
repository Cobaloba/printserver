# Story 2.2: Print Service — Todo, Receipt, Goatse

**Epic:** 2 — Complete Backend API
**Story:** 2.2
**Status:** review

---

## User Story

As a developer,
I want the three original print types implemented in the print service module, refactored from printertest.py,
So that existing proven print logic is available through the clean architecture.

---

## Acceptance Criteria

**AC1 — print_service.py has the three functions:**
**Given** `backend/app/services/print_service.py`
**When** reviewed
**Then** `print_todo(printer, title, items)`, `print_receipt(printer, store, items, address, phone, tax_pct)`, and `print_goatse(printer)` exist, each accepting `PrinterInterface` as first argument and containing no `escpos` imports

**AC2 — print_todo works with MockPrinter:**
**Given** `MockPrinter` and `print_todo(printer, "TO DO", ["Buy milk", "Call Bob"])`
**When** called
**Then** `mock.get_bytes_for_job()` returns a positive integer and no exception is raised

**AC3 — print_receipt works with MockPrinter:**
**Given** `MockPrinter` and `print_receipt(printer, "Harrods", [("Gold watch", 340.00)], None, None, 20)`
**When** called
**Then** the mock records calls and no exception is raised; the function does not catch `PrinterError` internally

**AC4 — PrinterError propagates:**
**Given** `pytest backend/tests/services/test_print_service.py` using `mock_printer` fixture
**When** run
**Then** all tests pass; `PrinterError` propagation is verified by configuring `MockPrinter` to raise and asserting it re-raises

---

## Files to Create

```
backend/
└── app/
│   └── services/
│       └── print_service.py    ← NEW
└── tests/
    └── services/
        └── test_print_service.py  ← NEW
```

**DO NOT modify:** `printer.py`, `main.py`, `config.py`, `exceptions.py`

---

## Implementation

### `backend/app/services/print_service.py`

```python
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
```

**Why so thin?** The formatting logic lives in `EscposPrinter` (hardware-specific) and MockPrinter records calls. `print_service.py` is the public business API — it's the layer routers import from, and it's where bytes will be reported to the RollTracker in Story 2.6 (`roll_tracker.add_bytes(printer.get_bytes_for_job())`). Keeping it thin now means that addition is a one-liner later.

**PrinterError must NOT be caught here** — it propagates to the router which converts it to HTTP 503.

---

## Context from Previous Stories

### From Story 2.1
- `MockPrinter.configure_error(exc)` sets a one-shot exception for the next print call
- `mock.get_bytes_for_job()` returns `> 0` after any successful print call
- `conftest.py` already has `mock_printer` fixture — use it directly

### From printertest.py
- `print_todo`, `print_receipt`, `print_goatse` are already implemented in `EscposPrinter` in printer.py (refactored from printertest.py logic in Story 2.1)
- print_service.py delegates to printer — no duplication of formatting logic

---

## Definition of Done

- [x] `backend/app/services/print_service.py` exists with 3 functions
- [x] No `escpos` import in `print_service.py`
- [x] `PrinterError` is not caught inside any print_service function
- [x] `backend/tests/services/test_print_service.py` exists and all tests pass
- [x] `pytest backend/` passes with 0 failures (18 tests)

---

## Dev Notes

_To be filled by developer during/after implementation._

---

## Dev Agent Record

### Completion Notes

- `print_service.py` is intentionally thin — delegates to `printer.print_*()` methods. Formatting logic lives in `EscposPrinter`; print_service is the layer routers import from. `roll_tracker.add_bytes()` will be added here in Story 2.6.
- `PrinterError` propagates uncaught through all three functions — verified by 3 dedicated propagation tests.
- 8 new tests (18 total), all passing. No regressions.

### File List

- `backend/app/services/print_service.py` (new)
- `backend/tests/services/test_print_service.py` (new)

### Change Log

- 2026-05-10: Created print_service.py with print_todo, print_receipt, print_goatse. 8 tests passing.
