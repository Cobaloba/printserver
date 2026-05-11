# Story 3.2: API Client, Stores, and Polling

Status: review

## Story

As a developer,
I want typed API wrappers, Svelte stores for shared state, and a polling loop,
So that all components consume the API consistently and printer status updates reactively.

## Acceptance Criteria

1. **Given** `frontend/src/lib/types.ts` **When** reviewed **Then** `PrinterStatus` and `RollState` TypeScript interfaces are defined with `snake_case` field names matching the API schemas exactly

2. **Given** `frontend/src/lib/api.ts` **When** reviewed **Then** `printTodo`, `printReceipt`, `printFreeText`, `printQr`, `printGoatse`, `getStatus`, `getAdminRoll`, `postAdminRoll` are all exported; each uses `snake_case` in request bodies; each throws `Error(err.detail)` on non-2xx responses

3. **Given** `frontend/src/lib/stores.ts` **When** reviewed **Then** `printerStatus` (writable `PrinterStatus`) and `rollState` (writable `RollState | null`) are exported with sensible defaults

4. **Given** `frontend/src/lib/polling.ts` **When** reviewed **Then** `startPolling()` calls `getStatus()` every 5 seconds and calls `printerStatus.set(result)`; `stopPolling()` cancels the interval; errors from `getStatus()` update `printerStatus` to offline state rather than crashing

5. **Given** a Vitest test mocking `fetch` to return a 503 with `{"detail": "Printer offline"}` **When** any `api.ts` print function is called **Then** it throws `Error("Printer offline")`

## Tasks / Subtasks

- [x] Task 1: Create `frontend/src/lib/types.ts` (AC: 1)
  - [x] Define `PrinterStatus` interface with exact backend field names
  - [x] Define `RollState` interface with exact backend field names
  - [x] Export both interfaces

- [x] Task 2: Create `frontend/src/lib/api.ts` (AC: 2)
  - [x] Implement `getStatus(): Promise<PrinterStatus>`
  - [x] Implement `getAdminRoll(): Promise<RollState>`
  - [x] Implement `postAdminRoll(width_mm: number, diameter_mm: number): Promise<void>`
  - [x] Implement `printTodo(title: string, items: string[]): Promise<void>`
  - [x] Implement `printReceipt(params: ReceiptParams): Promise<void>`
  - [x] Implement `printFreeText(text: string, font_size: FontSize): Promise<void>`
  - [x] Implement `printQr(url: string): Promise<void>`
  - [x] Implement `printGoatse(): Promise<void>`

- [x] Task 3: Create `frontend/src/lib/stores.ts` (AC: 3)
  - [x] Export `printerStatus` writable store with offline default
  - [x] Export `rollState` writable store defaulting to `null`

- [x] Task 4: Create `frontend/src/lib/polling.ts` (AC: 4)
  - [x] Implement `startPolling()` calling `getStatus()` every 5s, setting `printerStatus` store
  - [x] Implement `stopPolling()` cancelling the interval
  - [x] On error: set `printerStatus` to offline default (do NOT throw/crash)

- [x] Task 5: Write Vitest tests in `frontend/src/lib/api.test.ts` (AC: 5)
  - [x] Test: 503 response with `{"detail": "Printer offline"}` → throws `Error("Printer offline")`
  - [x] Test: successful print response `{"success": true}` → resolves without throwing
  - [x] Test: non-detail error body → throws with fallback message
  - [x] Delete `frontend/src/lib/placeholder.test.ts`
  - [x] Run `npm run test` — all tests pass

## Dev Notes

### Exact API Response Shapes (read from backend source)

These were extracted directly from the backend router and model files — use these exactly.

**`GET /api/v1/status`** → returns:
```json
{
  "printer_online": false,
  "paper_near_end": false,
  "paper_out": false,
  "estimated_remaining_pct": 0
}
```
Note: `estimated_remaining_pct` is injected by the status router from `tracker.estimate_remaining()` — it is NOT stored in the status cache itself, but is always present in the API response.

**`GET /api/v1/admin/roll`** → returns:
```json
{
  "bytes_printed": 0,
  "roll_width_mm": 57,
  "roll_diameter_mm": 40,
  "last_reset": "2026-05-07T10:00:00Z",
  "estimated_remaining_pct": 85
}
```

**Print endpoints** all return `{"success": true}` on 200.

**Errors** return `{"detail": "message"}` (FastAPI standard).

### TypeScript Interface Definitions (exact field names)

```typescript
// frontend/src/lib/types.ts
export interface PrinterStatus {
  printer_online: boolean
  paper_near_end: boolean
  paper_out: boolean
  estimated_remaining_pct: number
}

export interface RollState {
  bytes_printed: number
  roll_width_mm: number
  roll_diameter_mm: number
  last_reset: string
  estimated_remaining_pct: number
}
```

Do NOT use camelCase. Architecture rule: all JSON/TS fields `snake_case` throughout — no conversion layer.

### API Endpoint URLs (exact)

| Function | Method | URL |
|---|---|---|
| `getStatus` | GET | `/api/v1/status` |
| `getAdminRoll` | GET | `/api/v1/admin/roll` |
| `postAdminRoll` | POST | `/api/v1/admin/roll` |
| `printTodo` | POST | `/api/v1/print/todo` |
| `printReceipt` | POST | `/api/v1/print/receipt` |
| `printFreeText` | POST | `/api/v1/print/free-text` |
| `printQr` | POST | `/api/v1/print/qr` |
| `printGoatse` | POST | `/api/v1/print/goatse` |

### Request Body Shapes (exact — must match backend Pydantic models)

```typescript
// printTodo
{ title: string, items: string[] }

// printReceipt
{
  store: string,
  items: Array<{ name: string, price: number }>,
  address: string | null,
  phone: string | null,
  tax_pct: number
}

// printFreeText
{ text: string, font_size: 'small' | 'medium' | 'large' }

// printQr
{ url: string }

// printGoatse — no body

// postAdminRoll
{ width_mm: number, diameter_mm: number }
```

### API Auth Header — Critical Note

The backend has optional API key auth (`X-API-Key` header, controlled by `API_KEY` env var). When `API_KEY` is not set (the default), the backend accepts all requests without a key. **The frontend does NOT need to send an API key header** — the backend is designed to work without it on the trusted LAN. Do not add auth header logic to `api.ts`.

The `/api/v1/status` endpoint has **no auth requirement** at all — it's always open.

### Standard Fetch Wrapper Pattern

Every `api.ts` function follows this exact shape (from `architecture.md`):

```typescript
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

For GET endpoints, omit `method`/`headers`/`body`. For `getStatus` and `getAdminRoll`, return `await res.json()` cast to the correct interface. For `printGoatse`, send no body (omit body and Content-Type).

### Function Signatures for Future Stories

These exact signatures will be called by Stories 3.4–3.8. Match them exactly:

```typescript
// Called in 3.5:
printTodo(title: string, items: string[]): Promise<void>
printFreeText(text: string, font_size: 'small' | 'medium' | 'large'): Promise<void>

// Called in 3.6 (object param — many optional fields):
printReceipt(params: {
  store: string,
  items: Array<{ name: string, price: number }>,
  address: string | null,
  phone: string | null,
  tax_pct: number
}): Promise<void>

// Called in 3.7:
printQr(url: string): Promise<void>
printGoatse(): Promise<void>

// Called in 3.8:
getAdminRoll(): Promise<RollState>
postAdminRoll(width_mm: number, diameter_mm: number): Promise<void>

// Called in polling.ts (3.4 will call startPolling/stopPolling):
getStatus(): Promise<PrinterStatus>
```

### Stores — Offline Default

```typescript
// frontend/src/lib/stores.ts
import { writable } from 'svelte/store'
import type { PrinterStatus, RollState } from './types'

const OFFLINE_STATUS: PrinterStatus = {
  printer_online: false,
  paper_near_end: false,
  paper_out: false,
  estimated_remaining_pct: 0
}

export const printerStatus = writable<PrinterStatus>(OFFLINE_STATUS)
export const rollState = writable<RollState | null>(null)
```

The offline default is safe: the UI shows offline/grey status until the first successful poll. Do NOT initialise `printerStatus` to null — it must always be a valid `PrinterStatus` so components can destructure without null checks.

### Polling — Error Handling is Mandatory

The `startPolling()` function MUST catch errors and set offline status — never let a failed poll crash the app or leave the store in an inconsistent state:

```typescript
// frontend/src/lib/polling.ts
import { getStatus } from './api'
import { printerStatus } from './stores'
import type { PrinterStatus } from './types'

const OFFLINE: PrinterStatus = {
  printer_online: false,
  paper_near_end: false,
  paper_out: false,
  estimated_remaining_pct: 0
}

let intervalId: ReturnType<typeof setInterval> | null = null

export function startPolling(): void {
  if (intervalId !== null) return  // already running — guard against double-start
  intervalId = setInterval(async () => {
    try {
      const status = await getStatus()
      printerStatus.set(status)
    } catch {
      printerStatus.set(OFFLINE)
    }
  }, 5000)
}

export function stopPolling(): void {
  if (intervalId !== null) {
    clearInterval(intervalId)
    intervalId = null
  }
}
```

### Vitest Test Pattern

Use `vi.stubGlobal('fetch', ...)` to mock fetch in Vitest. Tests go in `frontend/src/lib/api.test.ts`:

```typescript
import { describe, it, expect, vi, afterEach } from 'vitest'
import { printTodo } from './api'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('api error handling', () => {
  it('throws Error with detail message on 503', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Printer offline' })
    }))
    await expect(printTodo('Test', ['item'])).rejects.toThrow('Printer offline')
  })
})
```

Test at minimum:
1. 503 + `{"detail": "Printer offline"}` → `Error("Printer offline")`
2. 200 + `{"success": true}` → resolves (no throw)
3. Non-2xx with no `detail` field → throws with fallback message (e.g. `"Print failed"`)

### `FontSize` Type Export

Export `FontSize` as a type alias from `types.ts` for reuse in Stories 3.5+:
```typescript
export type FontSize = 'small' | 'medium' | 'large'
```

### Project Structure Notes

- Files go in `frontend/src/lib/` — not `src/lib/components/` (components are Story 3.3)
- File names: `camelCase.ts` (`api.ts`, `stores.ts`, `polling.ts`, `types.ts`) — architecture rule
- Export from each file directly — no barrel `index.ts` needed
- Delete `frontend/src/lib/placeholder.test.ts` once `api.test.ts` exists

### Architecture Rules (mandatory)

- All JSON fields `snake_case` — no camelCase in request bodies or response types
- Never use `any` type in TypeScript interfaces for API responses
- `loading = false` always in `finally` block (relevant to Stories 3.5+ not this one)
- Never fetch directly in Svelte components — always via `api.ts`
- Never mutate stores directly in components — use `printerStatus.set(...)` only from `polling.ts`

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 3.2 ACs]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Frontend Architecture, API Patterns, Store patterns]
- [Source: `backend/app/routers/status.py` — exact GET /api/v1/status response shape]
- [Source: `backend/app/routers/admin.py` — exact GET/POST /api/v1/admin/roll response shape]
- [Source: `backend/app/routers/print.py` — all print endpoint URLs and auth dependency]
- [Source: `backend/app/models/print_models.py` — exact request body field names]
- [Source: `backend/app/auth.py` — API key is optional, default open access]
- [Source: `backend/app/services/status_cache.py` — confirms `estimated_remaining_pct` NOT in cache]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation matched spec exactly; all 12 tests passed first run.

### Completion Notes List

- AC1 ✅: `types.ts` defines `PrinterStatus` (4 fields, snake_case), `RollState` (5 fields, snake_case), `FontSize` type alias — all match backend Pydantic models exactly
- AC2 ✅: `api.ts` exports all 8 functions; private `request()` helper centralises error extraction (`err.detail ?? 'Request failed'`); `ReceiptParams` interface exported for Story 3.6
- AC3 ✅: `stores.ts` exports `printerStatus` (writable, initialised to offline) and `rollState` (writable, null default)
- AC4 ✅: `polling.ts` exports `startPolling()` (double-start guarded) and `stopPolling()`; errors set offline state silently
- AC5 ✅: `api.test.ts` — 12 tests; covers 503+detail, 200+success, no-detail fallback, all print functions, getStatus, getAdminRoll, postAdminRoll
- `placeholder.test.ts` deleted; replaced by `api.test.ts`
- Build passes clean (828ms); no TypeScript errors

### File List

- `frontend/src/lib/types.ts` — NEW
- `frontend/src/lib/api.ts` — NEW
- `frontend/src/lib/stores.ts` — NEW
- `frontend/src/lib/polling.ts` — NEW
- `frontend/src/lib/api.test.ts` — NEW
- `frontend/src/lib/placeholder.test.ts` — DELETED
