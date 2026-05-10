# Story 2.4: FastAPI Application — Routers, Models, Static Mount

**Epic:** 2 — Complete Backend API
**Story:** 2.4
**Status:** review

---

## User Story

As a developer,
I want the full FastAPI application wired together with all API routes, Pydantic validation, and static file serving,
So that every endpoint is reachable, validates inputs, and the frontend SPA is served from the same origin.

---

## Acceptance Criteria

**AC1 — Routers registered before StaticFiles:**
**Given** `backend/app/main.py`
**When** reviewed
**Then** all API routers (`/api/v1/print/*`, `/health`) are registered **before** the `StaticFiles` mount at `/`

**AC2 — Print endpoint returns success:**
**Given** `POST /api/v1/print/todo` with `{"title": "My List", "items": ["item1"]}`
**When** processed with `MockPrinter` injected
**Then** `{"success": true}` is returned with HTTP 200

**AC3 — Validation rejects empty items:**
**Given** `POST /api/v1/print/todo` with `{"items": []}`
**When** processed
**Then** HTTP 422 is returned with a validation error detail (no print call made)

**AC4 — PrinterError → HTTP 503:**
**Given** a `PrinterError` raised by the injected `MockPrinter`
**When** any print endpoint handles it
**Then** HTTP 503 is returned with `{"detail": "<message>"}` — not 500

**AC5 — Health check:**
**Given** `GET /health`
**When** called
**Then** `{"status": "ok"}` is returned with HTTP 200

**AC6 — All 5 print endpoints tested with TestClient:**
**Given** `FastAPI TestClient` in `backend/tests/routers/test_print_routes.py`
**When** all 5 print endpoints are tested with valid inputs, empty/invalid inputs, and `PrinterError` conditions
**Then** all tests pass

---

## Files to Create

```
backend/app/
├── dependencies.py         ← NEW: get_printer() dependency
├── routers/
│   ├── print.py            ← NEW: all /api/v1/print/* routes
│   └── health.py           ← NEW: /health route
├── models/
│   └── print_models.py     ← NEW: Pydantic request models
└── static/
    └── .gitkeep            ← NEW: ensures dir exists for StaticFiles
```

```
backend/tests/routers/
└── test_print_routes.py    ← NEW: TestClient tests
```

**Files to MODIFY:**
- `backend/app/main.py` — register routers, StaticFiles, global PrinterError handler

---

## Implementation

### `backend/app/dependencies.py`

```python
from app.services.printer import PrinterInterface, EscposPrinter
from app.config import PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID

_printer: PrinterInterface | None = None

def get_printer() -> PrinterInterface:
    global _printer
    if _printer is None:
        _printer = EscposPrinter(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)
    return _printer
```

Lazy singleton — connects to printer on first request. Tests override via `app.dependency_overrides[get_printer] = lambda: mock_printer`.

### `backend/app/models/print_models.py`

```python
from pydantic import BaseModel, field_validator

class TodoRequest(BaseModel):
    title: str = "TO DO"
    items: list[str]

    @field_validator('items')
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError('items must not be empty')
        return v

class ReceiptItem(BaseModel):
    name: str
    price: float

class ReceiptRequest(BaseModel):
    store: str
    items: list[ReceiptItem]
    address: str | None = None
    phone: str | None = None
    tax_pct: float = 0.0

class FreeTextRequest(BaseModel):
    text: str
    font_size: str = "medium"

class QrRequest(BaseModel):
    url: str
```

### `backend/app/routers/health.py`

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}
```

### `backend/app/routers/print.py`

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from app.dependencies import get_printer
from app.services.printer import PrinterInterface
from app.services import print_service
from app.models.print_models import TodoRequest, ReceiptRequest, FreeTextRequest, QrRequest

router = APIRouter(prefix="/print", tags=["print"])
PrinterDep = Annotated[PrinterInterface, Depends(get_printer)]

@router.post("/todo")
def print_todo(req: TodoRequest, printer: PrinterDep):
    print_service.print_todo(printer, req.title, req.items)
    return {"success": True}

@router.post("/receipt")
def print_receipt(req: ReceiptRequest, printer: PrinterDep):
    items = [(item.name, item.price) for item in req.items]
    print_service.print_receipt(printer, req.store, items, req.address, req.phone, req.tax_pct)
    return {"success": True}

@router.post("/free-text")
def print_free_text(req: FreeTextRequest, printer: PrinterDep):
    print_service.print_free_text(printer, req.text, req.font_size)
    return {"success": True}

@router.post("/qr")
def print_qr(req: QrRequest, printer: PrinterDep):
    print_service.print_qr(printer, req.url)
    return {"success": True}

@router.post("/goatse")
def print_goatse(printer: PrinterDep):
    print_service.print_goatse(printer)
    return {"success": True}
```

### `backend/app/main.py` (full replacement)

```python
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.exceptions import PrinterError
from app.routers import health, print as print_router

app = FastAPI(title="PrintServer")

@app.exception_handler(PrinterError)
async def printer_error_handler(request: Request, exc: PrinterError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})

# API routers MUST be registered before StaticFiles
app.include_router(health.router)
app.include_router(print_router.router, prefix="/api/v1")

# Static files — serves the SvelteKit SPA; comes last to avoid swallowing API routes
_static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
```

### Test fixture pattern

```python
@pytest.fixture
def client(mock_printer):
    from app.main import app
    from app.dependencies import get_printer
    app.dependency_overrides[get_printer] = lambda: mock_printer
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

---

## Context from Previous Stories

- `PrinterError` is in `app.exceptions` — used by the global error handler
- `print_service` has all 5 functions — routers call them
- `MockPrinter.configure_error()` — use this to simulate 503 in tests
- `mock_printer` fixture is in `conftest.py` — use it in the `client` fixture

---

## Definition of Done

- [x] `backend/app/dependencies.py` exists with `get_printer()`
- [x] `backend/app/models/print_models.py` exists with 5 models
- [x] `backend/app/routers/print.py` exists with 5 endpoints
- [x] `backend/app/routers/health.py` exists
- [x] `backend/app/static/.gitkeep` exists
- [x] `backend/app/main.py` updated — routers registered before StaticFiles
- [x] `GET /health` → 200 `{"status": "ok"}`
- [x] `POST /api/v1/print/todo` valid → 200 `{"success": true}`
- [x] `POST /api/v1/print/todo` empty items → 422
- [x] `PrinterError` → 503 `{"detail": "..."}`
- [x] `pytest backend/` passes with 0 failures (38 tests)

---

## Dev Notes

_To be filled by developer during/after implementation._

---

## Dev Agent Record

### Completion Notes

- `dependencies.py`: lazy singleton `get_printer()` — connects to USB printer on first request; tests override via `app.dependency_overrides`.
- `main.py`: global `PrinterError` exception handler → 503; routers registered before `StaticFiles("/")`.
- `static/.gitkeep`: dir created so `StaticFiles` doesn't raise at startup in dev; Docker build overwrites with real frontend.
- `httpx` was missing from local env (in requirements-dev.txt); installed. TestClient needs it.
- 13 new router tests (38 total). All DoD items verified.

### File List

- `backend/app/main.py` (modified)
- `backend/app/dependencies.py` (new)
- `backend/app/models/print_models.py` (new)
- `backend/app/routers/health.py` (new)
- `backend/app/routers/print.py` (new)
- `backend/app/static/.gitkeep` (new)
- `backend/tests/routers/test_print_routes.py` (new)

### Change Log

- 2026-05-10: Wired FastAPI app — routers, Pydantic models, StaticFiles, PrinterError→503 handler. 38 tests passing.
