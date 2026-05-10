# Story 2.5: Status Cache — Background Polling Thread

**Epic:** 2 — Complete Backend API
**Story:** 2.5
**Status:** review

---

## User Story

As a developer,
I want a background thread that polls the printer every 5 seconds and caches the result,
So that status requests return instantly without blocking on hardware I/O.

---

## Acceptance Criteria

**AC1 — StatusCache class:**
**Given** `backend/app/services/status_cache.py`
**When** reviewed
**Then** `StatusCache` has `start(printer)` launching a daemon thread, `get_cached()` returning the last known status dict, and initial state `{"printer_online": false, "paper_near_end": false, "paper_out": false, "estimated_remaining_pct": 0}`

**AC2 — Cache populates after polling:**
**Given** `StatusCache` started with a `MockPrinter` configured to return `printer_online: true`
**When** 6 seconds elapse
**Then** `get_cached()["printer_online"]` is `true`

**AC3 — Start handles unavailable printer gracefully:**
**Given** `MockPrinter` raises on `get_status()` (simulating unavailable printer at startup)
**When** `StatusCache.start()` is called
**Then** no exception propagates to the caller and `get_cached()` returns the initial offline state

**AC4 — Status endpoint is fast:**
**Given** `GET /api/v1/status` while the background thread is running
**When** response time is measured
**Then** it returns under 200ms (reading from cache, not polling hardware)

**AC5 — Wired into main.py lifespan:**
**Given** `status_cache` wired into `main.py` lifespan
**When** the container starts
**Then** the background polling thread begins automatically

---

## Files to Create / Modify

```
backend/app/
├── services/
│   └── status_cache.py         ← NEW
├── routers/
│   └── status.py               ← NEW: GET /api/v1/status
└── main.py                     ← UPDATE: add lifespan + status router
```

```
backend/tests/
└── services/
    └── test_status_cache.py    ← NEW
```

---

## Implementation

### `backend/app/services/status_cache.py`

```python
import threading
import time
import logging

logger = logging.getLogger(__name__)

_DEFAULT_STATE = {
    "printer_online": False,
    "paper_near_end": False,
    "paper_out": False,
    "estimated_remaining_pct": 0,
}
POLL_INTERVAL = 5


class StatusCache:
    def __init__(self):
        self._cache: dict = dict(_DEFAULT_STATE)
        self._lock = threading.Lock()

    def start(self, printer) -> None:
        thread = threading.Thread(
            target=self._poll_loop, args=(printer,), daemon=True
        )
        thread.start()

    def _poll_loop(self, printer) -> None:
        while True:
            try:
                status = printer.get_status()
                with self._lock:
                    self._cache.update(status)
                    self._cache.setdefault("estimated_remaining_pct", 0)
            except Exception as e:
                logger.debug("Status poll failed: %s", e)
                with self._lock:
                    self._cache["printer_online"] = False
            time.sleep(POLL_INTERVAL)

    def get_cached(self) -> dict:
        with self._lock:
            return dict(self._cache)
```

### `backend/app/routers/status.py`

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from app.dependencies import get_status_cache
from app.services.status_cache import StatusCache

router = APIRouter()
CacheDep = Annotated[StatusCache, Depends(get_status_cache)]


@router.get("/api/v1/status")
def get_status(cache: CacheDep):
    return cache.get_cached()
```

### `backend/app/dependencies.py` update

Add `get_status_cache()`:

```python
_status_cache: StatusCache | None = None

def get_status_cache() -> StatusCache:
    global _status_cache
    if _status_cache is None:
        from app.services.status_cache import StatusCache
        _status_cache = StatusCache()
    return _status_cache
```

### `backend/app/main.py` update

Add lifespan and status router:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.dependencies import get_printer, get_status_cache
    cache = get_status_cache()
    try:
        printer = get_printer()
        cache.start(printer)
    except Exception:
        pass  # printer unavailable at startup — cache stays at offline default
    yield

app = FastAPI(title="PrintServer", lifespan=lifespan)
# ... rest of app setup ...
```

---

## Context from Previous Stories

- `MockPrinter.get_status()` returns `{"printer_online": True, "paper_near_end": False, "paper_out": False}`
- `MockPrinter.configure_error(exc)` makes the next call raise — use to test AC3

---

## Definition of Done

- [x] `status_cache.py` exists with `StatusCache` class
- [x] `routers/status.py` exists with `GET /api/v1/status`
- [x] `dependencies.py` has `get_status_cache()`
- [x] `main.py` uses lifespan to start the cache
- [x] `test_status_cache.py` — AC1, AC2, AC3 tests pass
- [x] `GET /api/v1/status` returns the cached dict
- [x] `pytest backend/` passes with 0 failures (42 tests)

---

## Dev Notes

_To be filled by developer during/after implementation._

---

## Dev Agent Record

### Completion Notes

- `StatusCache`: daemon thread calls `printer.get_status()` every 5s; exceptions caught internally (printer_online→False); thread-safe with `threading.Lock`.
- `MockPrinter` updated: added `configure_status_error()` + `_raise_on_status` flag so status polling errors can be injected in tests (separate from print error injection).
- `main.py` updated with `lifespan` context manager — starts cache on startup; catches exceptions if printer unavailable (cache stays offline).
- AC2 (6-second polling test) passes; AC3 (error handling) verified with 200ms sleep after thread start.

### File List

- `backend/app/services/status_cache.py` (new)
- `backend/app/routers/status.py` (new)
- `backend/app/dependencies.py` (modified — added `get_status_cache`)
- `backend/app/main.py` (modified — added lifespan + status router)
- `backend/app/services/printer.py` (modified — added `configure_status_error` to MockPrinter)
- `backend/tests/services/test_status_cache.py` (new)

### Change Log

- 2026-05-10: StatusCache with daemon polling thread, GET /api/v1/status, lifespan wiring. 42 tests passing.
