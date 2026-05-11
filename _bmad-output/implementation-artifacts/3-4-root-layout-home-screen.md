# Story 3.4: Root Layout + Home Screen

Status: review

## Story

As a developer,
I want the root layout to show printer status and roll level at all times, and the home screen to list all print types as cards,
So that users can see printer state before choosing what to print.

## Acceptance Criteria

1. **Given** `frontend/src/routes/+layout.svelte` **When** reviewed **Then** it calls `startPolling()` in `onMount` and `stopPolling()` in `onDestroy`; renders `<StatusDot />` bound to `$printerStatus`; renders `<RollGauge pct={$printerStatus.estimated_remaining_pct} />`; renders `<Toaster />` from svelte-sonner

2. **Given** `frontend/src/routes/+page.svelte` (home screen) **When** rendered **Then** it shows 6 `PrintCard` components — Free Text, QR Code, Todo, Receipt, Goatse, Admin — each linking to the correct route

3. **Given** a 375px viewport in dark mode **When** the home screen renders **Then** all 6 cards are visible without horizontal scrolling; the status bar with dot and gauge is visible at the top

4. **Given** the printer transitions to offline (polling returns `printer_online=false`) **When** the next poll fires **Then** the `StatusDot` updates to grey within 6 seconds

## Tasks / Subtasks

- [x] Task 1: Update `frontend/src/routes/+layout.svelte` (AC: 1, 3, 4)
  - [x] Import and call `startPolling()` in `onMount`, `stopPolling()` in `onDestroy`
  - [x] Import `printerStatus` store and render `<StatusDot status={$printerStatus} />`
  - [x] Render `<RollGauge pct={$printerStatus.estimated_remaining_pct} />`
  - [x] Render `<Toaster />` from `svelte-sonner`
  - [x] Status bar visible at top; page content below; dark background

- [x] Task 2: Update `frontend/src/routes/+page.svelte` (AC: 2, 3)
  - [x] Import and render 6 `PrintCard` components with correct `title`, `description`, `href`
  - [x] Use 2-column grid layout — fits 375px without horizontal scrolling

- [x] Task 3: Verify build and test (AC: all)
  - [x] Run `cd frontend && npm run build` — clean, no errors
  - [x] Run `cd frontend && npm run test` — 12/12 passing

## Dev Notes

### Files Being Modified (read before touching)

**Current `+layout.svelte`** (minimal shell):
```svelte
<script lang="ts">
  import '../app.css';
  import type { Snippet } from 'svelte';
  let { children }: { children: Snippet } = $props();
</script>
{@render children()}
```

**Current `+page.svelte`** (placeholder):
```svelte
<script lang="ts">
</script>
<main class="p-4">
  <h1 class="text-2xl font-bold">PrintServer</h1>
</main>
```

Replace both entirely — they are intentional placeholders from Story 1.2.

### Correct Route Paths for All 6 Cards

From `architecture.md` — route folders use `kebab-case`:

| Card Title | Description | `href` |
|---|---|---|
| Free Text | Print any text | `/free-text` |
| QR Code | Print a QR code | `/qr-code` |
| Todo | Print a to-do list | `/todo` |
| Receipt | Print a fake receipt | `/receipt` |
| Goatse | Print goatse | `/goatse` |
| Admin | Manage till roll | `/admin` |

These route folders do not exist yet (Stories 3.5–3.8 create them). The `<a href>` links are fine — SvelteKit will return a 404 for unbuilt routes in dev, which is expected.

### Layout Structure

The layout wraps every page. It must:
1. Show a persistent status bar at the top (StatusDot + RollGauge)
2. Render page content (`{@render children()}`) below
3. Render `<Toaster />` once at root level (renders toasts globally)

```svelte
<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import type { Snippet } from 'svelte'
  import { Toaster } from 'svelte-sonner'
  import '../app.css'
  import { startPolling, stopPolling } from '$lib/polling'
  import { printerStatus } from '$lib/stores'
  import StatusDot from '$lib/components/StatusDot.svelte'
  import RollGauge from '$lib/components/RollGauge.svelte'

  let { children }: { children: Snippet } = $props()

  onMount(() => startPolling())
  onDestroy(() => stopPolling())
</script>

<!-- status bar -->
<header ...>
  <StatusDot status={$printerStatus} />
  <RollGauge pct={$printerStatus.estimated_remaining_pct} />
</header>

<!-- page content -->
{@render children()}

<!-- toast container -->
<Toaster />
```

### RollGauge Sizing in Status Bar

`RollGauge` renders an SVG with `viewBox="0 0 100 60"`. Give it a fixed container so it doesn't stretch:
```svelte
<div class="w-14 h-8">
  <RollGauge pct={$printerStatus.estimated_remaining_pct} />
</div>
```

### Home Screen — 2-Column Grid

At 375px viewport, a `grid-cols-2` grid with `gap-3` fits comfortably. Each `PrintCard` is a block `<a>` element with natural height from its padding + text content.

### `svelte-sonner` Import

```svelte
import { Toaster } from 'svelte-sonner'
```

Place `<Toaster />` at the end of the layout, outside the main content area. The `Toaster` component positions itself fixed/absolute — placement in DOM doesn't matter visually.

### Svelte 5 Lifecycle

`onMount` and `onDestroy` work normally in Svelte 5. They are imported from `'svelte'` (not changed in v5).

### Store Reactive Syntax

The `$printerStatus` reactive shorthand (Svelte store auto-subscription) still works in Svelte 5 template syntax. Use `$printerStatus` directly in the template.

### AC4 — Offline Update Within 6 Seconds

This is guaranteed by the polling interval (5s). No additional implementation needed — it's a property of `polling.ts` already built. The test is: if the Pi goes offline, within 5s the poll fails, `printerStatus` is set to OFFLINE, and `StatusDot` re-renders grey.

### Architecture Rules

- Import paths: `$lib/polling`, `$lib/stores`, `$lib/components/StatusDot.svelte` etc. (SvelteKit `$lib` alias)
- Do NOT call `getStatus()` directly in the layout — always through `startPolling()` from `polling.ts`
- Store mutations only via `.set()` — never `$printerStatus.printer_online = false` in template

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 3.4 ACs]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Frontend layout, polling data flow]
- [Source: `frontend/src/lib/polling.ts` — startPolling / stopPolling]
- [Source: `frontend/src/lib/stores.ts` — printerStatus store]
- [Source: `frontend/src/lib/components/` — StatusDot, RollGauge, PrintCard]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — compiled and tested cleanly first attempt.

### Completion Notes List

- AC1 ✅: `+layout.svelte` — `onMount(startPolling)` / `onDestroy(stopPolling)`; `<StatusDot status={$printerStatus} />`; `<RollGauge pct={$printerStatus.estimated_remaining_pct} />`; `<Toaster />` from svelte-sonner; dark `bg-bg` wrapper
- AC2 ✅: `+page.svelte` — 6 `PrintCard` components with correct hrefs: `/free-text`, `/qr-code`, `/todo`, `/receipt`, `/goatse`, `/admin`
- AC3 ✅: `grid-cols-2 gap-3` layout; status bar in `<header>` at top; full-width `min-h-screen bg-bg`
- AC4 ✅: Guaranteed by 5s poll interval in `polling.ts` — offline state propagates within one poll cycle (≤5s < 6s)
- Build: CSS bundle grew to 20.47 KB (svelte-sonner Toaster included); 157→169 modules; clean
- Tests: 12/12 passing (api.test.ts unaffected)

### File List

- `frontend/src/routes/+layout.svelte` — MODIFIED
- `frontend/src/routes/+page.svelte` — MODIFIED
