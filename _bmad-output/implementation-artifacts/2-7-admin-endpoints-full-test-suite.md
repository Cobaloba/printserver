# Story 2.7: Admin Endpoints + Full Test Suite

**Epic:** 2 — Complete Backend API
**Story:** 2.7
**Status:** review

---

## User Story

As a developer,
I want the admin endpoints for roll management and a complete passing test suite,
So that till roll operations are API-accessible and every backend component has verified coverage.

---

## Acceptance Criteria

**AC1 — POST /api/v1/admin/roll resets the tracker:**
**Given** `POST /api/v1/admin/roll` with `{"width_mm": 57, "diameter_mm": 40}`
**When** processed
**Then** `RollTracker.reset()` is called, state is updated, and `{"success": true}` is returned

**AC2 — GET /api/v1/admin/roll returns roll state:**
**Given** `GET /api/v1/admin/roll`
**When** called
**Then** a JSON object with `bytes_printed`, `roll_width_mm`, `roll_diameter_mm`, `last_reset`, and `estimated_remaining_pct` is returned

**AC3 — Validation on missing fields:**
**Given** `POST /api/v1/admin/roll` with missing required fields
**When** processed
**Then** HTTP 422 is returned

**AC4 — Full test suite passes:**
**Given** `pytest backend/` run across the full test suite
**When** all tests execute
**Then** all pass; every test touching print operations uses `MockPrinter`; no test imports `escpos` directly

**AC5 — Admin route coverage:**
**Given** `backend/tests/routers/test_admin_routes.py`
**When** run
**Then** both admin endpoints are covered with valid inputs, missing fields, and a reset-then-verify flow

---

## Files to Create / Modify

```
backend/app/
├── models/
│   └── admin_models.py         ← NEW
├── routers/
│   ├── admin.py                ← NEW
│   └── print.py                ← UPDATE: add_bytes after each print
│   └── status.py               ← UPDATE: include estimated_remaining_pct from tracker
└── dependencies.py             ← UPDATE: add get_roll_tracker()
└── main.py                     ← UPDATE: include admin router
backend/tests/routers/
└── test_admin_routes.py        ← NEW
```

---

## Implementation

### `backend/app/models/admin_models.py`

```python
from pydantic import BaseModel

class NewRollRequest(BaseModel):
    width_mm: int
    diameter_mm: int
```

### `backend/app/routers/admin.py`

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from app.dependencies import get_roll_tracker
from app.services.roll_tracker import RollTracker
from app.models.admin_models import NewRollRequest

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
TrackerDep = Annotated[RollTracker, Depends(get_roll_tracker)]

@router.post("/roll")
def reset_roll(req: NewRollRequest, tracker: TrackerDep):
    tracker.reset(req.width_mm, req.diameter_mm)
    return {"success": True}

@router.get("/roll")
def get_roll_state(tracker: TrackerDep):
    state = tracker.state
    return {
        "bytes_printed": state["bytes_printed"],
        "roll_width_mm": state["roll_width_mm"],
        "roll_diameter_mm": state["roll_diameter_mm"],
        "last_reset": state["last_reset"],
        "estimated_remaining_pct": tracker.estimate_remaining(),
    }
```

### `dependencies.py` update — add `get_roll_tracker()`

```python
_roll_tracker = None

def get_roll_tracker():
    global _roll_tracker
    if _roll_tracker is None:
        from app.services.roll_tracker import RollTracker
        from app.config import DATA_DIR
        import os
        _roll_tracker = RollTracker.load(os.path.join(DATA_DIR, "roll_state.json"))
    return _roll_tracker
```

### `routers/print.py` update — call `add_bytes` after each print

Each endpoint gets a `TrackerDep` and calls `tracker.add_bytes(printer.get_bytes_for_job())` after the print call.

### `routers/status.py` update — include roll estimate

```python
@router.get("/api/v1/status")
def get_status(cache: CacheDep, tracker: TrackerDep):
    status = cache.get_cached()
    status["estimated_remaining_pct"] = tracker.estimate_remaining()
    return status
```

---

## Context from Previous Stories

- `RollTracker.reset()`, `add_bytes()`, `estimate_remaining()` all implemented in Story 2.6
- `get_roll_tracker()` in tests: override with `lambda: RollTracker.load(tmp_roll_state)` in client fixture
- `tmp_roll_state` fixture already provides a temporary path

---

## Definition of Done

- [x] `admin_models.py` with `NewRollRequest`
- [x] `routers/admin.py` with POST and GET `/api/v1/admin/roll`
- [x] `dependencies.py` has `get_roll_tracker()`
- [x] `routers/print.py` calls `add_bytes` after each print
- [x] `routers/status.py` returns `estimated_remaining_pct` from tracker
- [x] `main.py` includes admin router
- [x] `test_admin_routes.py` — 7 tests covering AC1–AC3 + AC5 (reset-then-verify)
- [x] `pytest backend/` — 59 tests pass, no `import escpos` in tests (verified by grep)

---

## Dev Notes

_To be filled by developer during/after implementation._

---

## Dev Agent Record

### Completion Notes

- Admin endpoints wired: `POST /api/v1/admin/roll` calls `tracker.reset()`; `GET /api/v1/admin/roll` returns full state + estimate.
- `routers/print.py` updated: all 5 print endpoints call `tracker.add_bytes(printer.get_bytes_for_job())` after successful print.
- `routers/status.py` updated: `estimated_remaining_pct` now comes from `tracker.estimate_remaining()` not the status cache default.
- `test_print_routes.py` fixture updated to also override `get_roll_tracker` (needed since print endpoints now depend on it).
- AC4 confirmed: `grep -r "import escpos" tests/` returns empty. All 59 tests use MockPrinter.

### File List

- `backend/app/models/admin_models.py` (new)
- `backend/app/routers/admin.py` (new)
- `backend/app/dependencies.py` (modified — added `get_roll_tracker`)
- `backend/app/routers/print.py` (modified — add_bytes wiring)
- `backend/app/routers/status.py` (modified — tracker estimate)
- `backend/app/main.py` (modified — admin router)
- `backend/tests/routers/test_admin_routes.py` (new)
- `backend/tests/routers/test_print_routes.py` (modified — tracker override in fixture)

### Change Log

- 2026-05-10: Admin roll endpoints, roll tracker wired into print pipeline, status returns live estimate. 59 tests passing.
