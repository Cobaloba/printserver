# Story 2.6: Till Roll Tracker

**Epic:** 2 — Complete Backend API
**Story:** 2.6
**Status:** review

---

## User Story

As a developer,
I want a roll tracker service that persists paper usage and estimates remaining paper,
So that the API can report paper level and the state survives container restarts.

---

## Acceptance Criteria

**AC1 — RollTracker class:**
**Given** `backend/app/services/roll_tracker.py`
**When** reviewed
**Then** `RollTracker` has `load(path)`, `save()` (atomic rename), `add_bytes(n)`, `reset(width_mm, diameter_mm)`, and `estimate_remaining() -> int` (0–100)

**AC2 — Default state created if file missing:**
**Given** `roll_state.json` does not exist
**When** `RollTracker.load(path)` is called
**Then** a default state file is created: `bytes_printed=0`, `roll_width_mm=57`, `roll_diameter_mm=40`, `last_reset=<now ISO>`, `hardware_paper_sensor_available=null`

**AC3 — add_bytes writes atomically to disk:**
**Given** `add_bytes(500)` is called
**When** `roll_state.json` is read directly from disk
**Then** `bytes_printed` equals 500, confirming the atomic write completed

**AC4 — State survives restart:**
**Given** the volume is mounted and a previous state was saved
**When** a new `RollTracker.load()` is called (simulating container restart)
**Then** the previously saved `bytes_printed` value is recovered intact

**AC5 — Tests use tmp_path:**
**Given** `pytest backend/tests/services/test_roll_tracker.py` using `tmp_path`
**When** all tests run
**Then** all pass without accessing real filesystem paths outside `tmp_path`

---

## Files to Create / Modify

```
backend/app/
└── services/
    └── roll_tracker.py         ← NEW
backend/tests/
└── services/
    └── test_roll_tracker.py    ← NEW
```

Also update `dependencies.py` and `main.py` to wire the tracker so `add_bytes()` is called after each print (Status Cache already returns `estimated_remaining_pct` — the tracker provides that value).

---

## Implementation

### `backend/app/services/roll_tracker.py`

```python
import json
import os
from datetime import datetime, timezone
from pathlib import Path

_D_CORE_MM = 12  # typical thermal receipt roll core diameter (mm)
_BYTES_PER_MM2 = 14  # calibration: approx bytes per mm² of roll cross-section


class RollTracker:
    _DEFAULT = {
        "bytes_printed": 0,
        "roll_width_mm": 57,
        "roll_diameter_mm": 40,
        "last_reset": None,
        "hardware_paper_sensor_available": None,
    }

    def __init__(self):
        self._path: Path | None = None
        self._state: dict = {}

    @classmethod
    def load(cls, path) -> "RollTracker":
        tracker = cls()
        tracker._path = Path(path)
        if tracker._path.exists():
            tracker._state = json.loads(tracker._path.read_text())
        else:
            tracker._state = dict(cls._DEFAULT)
            tracker._state["last_reset"] = datetime.now(timezone.utc).isoformat()
            tracker.save()
        return tracker

    def save(self) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, indent=2))
        os.replace(tmp, self._path)  # atomic on POSIX; best-effort on Windows

    def add_bytes(self, n: int) -> None:
        self._state["bytes_printed"] = self._state.get("bytes_printed", 0) + n
        self.save()

    def reset(self, width_mm: int, diameter_mm: int) -> None:
        self._state["bytes_printed"] = 0
        self._state["roll_width_mm"] = width_mm
        self._state["roll_diameter_mm"] = diameter_mm
        self._state["last_reset"] = datetime.now(timezone.utc).isoformat()
        self.save()

    def estimate_remaining(self) -> int:
        d = self._state.get("roll_diameter_mm", 40)
        area = (d / 2) ** 2 - (_D_CORE_MM / 2) ** 2
        total_bytes = max(1, area * _BYTES_PER_MM2)
        used_pct = int(self._state.get("bytes_printed", 0) / total_bytes * 100)
        return max(0, 100 - used_pct)

    @property
    def state(self) -> dict:
        return dict(self._state)
```

### Wire `add_bytes` into print_service.py

After each successful print, call `roll_tracker.add_bytes(printer.get_bytes_for_job())`. This requires the tracker to be accessible from print_service functions. Add it as an optional parameter:

```python
def print_todo(printer, title, items, roll_tracker=None):
    printer.print_todo(title, items)
    if roll_tracker is not None:
        roll_tracker.add_bytes(printer.get_bytes_for_job())
```

Or, simpler for now: wire it in the router layer by calling `roll_tracker.add_bytes()` after a successful print. Either approach is fine; the router approach keeps print_service thin.

**Decision: wire in dependencies.py** — add `get_roll_tracker()` returning a module-level `RollTracker` instance loaded from `DATA_DIR/roll_state.json`. The status cache's `estimated_remaining_pct` is updated by reading from the tracker.

For this story: **implement RollTracker and its tests**. Wiring into routers happens in Story 2.7 where admin endpoints also need it.

---

## Context from Previous Stories

- `DATA_DIR` from `config.py` = `/app/data` (Docker) or `./data` (dev)
- `tmp_roll_state` fixture in `conftest.py` provides `tmp_path / "roll_state.json"`
- Atomic write ensures crash safety — important for a Pi that may lose power

---

## Definition of Done

- [x] `roll_tracker.py` exists with all 5 methods
- [x] Default state created when file missing (AC2)
- [x] `add_bytes` writes atomically — verified by reading file directly (AC3)
- [x] State survives load/reload cycle (AC4)
- [x] `pytest backend/tests/services/test_roll_tracker.py` — 10 tests passing using `tmp_path`
- [x] `pytest backend/` passes with 0 failures (52 tests)

---

## Dev Notes

_To be filled by developer during/after implementation._

---

## Dev Agent Record

### Completion Notes

- `RollTracker.load()`: creates default state + saves if file missing; loads existing otherwise.
- `save()`: uses `os.replace(tmp, path)` — atomic on POSIX, best-effort on Windows.
- `estimate_remaining()`: area formula based on roll diameter vs core (12mm). Calibration: ~14 bytes/mm² gives sensible estimates for 57×40mm roll.
- `hardware_paper_sensor_available` stored as `null` — set to true/false on first real `get_status()` call (Story 2.7 / EscposPrinter).
- Router wiring (`add_bytes` after print) and admin endpoints covered in Story 2.7.

### File List

- `backend/app/services/roll_tracker.py` (new)
- `backend/tests/services/test_roll_tracker.py` (new)

### Change Log

- 2026-05-10: RollTracker with load/save/add_bytes/reset/estimate_remaining. Atomic writes. 52 tests passing.
