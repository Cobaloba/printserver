---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-05-08'
inputDocuments: ['_bmad-output/planning-artifacts/prd.md']
workflowType: 'architecture'
project_name: 'PrintServer'
user_name: 'Conor'
date: '2026-05-07'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:** 38 FRs across 7 areas covering print operations (5 print types + formatting + outcome reporting), printer hardware monitoring (online/offline/paper detection), till roll state management, mobile PWA frontend, system reliability (auto-restart, health check, graceful degradation), versioned REST API, and developer ergonomics (modular add pattern, CI/CD, SSH redeploy).

**Non-Functional Requirements:**
- Performance: < 3s print end-to-end, < 200ms status API, < 2s frontend load
- Reliability: auto-restart within 30s, USB path stable across reboots, state survives restarts
- Maintainability: new print type in ≤ 2 files, unit-testable without hardware, 10-min deploy cycle
- Security: no content persistence, LAN-only binding, no secrets in image
- Compatibility: `linux/arm64`, mobile Chrome/Safari 375px+, no port conflicts with PiHole/Octoprint

**Scale & Complexity:**
- Primary domain: Full-stack self-hosted service (ARM64)
- Complexity level: Medium
- Estimated architectural components: 6 (Printer Interface, Print Service, API Layer, State Manager, Frontend SPA, CI/CD Pipeline)

### Technical Constraints & Dependencies

- **Hardware:** USB thermal printer via `python-escpos` `Usb()` backend — vendor/product ID required; udev symlink required for stable device path
- **Runtime:** Docker on `linux/arm64` (Pi 4); base image `python:3.12-slim-bookworm`; must not use Alpine (musl libc breaks escpos USB backend)
- **Coexistence:** Pi already runs PiHole (80/443) and Octoprint (5000) — port must be confirmed conflict-free
- **Brownfield:** Existing `printertest.py` contains proven print logic (todo, receipt, goatse formatting) to be refactored — not rewritten
- **Deployment:** GitHub Actions multi-arch build (`linux/arm64`); GHCR registry; Watchtower auto-pull on Pi

### Cross-Cutting Concerns Identified

1. **Error propagation chain** — hardware fault must surface as a clean `503 + detail` API response and reach the frontend toast; affects Printer Interface, Print Service, API routes, and frontend error handling
2. **Printer connection lifecycle** — connect/disconnect/reconnect affects status polling, all print operations, and admin functions; must be handled consistently
3. **Testability abstraction** — printer hardware must be mockable; the Printer Interface is the seam that enables this across all 5 print types and status checks
4. **State persistence** — roll tracking state (bytes printed, roll size, last reset) is written by the Print Service and read by the Status API and frontend; must survive container restarts via volume mount

## Starter Template Evaluation

### Primary Technology Domain

Full-stack self-hosted service — Python/FastAPI REST backend + SvelteKit PWA frontend, monorepo, single Docker container serving both.

### Starter Options Considered

| Option | Verdict |
|---|---|
| `npm create svelte@latest` (SvelteKit 2 + Svelte 5) | ✓ Selected — adapter-static gives pure SPA/PWA output |
| `npm create vite@latest --template svelte-ts` | Rejected — no routing, no PWA tooling, more manual setup for no gain |
| FastAPI scaffold tools (community) | Rejected — manual structure is cleaner and matches our modular pattern exactly |

### Selected Starters

**Frontend: SvelteKit 2 + Svelte 5**

```bash
npm create svelte@latest frontend
# Select: SvelteKit minimal, TypeScript, ESLint + Prettier, Vitest
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite
npm install -D vite-plugin-pwa
```

**Backend: FastAPI (manual)**

```bash
pip install fastapi "uvicorn[standard]" python-escpos pydantic
```

### Architectural Decisions Provided by Starters

**Language & Runtime:**
- Frontend: TypeScript (SvelteKit default), compiled to static JS
- Backend: Python 3.12, FastAPI 0.115.x, Pydantic v2

**Styling Solution:**
- Tailwind CSS v4 via `@tailwindcss/vite` Vite plugin — no `tailwind.config.js`; custom tokens defined in `@theme {}` blocks in CSS

**Build Tooling:**
- Frontend: Vite + `@sveltejs/adapter-static` → outputs to `frontend/build/`
- Backend: Docker multi-stage build copies `frontend/build/` into `app/static/`; FastAPI mounts `static/` at `/`

**Testing Framework:**
- Frontend: Vitest (unit), Playwright (E2E optional)
- Backend: pytest + pytest-asyncio; printer hardware mocked via a `PrinterInterface` abstract class

**Code Organisation:**
```
/
├── frontend/               # SvelteKit app
│   ├── src/
│   │   ├── routes/         # One route per print type
│   │   ├── lib/            # Shared components, API client
│   │   └── app.css         # Tailwind @import + @theme
│   ├── static/             # PWA manifest, icons
│   └── vite.config.ts
├── backend/
│   └── app/
│       ├── main.py         # FastAPI instance, static mount
│       ├── routers/
│       │   ├── print.py    # All /api/v1/print/* routes
│       │   ├── status.py   # /api/v1/status
│       │   └── admin.py    # /api/v1/admin/*
│       ├── services/
│       │   ├── print_service.py   # One function per print type
│       │   ├── printer.py         # PrinterInterface + EscposPrinter + MockPrinter
│       │   └── roll_tracker.py    # Till roll state management
│       ├── models/         # Pydantic v2 request/response schemas
│       └── data/           # Volume-mounted state file (roll_state.json)
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/      # CI/CD pipeline
```

**Development Experience:**
- Hot reload: `uvicorn --reload` (backend), `vite dev` (frontend)
- Frontend proxies `/api/` to backend during development via `vite.config.ts`
- Single `docker compose up --build` for production parity

**Note:** Project initialisation using these commands is the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Service port: **9000** *(pending PiHole port conflict spike — see spikes below)*
- State persistence: **JSON file** (`/app/data/roll_state.json`, volume-mounted)
- Printer status strategy: **Background cache thread** (5s poll cycle, instant reads)
- Printer hardware abstraction: **`PrinterInterface` abstract class** with `EscposPrinter` (real) and `MockPrinter` (tests)

**Important Decisions (Shape Architecture):**
- Frontend state management: **Svelte stores** (built-in `writable`/`derived`, no external library)
- Frontend API client: **Thin `fetch` wrapper** in `src/lib/api.ts` (no axios/ky)
- Toast notifications: **`svelte-sonner`** (modern, accessible, zero-config)
- Error handling standard: **`HTTPException(status_code, detail=str)`** caught globally; `detail` field surfaced in frontend toast
- Logging: **Python standard `logging`**, INFO level, UTC timestamps, structured enough for `docker logs`
- API documentation: **OpenAPI enabled** at `/docs` and `/redoc` (useful for dev and API testing)
- Dev proxy: **Vite proxies `/api/` → `http://localhost:9000`** so frontend dev server calls the local backend

**Deferred Decisions (Post-MVP):**
- Authentication mechanism (V2 — JWT, session, or API key — to be decided when scoped)
- Reverse proxy / local hostname (Nginx Proxy Manager or Traefik — nice-to-have after V1 stable)
- Structured log aggregation (homelab `docker logs` is sufficient for V1)

### Data Architecture

**State Persistence: JSON file**
- Path: `/app/data/roll_state.json` (inside container), mounted from Pi host via Docker volume
- Schema:
```json
{
  "bytes_printed": 0,
  "roll_width_mm": 57,
  "roll_diameter_mm": 40,
  "last_reset": "2026-05-07T10:00:00Z",
  "hardware_paper_sensor_available": null
}
```
- Write strategy: write to temp file → atomic rename (prevents corrupt state on crash mid-write)
- `hardware_paper_sensor_available` starts as `null`; set to `true/false` on first `get_status()` call so the system self-discovers printer capability
- No database required — state is simple, single-writer, single-reader

**Printer Status Cache:**
- Background `threading.Thread` started on FastAPI `lifespan` startup, polls `printer.get_status()` every 5 seconds
- Cached result: `{"printer_online": bool, "paper_near_end": bool, "paper_out": bool, "estimated_remaining_pct": int}`
- `GET /api/v1/status` reads from cache instantly — no blocking hardware call per request
- Cache initialises as `printer_online: false` until first successful poll

### Authentication & Security

- **V1:** No authentication. LAN-only by network topology. Accepted risk documented in PRD.
- **No CORS middleware** in production — FastAPI serves the SPA from the same origin
- **Dev CORS:** Vite proxy in `vite.config.ts` handles API calls during development — no CORS headers needed even in dev
- **No secrets in image:** `PRINTER_VENDOR_ID`, `PRINTER_PRODUCT_ID`, `PORT`, `DATA_DIR` passed via `.env` / Docker Compose `env_file`
- **V2 auth:** Architecture must not hardcode unauthenticated assumptions — router structure is auth-middleware-ready from day one

### API & Communication Patterns

- REST, `/api/v1/` prefix, JSON request/response
- Pydantic v2 models for all request bodies (`app/models/`) — validation errors return `422` automatically
- Global exception handler catches `PrinterError` → `HTTPException(503, detail="...")`
- OpenAPI auto-generated at `/docs` (SwaggerUI) and `/redoc`
- No rate limiting (single user, LAN only)
- Environment variable `PORT=9000` used by uvicorn — easily changed if port conflict found

### Frontend Architecture

- **SvelteKit file-based routing:** one route per print type (`src/routes/todo/`, `src/routes/receipt/`, etc.)
- **Svelte stores:** `printerStatus` store (writable, updated by polling loop), `rollState` store — no external state library
- **API client:** `src/lib/api.ts` exports typed `fetch` wrappers for each endpoint; all error handling in one place
- **Toast:** `svelte-sonner` — `toast.success('Sent to printer ✓')` / `toast.error(detail)` called from API client
- **PWA:** `vite-plugin-pwa` configured in `vite.config.ts`; `manifest.webmanifest` in `static/`; service worker caches app shell
- **Components:** shared UI in `src/lib/components/` (StatusDot, RollGauge, PrintButton, Toast wrapper)

### Infrastructure & Deployment

- **Port:** `9000` — set via `PORT` env var; Docker Compose `ports: ["9000:9000"]` *(pending PiHole spike)*
- **Health check:** `GET /health` → `{"status": "ok"}`; Docker `HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -f http://localhost:9000/health`
- **Docker Compose:**
  - `restart: unless-stopped`
  - `devices: ["/dev/receipt-printer:/dev/receipt-printer"]`
  - `volumes: ["./data:/app/data"]`
  - `env_file: .env`
- **CI/CD:** GitHub Actions → GHCR (`ghcr.io/{user}/printserver:latest`, `linux/arm64`) → Watchtower auto-pull
- **Dev workflow:** `uvicorn app.main:app --reload --port 9000` + `npm run dev` (Vite on 5173, proxies `/api/` to 9000)
- **SSH redeploy alias on Pi:** `alias redeploy='cd ~/printserver && git pull && docker compose up --build -d'`

### Pre-Development Spikes Required

| Spike | What to Test | Blocks |
|---|---|---|
| **Hardware validation** | Connect printer to Pi via USB → `lsusb` (get vendor/product ID) → `python-escpos Usb()` connects → `printer.get_status()` returns paper sensor data → udev symlink survives reboot | All print API development |
| **PiHole port check** | SSH into Pi → `docker ps` / `netstat -tlnp` → confirm what ports PiHole actually uses → verify 9000 is free | Docker Compose port config |

### Decision Impact Analysis

**Implementation Sequence:**
1. Hardware spike → confirms vendor/product ID and sensor capability
2. Port spike → locks `docker-compose.yml` port
3. `printer.py` — `PrinterInterface` ABC + `EscposPrinter` + `MockPrinter`
4. `roll_tracker.py` — JSON read/write with atomic rename
5. `print_service.py` — refactor from `printertest.py`, one function per type
6. `main.py` — FastAPI app, lifespan (start background poll thread), static mount, routers
7. `docker-compose.yml` + `Dockerfile` — build pipeline
8. GitHub Actions workflow — CI/CD
9. SvelteKit frontend — routes, stores, API client, PWA config

**Cross-Component Dependencies:**
- Background status thread → `printer.py` interface → all status reads
- `roll_tracker.py` → read by status API and frontend; written by print service (byte tracking)
- `PrinterInterface` abstraction → enables pytest mocking across all 5 print functions

## Implementation Patterns & Consistency Rules

### Critical Conflict Points Identified

8 areas where AI agents could make different choices without explicit rules: JSON field naming convention, API response envelope format, error propagation pattern, printer interface method signatures, Svelte store update patterns, test file location, loading state management, and route folder naming.

### Naming Patterns

**Backend (Python) Conventions:**
- Files/modules: `snake_case.py` — `print_service.py`, `roll_tracker.py`
- Functions/variables: `snake_case` — `def print_todo(...)`, `bytes_printed`
- Classes: `PascalCase` — `PrinterInterface`, `EscposPrinter`, `TodoRequest`
- Constants: `UPPER_SNAKE_CASE` — `DEFAULT_POLL_INTERVAL = 5`
- Pydantic models: `PascalCase` suffix `Request`/`Response` — `TodoRequest`, `StatusResponse`

**Frontend (TypeScript/Svelte) Conventions:**
- Svelte components: `PascalCase.svelte` — `StatusDot.svelte`, `RollGauge.svelte`, `PrintButton.svelte`
- TypeScript utilities/stores: `camelCase.ts` — `api.ts`, `stores.ts`, `polling.ts`
- SvelteKit route folders: `kebab-case` — `src/routes/free-text/`, `src/routes/qr-code/`
- TypeScript interfaces: `PascalCase` — `interface PrinterStatus { ... }`
- Store names: `camelCase` — `printerStatus`, `rollState`

**API Endpoint Naming:**
- Always `kebab-case` path segments: `/api/v1/print/free-text`, `/api/v1/admin/roll`
- Verbs via HTTP method, not in URL: `POST /api/v1/print/todo` not `POST /api/v1/print/todo/submit`

### Format Patterns

**JSON Field Naming — CRITICAL RULE:**
- All JSON fields (request bodies and response payloads) use `snake_case` throughout
- **No camelCase conversion layer** between backend and frontend
- Frontend TypeScript interfaces mirror backend field names exactly
- ✅ `paper_near_end`, `bytes_printed`, `roll_width_mm`
- ❌ `paperNearEnd`, `bytesPrinted`, `rollWidthMm`

**API Response Formats:**

| Endpoint type | Success shape | Error shape |
|---|---|---|
| Print endpoints | `{"success": true}` | `{"detail": "Printer offline"}` |
| Status endpoint | Direct status object | `{"detail": "..."}` |
| Admin endpoints | `{"success": true}` | `{"detail": "..."}` |
| Health endpoint | `{"status": "ok"}` | — |

- **No global response wrapper** — return the model directly, not `{"data": model, "success": true}`
- Errors: FastAPI's default `{"detail": "message"}` — never invent custom error envelope shapes
- HTTP status codes: `200` success, `422` validation failure (automatic), `503` printer unavailable, `400` bad input

**Date/Time Format:**
- All datetimes as ISO 8601 strings with UTC: `"2026-05-07T10:00:00Z"`
- Python: `datetime.utcnow().isoformat() + "Z"` or `datetime.now(UTC).isoformat()`
- Never Unix timestamps in API responses

### Structure Patterns

**Backend file organisation:**
```
backend/app/
├── main.py              # FastAPI app, lifespan, static mount, router registration
├── routers/
│   ├── print.py         # All /api/v1/print/* routes — thin, delegates to services
│   ├── status.py        # /api/v1/status route
│   └── admin.py         # /api/v1/admin/* routes
├── services/
│   ├── print_service.py # One function per print type: print_todo(), print_receipt(), etc.
│   ├── printer.py       # PrinterInterface ABC + EscposPrinter + MockPrinter
│   └── roll_tracker.py  # RollTracker: read/write roll_state.json, estimate_remaining()
├── models/
│   ├── print_models.py  # TodoRequest, ReceiptRequest, FreeTextRequest, QrRequest
│   ├── status_models.py # StatusResponse, RollStateResponse
│   └── admin_models.py  # NewRollRequest
└── data/                # Volume-mounted directory — roll_state.json lives here
```

**Backend test organisation:**
```
backend/tests/
├── services/
│   ├── test_print_service.py   # Uses MockPrinter
│   ├── test_roll_tracker.py    # Uses tmp_path fixture
│   └── test_printer.py         # MockPrinter behaviour
└── routers/
    └── test_print_routes.py    # FastAPI TestClient
```

**Frontend organisation:**
```
frontend/src/
├── routes/
│   ├── +layout.svelte          # Starts polling, renders StatusDot + RollGauge + Toaster
│   ├── +page.svelte            # Home screen — print type cards
│   ├── todo/+page.svelte
│   ├── receipt/+page.svelte
│   ├── free-text/+page.svelte
│   ├── qr-code/+page.svelte
│   ├── goatse/+page.svelte
│   └── admin/+page.svelte
├── lib/
│   ├── api.ts                  # All fetch wrappers — single source of truth for API calls
│   ├── stores.ts               # printerStatus, rollState Svelte stores
│   ├── polling.ts              # startPolling() / stopPolling() — called from layout
│   └── components/
│       ├── StatusDot.svelte
│       ├── RollGauge.svelte
│       ├── PrintButton.svelte  # Handles loading state internally
│       └── PrintCard.svelte    # Home screen card
└── app.css                     # @import "tailwindcss"; + @theme {} tokens
```

### Communication Patterns

**Printer Interface Contract — agents MUST implement exactly these signatures:**
```python
from abc import ABC, abstractmethod

class PrinterInterface(ABC):
    @abstractmethod
    def print_todo(self, title: str, items: list[str]) -> None: ...
    @abstractmethod
    def print_receipt(self, store: str, items: list[tuple[str, float]],
                      address: str | None, phone: str | None, tax_pct: float) -> None: ...
    @abstractmethod
    def print_free_text(self, text: str, font_size: str) -> None: ...
    @abstractmethod
    def print_qr(self, url: str) -> None: ...
    @abstractmethod
    def print_goatse(self) -> None: ...
    @abstractmethod
    def get_status(self) -> dict: ...  # Returns {online, paper_near_end, paper_out}
    @abstractmethod
    def get_bytes_for_job(self) -> int: ...  # Bytes sent in last print call
```

**Svelte Store Update Pattern:**
- Stores are updated only from `polling.ts` (status) and `api.ts` responses (roll state)
- Components read stores via `$printerStatus` reactive syntax — never mutate directly
- ✅ `printerStatus.set(newStatus)` in polling loop
- ❌ `$printerStatus.printer_online = false` in a component

**Frontend API Call Pattern** — all calls go through `api.ts`:
```typescript
// api.ts pattern — every endpoint follows this shape
export async function printTodo(title: string, items: string[]): Promise<void> {
  const res = await fetch('/api/v1/print/todo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, items })
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail ?? 'Print failed')
  }
}
```

### Process Patterns

**Error Handling Chain:**
```
EscposPrinter raises exception
  → print_service.py catches, raises PrinterError("message")
    → router catches PrinterError, raises HTTPException(503, detail="message")
      → FastAPI returns {"detail": "message"}
        → api.ts throws Error(detail)
          → +page.svelte catches, calls toast.error(error.message)
```
- **Never swallow errors silently** at any layer
- Backend logs every `PrinterError` at WARNING level before re-raising

**Loading State Pattern (frontend):**
```typescript
let loading = false

async function handlePrint() {
  loading = true
  try {
    await api.printTodo(title, items)
    toast.success('Sent to printer ✓')
  } catch (e) {
    toast.error(e.message)
  } finally {
    loading = false  // Always reset
  }
}
```
- `loading` is always local to the form — never a global store
- `PrintButton` accepts `{loading}` prop and handles spinner/disabled state

**Adding a New Print Type — the pattern:**
1. `backend/app/services/print_service.py` — add `def print_shopping_list(...) -> None:`
2. `backend/app/routers/print.py` — add `@router.post("/shopping-list")` route
3. `backend/app/models/print_models.py` — add `ShoppingListRequest` Pydantic model
4. `frontend/src/routes/shopping-list/+page.svelte` — add input UI
5. `frontend/src/lib/api.ts` — add `printShoppingList()` wrapper
6. `frontend/src/routes/+page.svelte` — add card to home screen

### Enforcement Guidelines

**All AI agents MUST:**
- Use `snake_case` for all JSON field names — no camelCase in API payloads
- Return errors as `{"detail": "message"}` — no custom envelope shapes
- Implement new print types by adding to `print_service.py` + `print.py` router — never inline logic in routes
- Use `MockPrinter` in all tests — never attempt to connect to real hardware in tests
- Reset `loading = false` in a `finally` block — never in try or catch only
- Write to `roll_state.json` via atomic rename — never direct file write

**Anti-Patterns to Avoid:**
- ❌ Adding business logic directly in FastAPI route handlers
- ❌ Importing `escpos` anywhere except `printer.py`
- ❌ Creating a new Svelte store for per-form state (use local `let` variables)
- ❌ Fetching API directly in a Svelte component — always use `api.ts`
- ❌ Using `any` type in TypeScript interfaces for API responses

## Project Structure & Boundaries

### Complete Project Directory Structure

```
printserver/
├── README.md
├── .gitignore
├── .env.example                    # PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID, PORT, DATA_DIR
├── .env                            # gitignored — actual values
├── Makefile                        # make build, make deploy, make redeploy, make test
├── Dockerfile                      # Multi-stage: node build → python runtime
├── docker-compose.yml              # Production: image pull + volume + device
├── docker-compose.dev.yml          # Dev override: build from source + hot reload
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # test → build linux/arm64 → push GHCR
│
├── backend/
│   ├── pyproject.toml              # Dependencies + build config
│   ├── requirements-dev.txt        # pytest, pytest-asyncio, httpx (TestClient)
│   ├── .python-version             # 3.12
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app, lifespan, router registration, static mount
│   │   ├── config.py               # Settings from env: PRINTER_VENDOR_ID, PORT, DATA_DIR
│   │   ├── exceptions.py           # PrinterError(Exception)
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── print.py            # POST /api/v1/print/{todo,receipt,free-text,qr,goatse}
│   │   │   ├── status.py           # GET /api/v1/status
│   │   │   ├── admin.py            # GET|POST /api/v1/admin/roll
│   │   │   └── health.py           # GET /health
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── printer.py          # PrinterInterface ABC + EscposPrinter + MockPrinter
│   │   │   ├── print_service.py    # print_todo(), print_receipt(), print_free_text(), etc.
│   │   │   ├── status_cache.py     # StatusCache: background thread, 5s poll, cached result
│   │   │   └── roll_tracker.py     # RollTracker: load/save roll_state.json, estimate_remaining()
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── print_models.py     # TodoRequest, ReceiptRequest, ReceiptItem, FreeTextRequest, QrRequest
│   │   │   ├── status_models.py    # StatusResponse, RollStateResponse
│   │   │   └── admin_models.py     # NewRollRequest, RollStateResponse
│   │   │
│   │   └── data/                   # Volume mount point — /app/data on container
│   │       └── .gitkeep            # Keeps dir in git; roll_state.json is gitignored
│   │
│   └── tests/
│       ├── conftest.py             # mock_printer fixture, tmp_roll_state fixture
│       ├── services/
│       │   ├── test_print_service.py    # All 5 print functions via MockPrinter
│       │   ├── test_roll_tracker.py     # Load/save/estimate with tmp_path
│       │   └── test_status_cache.py     # Cache behaviour with MockPrinter
│       └── routers/
│           ├── test_print_routes.py     # FastAPI TestClient, all print endpoints
│           ├── test_status_routes.py    # Status endpoint returns cached value
│           ├── test_admin_routes.py     # Roll reset + retrieval
│           └── test_health.py           # Health check returns 200
│
└── frontend/
    ├── package.json
    ├── svelte.config.js            # adapter-static, fallback: 'index.html'
    ├── vite.config.ts              # tailwindcss(), sveltekit(), VitePWA(), /api proxy
    ├── tsconfig.json
    ├── .eslintrc.cjs
    ├── .prettierrc
    │
    ├── static/
    │   ├── manifest.webmanifest    # name, display: standalone, icons, theme_color
    │   ├── icon-192.png
    │   ├── icon-512.png
    │   └── favicon.ico
    │
    └── src/
        ├── app.html                # SvelteKit HTML shell
        ├── app.css                 # @import "tailwindcss"; @theme { --color-*: ...; }
        ├── app.d.ts                # TypeScript ambient declarations
        │
        ├── routes/
        │   ├── +layout.svelte      # Starts polling, <Toaster />, status bar, roll gauge
        │   ├── +page.svelte        # Home — PrintCard grid (all print types)
        │   ├── todo/
        │   │   └── +page.svelte    # Dynamic list input + PrintButton
        │   ├── receipt/
        │   │   └── +page.svelte    # Mini-ledger builder + running total + PrintButton
        │   ├── free-text/
        │   │   └── +page.svelte    # Textarea + font size picker + PrintButton
        │   ├── qr-code/
        │   │   └── +page.svelte    # URL input + QR preview + PrintButton
        │   ├── goatse/
        │   │   └── +page.svelte    # Single PrintButton (no input)
        │   └── admin/
        │       └── +page.svelte    # New Roll form + current state display
        │
        └── lib/
            ├── types.ts            # TypeScript interfaces mirroring API models
            ├── api.ts              # All fetch wrappers — single source of truth
            ├── stores.ts           # printerStatus (writable), rollState (writable)
            ├── polling.ts          # startPolling() / stopPolling() — called from layout
            └── components/
                ├── StatusDot.svelte     # Pulsing green / flat grey / amber dot
                ├── RollGauge.svelte     # Arc gauge showing estimated_remaining_pct
                ├── PrintButton.svelte   # Full-width button, loading prop, spinner
                └── PrintCard.svelte     # Home screen card (icon, name, description)
```

### Architectural Boundaries

**API Boundary — FastAPI serves everything:**
- `/api/v1/*` — REST API endpoints (routers)
- `/` and all non-API paths — SvelteKit SPA (`app/static/`, `index.html` fallback)
- `/docs`, `/redoc` — OpenAPI documentation
- `/health` — container health check

**Service Boundaries — no cross-service imports:**
- `print_service.py` → imports `PrinterInterface` only (never `escpos` directly)
- `status_cache.py` → imports `PrinterInterface` only
- `roll_tracker.py` → no external imports beyond stdlib + config
- Routers → import services only (never `printer.py` or `escpos` directly)

**Hardware Boundary:**
- `EscposPrinter` in `printer.py` is the only place `escpos` is imported
- All other code uses `PrinterInterface` — fully swappable for `MockPrinter` in tests

**State Boundary:**
- `roll_state.json` read/written exclusively by `RollTracker`
- Status cache read/written exclusively by `StatusCache`
- No direct file access from routers or route handlers

### Requirements to Structure Mapping

| FR Category | Backend Location | Frontend Location |
|---|---|---|
| Print Operations (FR1–FR8) | `routers/print.py`, `services/print_service.py`, `models/print_models.py` | `routes/{todo,receipt,free-text,qr-code,goatse}/`, `lib/api.ts` |
| Printer Status & Monitoring (FR9–FR12) | `services/printer.py`, `services/status_cache.py`, `routers/status.py` | `lib/polling.ts`, `lib/stores.ts`, `components/StatusDot.svelte` |
| Till Roll Management (FR13–FR18) | `services/roll_tracker.py`, `routers/admin.py`, `models/admin_models.py` | `routes/admin/+page.svelte`, `components/RollGauge.svelte` |
| Frontend Experience (FR19–FR25) | `main.py` (static mount) | `routes/`, `components/`, `static/manifest.webmanifest`, `vite.config.ts` |
| System Reliability (FR26–FR30) | `routers/health.py`, `services/printer.py` (error handling), `app/data/` | — |
| API & Integration (FR31–FR34) | `main.py`, all `routers/`, all `models/` | `lib/api.ts`, `lib/types.ts` |
| Developer Operations (FR35–FR38) | `services/printer.py` (MockPrinter), `tests/` | `.github/workflows/ci.yml`, `Makefile` |

### Integration Points

**Data Flow — print request:**
```
Phone → SvelteKit PWA → api.ts POST /api/v1/print/todo
  → FastAPI print.py router
    → print_service.print_todo()
      → EscposPrinter.print_todo() → USB → physical paper
      → roll_tracker.add_bytes(n) → roll_state.json (atomic write)
  → {"success": true}
→ toast.success('Sent to printer ✓')
```

**Data Flow — status polling:**
```
+layout.svelte onMount → polling.ts startPolling()
  → every 5s: api.ts GET /api/v1/status
    → FastAPI status.py → status_cache.get_cached()
    → {"printer_online": true, "paper_near_end": false, "estimated_remaining_pct": 72}
  → printerStatus.set(result) → StatusDot re-renders
```

**Key configuration files:**

| File | Purpose |
|---|---|
| `.env` | `PRINTER_VENDOR_ID`, `PRINTER_PRODUCT_ID`, `PORT=9000`, `DATA_DIR=/app/data` |
| `docker-compose.yml` | Production: pulls from GHCR, device passthrough, volume, restart policy |
| `docker-compose.dev.yml` | Dev: builds locally, mounts source for hot reload |
| `Dockerfile` | Stage 1: `npm run build`; Stage 2: Python runtime + copy static build |
| `.github/workflows/ci.yml` | pytest → vitest → buildx linux/arm64 → push GHCR |
| `Makefile` | `make test`, `make build`, `make redeploy` |

### Development Workflow

**Local dev (no Pi required):**
```bash
# Terminal 1
cd backend && uvicorn app.main:app --reload --port 9000

# Terminal 2
cd frontend && npm run dev  # Vite on :5173, proxies /api/ → localhost:9000
```

**Deploy to Pi:**
```bash
git push origin main
# GitHub Actions: test → build → push GHCR
# Watchtower: detects new digest → pulls → restarts
# (or manually: ssh pi 'redeploy')
```

## Architecture Validation Results

### Coherence Validation

**Decision Compatibility:**
All technology choices are mutually compatible. Python 3.12 + FastAPI 0.115 + Pydantic v2 are a stable, tested combination. SvelteKit 2 + Svelte 5 + Tailwind v4 + `vite-plugin-pwa` are all compatible with Vite as the shared build toolchain. `python-escpos 3.1` supports Python 3.12. `python:3.12-slim-bookworm` is the correct multi-arch base image for ARM64 (Alpine excluded). Threading model (background `threading.Thread`) is compatible with FastAPI's sync route handlers.

**Pattern Consistency:**
Naming conventions are consistent: `snake_case` JSON throughout, Python `snake_case` functions/files, TypeScript `PascalCase` components, `kebab-case` route folders. Error chain is coherent end-to-end. Store update patterns are unambiguous. Loading state pattern (local `let`, `finally` reset) is simple and reproducible.

**Structure Alignment:**
Project structure directly enables the 2-file add pattern (FR35). `PrinterInterface` abstraction is the correct seam for testability (NFR13). Volume mount for `data/` maps directly to FR29. `restart: unless-stopped` maps to FR26/NFR6. FastAPI static file serving with SPA fallback maps to PWA requirement (FR23/FR24).

### Requirements Coverage Validation

**All 38 Functional Requirements: COVERED**

| FR Category | Coverage |
|---|---|
| Print Operations (FR1–FR8) | `print_service.py` + `routers/print.py` + `printer.py` abstraction |
| Status & Monitoring (FR9–FR12) | `status_cache.py` background thread + `routers/status.py` + `polling.ts` |
| Till Roll Management (FR13–FR18) | `roll_tracker.py` + `routers/admin.py` + `RollGauge.svelte` |
| Frontend Experience (FR19–FR25) | SvelteKit routes + components + `vite-plugin-pwa` + service worker |
| System Reliability (FR26–FR30) | `restart: unless-stopped` + `health.py` + `PrinterError` chain + udev + volume |
| API & Integration (FR31–FR34) | FastAPI routers + Pydantic models + OpenAPI |
| Developer Operations (FR35–FR38) | 2-file pattern + CI/CD workflow + `MockPrinter` + `Makefile` |

**All 23 Non-Functional Requirements: COVERED**

Key NFR–Architecture mappings:
- NFR2 (< 200ms status): status cache eliminates blocking hardware calls per request
- NFR6 (30s crash recovery): `restart: unless-stopped` handles this at container level
- NFR13 (testable without hardware): `MockPrinter` implementing `PrinterInterface`
- NFR14 (10min deploy): GitHub Actions ARM64 build ~8-10min + Watchtower restart (achievable with layer caching)

### Implementation Readiness Validation

**Decision Completeness:** All critical decisions documented with specific versions (FastAPI 0.115, SvelteKit 2, Svelte 5, Tailwind v4, python-escpos 3.1, Python 3.12). Two pre-development spikes documented with clear success criteria.

**Structure Completeness:** Full directory tree defined to file level. All integration points specified. All component boundaries documented. FR-to-file mapping complete.

**Pattern Completeness:** 8 conflict points identified and resolved. `PrinterInterface` contract specified with exact method signatures. API response envelopes standardised. Error chain documented end-to-end. Loading state pattern specified with code example.

### Gap Analysis Results

**Minor Gaps (non-blocking):**

1. **FastAPI route registration order** — API routers (`/api/v1/`) must be registered *before* the `StaticFiles` mount in `main.py`, or the SPA catch-all will intercept API calls. Document explicitly as a comment in `main.py`.

2. **Status cache startup resilience** — Background poll thread must initialise cache to `{"printer_online": false, ...}` before first poll completes, and must not crash if printer is unavailable at container start.

3. **`curl` in Docker image** — `HEALTHCHECK` uses `curl`. `python:3.12-slim-bookworm` does not include it by default. Dockerfile must add: `RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*`

4. **Frontend dependency declarations** — `svelte-sonner` (runtime) and `vite-plugin-pwa` (devDependency) must be explicit in `package.json`. Include in first implementation story.

**No Critical Gaps.**

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High — all 16 checklist items confirmed, no critical gaps, two pre-development spikes clearly scoped.

**Key Strengths:**
- `PrinterInterface` abstraction cleanly separates hardware from business logic — enables full test coverage without physical hardware
- 2-file add pattern is mechanical and teachable — new print types follow an identical template every time
- Status cache eliminates the most significant UX risk (blocking polls on offline printer)
- Atomic JSON write prevents state corruption on crash
- Monorepo + multi-stage Dockerfile keeps deployment simple without sacrificing separation

**Areas for Future Enhancement:**
- V2 auth: router structure is middleware-ready from day one
- Reverse proxy / named hostname: straightforward addition behind Nginx Proxy Manager
- Structured logging: `structlog` can replace stdlib logging with no other changes

### Implementation Handoff

**First steps:**
1. Resolve hardware spike: connect printer to Pi → `lsusb` → test `Usb()` → validate udev symlink
2. Resolve PiHole port spike: confirm port 9000 is free
3. `npm create svelte@latest frontend` → install Tailwind v4 + vite-plugin-pwa + svelte-sonner
4. Create `backend/` structure manually
5. Implement `PrinterInterface` + `MockPrinter` first — everything else builds on this

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use `MockPrinter` in tests — never real hardware
- Respect the `PrinterInterface` boundary — never import `escpos` outside `printer.py`
- Use `snake_case` in all JSON fields — no exceptions
- Register API routers before `StaticFiles` mount in `main.py`
