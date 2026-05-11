# Story 3.7: QR Code + Goatse Pages

Status: review

## Story

As a developer,
I want the QR code and Goatse print pages implemented,
So that users can print QR codes from URLs and trigger the goatse print.

## Acceptance Criteria

1. **Given** `frontend/src/routes/qr-code/+page.svelte` **When** a valid URL is typed **Then** a live QR code preview renders below the input using a client-side QR library; when the input is cleared, the preview disappears

2. **Given** an invalid URL (missing `https://` prefix) **When** Print is tapped **Then** client-side validation prevents submission and shows an inline error message; no API call is made

3. **Given** a valid URL and Print tapped **When** `api.printQr(url)` completes **Then** the appropriate success or failure toast fires and `loading` resets

4. **Given** `frontend/src/routes/goatse/+page.svelte` **When** rendered **Then** it shows a single full-width `<PrintButton>` with no other input; on tap, `api.printGoatse()` is called and the appropriate toast fires

## Tasks / Subtasks

- [x] Task 1: Install `qrcode` library
  - [x] `npm install qrcode` (runtime dep — renders in browser)
  - [x] `npm install -D @types/qrcode`

- [x] Task 2: Create `frontend/src/routes/qr-code/+page.svelte` (AC: 1, 2, 3)
  - [x] URL input bound to `url` state
  - [x] `$effect` generating QR data URL whenever `url` changes and is a valid URL
  - [x] QR preview image shown when `qrDataUrl` is set; hidden when empty
  - [x] Inline error message shown on print attempt with invalid URL
  - [x] `printQr(url)` on valid print; `loading` in `finally`; toasts

- [x] Task 3: Create `frontend/src/routes/goatse/+page.svelte` (AC: 4)
  - [x] Single `<PrintButton>` calling `printGoatse()`
  - [x] `loading` in `finally`; toasts

- [x] Task 4: Verify build and tests
  - [x] `cd frontend && npm run build` — clean
  - [x] `cd frontend && npm run test` — 12/12 passing

## Dev Notes

### New Dependency: `qrcode`

`qrcode` generates QR codes as data URLs (base64 PNG). Install as runtime dep (renders in browser):
```
npm install qrcode
npm install -D @types/qrcode
```

```typescript
import QRCode from 'qrcode'
// Generate data URL:
const dataUrl = await QRCode.toDataURL(url, { width: 200, margin: 1, color: { dark: '#000', light: '#fff' } })
```

### QR Preview with `$effect`

`QRCode.toDataURL` is async, so use `$effect` (not `$derived`) to update `qrDataUrl` reactively:

```svelte
let url = $state('')
let qrDataUrl = $state('')

$effect(() => {
  const trimmed = url.trim()
  if (isValidUrl(trimmed)) {
    QRCode.toDataURL(trimmed, { width: 200, margin: 1 })
      .then(data => { qrDataUrl = data })
      .catch(() => { qrDataUrl = '' })
  } else {
    qrDataUrl = ''
  }
})
```

`$effect` automatically tracks `url` as a dependency and re-runs when it changes.

### URL Validation

Use the `URL` constructor — it handles all valid URLs (http:// and https://):

```typescript
function isValidUrl(s: string): boolean {
  if (!s) return false
  try { new URL(s); return true } catch { return false }
}
```

The AC says "missing https:// prefix" as the example of an invalid URL. The `URL` constructor correctly rejects bare strings without a scheme. This is the right validation.

Inline error: show a `<p>` element when `urlError` is set, clear it when URL becomes valid.

### `package.json` Placement

`qrcode` is a **runtime** dependency (renders in the browser) — add to `dependencies`, not `devDependencies`. This matches the project rule: `@types/qrcode` → `devDependencies`.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 3.7 ACs]
- [Source: `frontend/src/lib/api.ts` — `printQr`, `printGoatse`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — clean first attempt.

### Completion Notes List

- AC1 ✅: `$effect` watches `url`, calls `QRCode.toDataURL()` on valid URLs, renders `<img>` preview; clears on empty/invalid
- AC2 ✅: `handlePrint` checks `isValidUrl()` via `URL` constructor; sets `urlError` and returns before any API call
- AC3 ✅: `printQr(trimmed)` → `toast.success` / `toast.error`; `loading` always reset in `finally`
- AC4 ✅: Goatse page is a single `<PrintButton>` — no input, `printGoatse()` on click
- `qrcode` added as runtime dep; `@types/qrcode` as devDep; 25 new packages installed

### File List

- `frontend/src/routes/qr-code/+page.svelte` — NEW
- `frontend/src/routes/goatse/+page.svelte` — NEW
- `frontend/package.json` — MODIFIED (qrcode added)
- `frontend/package-lock.json` — MODIFIED
