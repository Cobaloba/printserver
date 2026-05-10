# Story 2.3: Print Service — Free Text, QR Code

**Epic:** 2 — Complete Backend API
**Story:** 2.3
**Status:** review

---

## User Story

As a developer,
I want free text and QR code print types added to the print service,
So that all 5 V1 print types are available from the service layer.

---

## Acceptance Criteria

**AC1 — print_service.py has free_text and qr functions:**
**Given** `print_service.py` after this story
**When** reviewed
**Then** `print_free_text(printer, text, font_size)` and `print_qr(printer, url)` exist

**AC2 — font_size maps to different multipliers:**
**Given** `font_size` values `"small"`, `"medium"`, `"large"`
**When** `print_free_text` is called with each
**Then** `MockPrinter` records different height/width multiplier calls for each size

**AC3 — QR fallback to Pillow raster:**
**Given** `print_qr(printer, 'https://example.com')`
**When** the native QR escpos command is unavailable (raises)
**Then** `EscposPrinter.print_qr()` falls back to rendering the QR code as a Pillow raster image

**AC4 — All 5 print service functions tested:**
**Given** all 5 print service functions
**When** `pytest backend/tests/services/test_print_service.py` runs
**Then** all tests pass with `MockPrinter`

---

## Files to Modify / Create

```
backend/
├── app/
│   └── services/
│       ├── print_service.py    ← UPDATE (add 2 functions)
│       └── printer.py          ← UPDATE (add Pillow fallback to print_qr)
└── tests/
    └── services/
        └── test_print_service.py  ← UPDATE (add tests for new functions)
```

---

## Implementation

### `print_service.py` additions

```python
def print_free_text(printer: PrinterInterface, text: str, font_size: str) -> None:
    printer.print_free_text(text, font_size)


def print_qr(printer: PrinterInterface, url: str) -> None:
    printer.print_qr(url)
```

### `EscposPrinter.print_qr()` update in `printer.py`

Add Pillow fallback for printers that don't support native QR commands:

```python
def print_qr(self, url: str) -> None:
    def _():
        p = self._p
        p.set(align='center')
        try:
            p.qr(url, size=6)
        except Exception:
            # Native QR not supported — render via Pillow and send as image
            import qrcode
            qr = qrcode.QRCode(border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            p.image(img.get_image())
        p.text('\n' + url + '\n\n\n')
        p.cut()
    self._run(_)
```

`qrcode` is a transitive dependency of `python-escpos` — no new entry in `pyproject.toml` needed.

### AC2 note on font_size testing

`MockPrinter.print_free_text()` just records the call — it doesn't actually call `set()`. AC2 testing is therefore: verify the call is recorded and `get_bytes_for_job() > 0`. The font_size mapping (`"small"` → h1/w1, `"medium"` → h1/w2, `"large"` → h2/w2) is exercised by hardware testing on the Pi. The unit test verifies the value passes through correctly.

---

## Context from Previous Stories

### From Story 2.1
- `EscposPrinter.print_free_text()` already maps font_size: `{"small": (1,1), "medium": (1,2), "large": (2,2)}`
- `EscposPrinter.print_qr()` exists but has no Pillow fallback — add it in this story

### From Story 2.2
- print_service functions are thin wrappers → keep the same pattern

---

## Definition of Done

- [x] `print_service.py` has `print_free_text` and `print_qr`
- [x] `EscposPrinter.print_qr()` has Pillow fallback (try native `qr()`, except → Pillow `make_image()` + `p.image()`)
- [x] Tests for `print_free_text` (all 3 font sizes) and `print_qr` added to `test_print_service.py`
- [x] `pytest backend/` passes with 0 failures (25 tests)

---

## Dev Notes

_To be filled by developer during/after implementation._

---

## Dev Agent Record

### Completion Notes

- `print_service.print_free_text()` and `print_service.print_qr()` added — same thin delegation pattern as Story 2.2.
- `EscposPrinter.print_qr()` updated: tries `p.qr(url, size=6)` first; on any exception falls back to `qrcode` + Pillow image sent via `p.image()`. `qrcode` is a transitive dependency of `python-escpos` — no new pyproject.toml entry needed.
- 7 new tests (25 total). Font size values verified by checking MockPrinter call records.

### File List

- `backend/app/services/print_service.py` (modified — added `print_free_text`, `print_qr`)
- `backend/app/services/printer.py` (modified — Pillow fallback in `EscposPrinter.print_qr`)
- `backend/tests/services/test_print_service.py` (modified — 7 new tests)

### Change Log

- 2026-05-10: Added print_free_text and print_qr to print_service.py; added Pillow QR fallback to EscposPrinter. 25 tests passing.
