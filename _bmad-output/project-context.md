---
project_name: PrintServer
user_name: Conor
date: 2026-05-11
sections_completed:
  - technology_stack
  - language_rules
  - framework_rules
  - testing_rules
  - quality_rules
  - workflow_rules
  - anti_patterns
status: complete
optimized_for_llm: true
---

# Project Context for AI Agents

_Critical rules and patterns AI agents must follow when implementing code for PrintServer.
Focus is on unobvious details that agents commonly miss._

---

## Technology Stack

**Backend:** Python 3.12, FastAPI ≥0.115, Pydantic v2, uvicorn[standard], python-escpos ≥3.1, pyusb ≥1.0
**Frontend:** SvelteKit 2, Svelte 5 (runes mode), TypeScript 5, Vite 6, Tailwind CSS v4 (`@tailwindcss/vite`), svelte-sonner 0.3, qrcode 1.5.4, vite-plugin-pwa 0.21
**Testing:** pytest + pytest-asyncio + httpx (backend); Vitest 3 (frontend)
**Runtime:** Docker `linux/arm64`, base image `python:3.12-slim-bookworm` (NOT Alpine)
**Deploy:** GitHub Actions → GHCR → Watchtower auto-pull to Pi at `192.168.0.25:9000`

---

## Language-Specific Rules

### Python
- `snake_case` for variables, functions, files, modules; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants
- Pydantic models: `PascalCase` with `Request`/`Response` suffix (`TodoRequest`, `StatusResponse`)
- Datetime strings: ISO 8601 UTC only — never Unix timestamps
- `escpos` imported **only** in `backend/app/services/printer.py` — nowhere else
- `roll_state.json` writes: atomic rename (write temp → `os.replace`) — never direct write
- Never use `except Exception: pass` — silent failures hide real problems

### TypeScript / Svelte
- All API fields: `snake_case` throughout — no camelCase, no conversion layer, ever
- Import alias: `$lib/` resolves to `frontend/src/lib/` — always use alias, never relative `../../`
- **Svelte 5 runes mode is active** — use `$state()`, `$derived()`, `$effect()`, `$props()` only
  - ❌ NOT `export let`, `$:` reactive declarations, or `<slot />`
  - Children: `import type { Snippet } from 'svelte'` + `{@render children()}`
  - Event handlers: `onclick={fn}` prop — not `on:click` (that is Svelte 4)
- `$effect()` side effects: return a cleanup function to cancel timers/subscriptions
- `loading = false` **always** in `finally` — never in `try` or `catch` only

---

## Framework-Specific Rules

### FastAPI
- API routers **must** be registered in `main.py` **before** `StaticFiles` mount — order matters
- `PrinterError` → `HTTPException(503, detail="...")` — never 500 for printer faults
- Error envelope: always `{"detail": "message"}` — never invent custom shapes
- Print endpoint success: `{"success": true}` — health: `{"status": "ok"}`
- No CORS middleware — frontend is served from the same origin as the API
- Route prefix: `/api/v1/` for all API endpoints; `/health` is a separate top-level route

### SvelteKit
- `adapter-static` + `fallback: 'index.html'` — pure SPA, no SSR
- SSR disabled via `export const ssr = false` in `+layout.ts` — not in `svelte.config.js`
- Route folders: `kebab-case` (`src/routes/free-text/`, `src/routes/qr-code/`)
- Never fetch API directly in components — all calls go through `$lib/api.ts`
- Never create Svelte stores for per-form state — use local `let x = $state()`
- `<Toaster />` rendered once in `+layout.svelte` — do not add it to other routes
- Toasts: `toast.success('...')` / `toast.error('...')` from `svelte-sonner`

### Tailwind CSS v4
- No `tailwind.config.js` — config lives in `@theme {}` in `frontend/src/app.css`
- Theme tokens: `--color-bg: #0f0f0f`, `--color-surface: #1a1a1a`, `--color-accent: #22c55e`
- Token utilities: `bg-bg`, `bg-surface`, `bg-accent`, `text-accent`
- Touch targets: `min-h-[44px]` minimum on all interactive elements (buttons, inputs, cards)

### python-escpos (Jolimark-specific)
- `p.set(height=N, width=N)` **requires `custom_size=True`** — without it, silently ignored
- Font sizes: `font='b'` (small), `font='a'` (medium), `font='a', custom_size=True, width=2, height=2` (large)
- **Never call `p.qr()`** — it partially executes on this printer, feeds paper, and corrupts USB state
  (Errno 5). Always use qrcode library raster: `QRCode(border=2, box_size=6)` → `p.image()`
- USB Errno 5 / printer power cycle: container must be restarted to re-initialise USB handle

---

## Testing Rules

### Backend (pytest)
- All print tests use `MockPrinter` — never attempt real hardware in tests
- `mock_printer` and `tmp_roll_state` fixtures defined in `backend/tests/conftest.py`
- Router tests use `httpx.AsyncClient` with the FastAPI app
- No test may import `escpos` directly
- `PrinterError` propagation: configure `MockPrinter` to raise, assert endpoint returns 503
- Run: `pytest backend/` from repo root

### Frontend (Vitest)
- Unit tests live alongside source in `frontend/src/lib/` (e.g. `api.test.ts`)
- Mock fetch: `vi.stubGlobal('fetch', vi.fn().mockResolvedValue({...}))`
- Always `vi.restoreAllMocks()` in `afterEach`
- `@testing-library/svelte` is NOT installed — component rendering tests require installing it first
- Run: `cd frontend && npm run test`

### Definition of Done
- `cd frontend && npm run build` must pass before any story is marked done
- Any new ESC/POS command requires a live print test on the physical Jolimark printer
- UI stories require manual verification on a phone in PWA standalone mode (no browser chrome)

---

## Code Quality & Style Rules

### Naming
- Backend files: `snake_case.py` | Frontend components: `PascalCase.svelte` | Frontend utils: `camelCase.ts`
- TypeScript interfaces: `PascalCase` | Store names: `camelCase` (`printerStatus`, `rollState`)

### Organisation
- Business logic in `services/` — thin delegation only in `routers/`
- New print type = exactly 2 files: add function to `print_service.py`, add route to `routers/print.py`
- All API fetch wrappers in `$lib/api.ts` — single source of truth
- Shared UI components in `$lib/components/` as `PascalCase.svelte`

### Comments
- Write no comments by default
- Only comment when the WHY is non-obvious (hardware quirk, subtle invariant, specific bug workaround)
- Never comment WHAT the code does — names should do that

---

## Development Workflow Rules

### Local Dev
- Backend: `cd backend && uvicorn app.main:app --reload --port 9000`
- Frontend: `cd frontend && npm run dev` (Vite on :5173, proxies `/api/` → localhost:9000)

### Deploy
- Pi SSH: `ssh -i ~/.ssh/pi_printserver conor@192.168.0.25`
- Container: `printserver` | Port: `9000`
- Restart after printer power cycle: Admin page → "Restart Service", or `docker restart printserver`
- Never use ports 80, 443 (PiHole) or 5000 (Octoprint)

### Environment
- `.env` (gitignored): `PRINTER_VENDOR_ID=0x1ba0`, `PRINTER_PRODUCT_ID=0x220a`, `PORT=9000`, `DATA_DIR=/app/data`
- `API_KEY`: optional env var — when unset, all endpoints are open (LAN homelab default)
- Never commit `.env` or `backend/app/data/*.json`

### Docker
- Base image: `python:3.12-slim-bookworm` — NOT Alpine (musl libc breaks escpos USB)
- Requires `privileged: true` for USB device access
- `devices: ["/dev/receipt-printer:/dev/receipt-printer"]` — stable udev symlink
- `volumes: ["./data:/app/data"]` — roll state persists across restarts

---

## Critical Don't-Miss Rules

### Hard Anti-Patterns
- ❌ Import `escpos` anywhere except `backend/app/services/printer.py`
- ❌ Use camelCase in any JSON field name (requests, responses, TypeScript interfaces)
- ❌ Call `p.qr()` on the Jolimark — always use qrcode raster fallback with `box_size=6`
- ❌ Use `p.set(height=N, width=N)` without `custom_size=True`
- ❌ Write directly to `roll_state.json` — always use `RollTracker` atomic write
- ❌ Register `StaticFiles` in `main.py` before API routers
- ❌ Create Svelte stores for per-form state — use local `$state()`
- ❌ Fetch API directly in a Svelte component — always use `$lib/api.ts`
- ❌ Use `export let`, `$:`, or `<slot />` — Svelte 5 runes only
- ❌ Reset `loading = false` in `try` or `catch` — always in `finally`
- ❌ Use `except Exception: pass` — silent failures hide root causes
- ❌ Use Alpine Linux as Docker base — musl libc breaks python-escpos USB

### Hardware Realities
- Errno 5 (USB I/O error) = printer in bad state → container restart required
- Printer power cycle → container restart required (USB singleton holds stale handle)
- `get_status()` on Jolimark calls `paper_status()` internally: returns 2=OK, 1=near-end, 0=out
- MockPrinter cannot catch hardware partial-execution bugs — always test new ESC/POS on real hardware

### State Patterns
- `printerStatus` store: written only by `polling.ts`
- `rollState` store: written only by admin page fetch responses
- `OFFLINE_STATUS` constant: exported from `stores.ts` — import from there, never redefine
- `startPolling()` fires an immediate first call then 5s interval — don't call `getStatus()` separately

---

## Usage Guidelines

**For AI Agents:** Read this file before implementing any code. Follow ALL rules exactly. When in doubt, prefer the more restrictive option. Flag new hardware discoveries for addition here.

**For Humans:** Keep lean — only document unobvious rules. Update when stack or patterns change.

_Last Updated: 2026-05-11_
