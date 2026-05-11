# Story 3.3: Shared Components

Status: review

## Story

As a developer,
I want the four shared UI components built and visually verified,
So that every print page and the layout can use them without duplicating code.

## Acceptance Criteria

1. **Given** `StatusDot.svelte` accepting `status: PrinterStatus` **When** `printer_online=true`, `printer_online=false`, and `paper_near_end=true` are each rendered **Then** a pulsing green dot, flat grey dot, and amber dot are shown respectively; each has a minimum 8×8px visible size

2. **Given** `RollGauge.svelte` accepting `pct: number` (0–100) **When** rendered at 0%, 50%, and 100% **Then** the SVG arc fills proportionally; when `pct < 15`, the arc renders in a warning colour (red or amber)

3. **Given** `PrintButton.svelte` accepting `loading: boolean` **When** `loading=true` **Then** a spinner is shown and the button is `disabled`; when `loading=false`, the button shows its slot content and is interactive

4. **Given** `PrintCard.svelte` accepting `title`, `description`, and `href` **When** rendered and tapped **Then** navigation to `href` occurs; the card has a minimum bounding box of 44×44px

## Tasks / Subtasks

- [x] Task 1: Create `frontend/src/lib/components/StatusDot.svelte` (AC: 1)
  - [x] Accept `status: PrinterStatus` prop
  - [x] Pulsing green (`animate-pulse`) when `printer_online=true` and `paper_near_end=false`
  - [x] Flat amber when `paper_near_end=true` (takes precedence over green)
  - [x] Flat grey when `printer_online=false`
  - [x] Minimum visible size 8×8px (`w-3 h-3` = 12×12px)

- [x] Task 2: Create `frontend/src/lib/components/RollGauge.svelte` (AC: 2)
  - [x] Accept `pct: number` (0–100) prop
  - [x] Render a semicircular SVG arc gauge (top half of circle)
  - [x] Fill arc proportional to `pct`; empty arc shows grey background
  - [x] Warning colour (red `#ef4444`) when `pct < 15`; accent green otherwise
  - [x] Arc does not render fill when `pct === 0`

- [x] Task 3: Create `frontend/src/lib/components/PrintButton.svelte` (AC: 3)
  - [x] Accept `loading: boolean` and optional `onclick` prop
  - [x] When `loading=true`: show spinner, set `disabled`, prevent clicks
  - [x] When `loading=false`: render `children` snippet content
  - [x] Full-width (`w-full`), minimum height 44px

- [x] Task 4: Create `frontend/src/lib/components/PrintCard.svelte` (AC: 4)
  - [x] Accept `title: string`, `description: string`, `href: string` props
  - [x] Render as `<a href={href}>` for SvelteKit navigation
  - [x] Card surface styling (`bg-surface`)
  - [x] Minimum bounding box 44×44px (padding + min-height)

- [x] Task 5: Verify build passes (AC: all)
  - [x] Run `cd frontend && npm run build` — must complete without TypeScript errors
  - [x] Confirm all 4 component files exist in `frontend/src/lib/components/`

## Dev Notes

### Svelte 5 Syntax — MANDATORY

The project uses **Svelte 5 runes mode**. The existing `+layout.svelte` confirms the patterns:
```svelte
<script lang="ts">
  import type { Snippet } from 'svelte'
  let { children }: { children: Snippet } = $props()
</script>
{@render children()}
```

**All components MUST use:**
- `let { foo, bar } = $props()` instead of `export let foo`
- `let x = $derived(expr)` instead of `$: x = expr`
- `{@render children()}` instead of `<slot />`
- `import type { Snippet } from 'svelte'` for snippet typing
- `onclick` prop (not `on:click` directive — that's Svelte 4)

### Tailwind v4 Color Tokens

From `frontend/src/app.css`:
```css
@theme {
  --color-bg: #0f0f0f;
  --color-surface: #1a1a1a;
  --color-accent: #22c55e;
}
```

In Tailwind v4, `--color-*` tokens map directly to utilities:
- `bg-bg` → `#0f0f0f`
- `bg-surface` → `#1a1a1a`
- `bg-accent` → `#22c55e`
- `text-accent` → `#22c55e`

Use these tokens in components. Do NOT hardcode hex values in class attributes.

### StatusDot — Implementation Detail

Priority order: `paper_near_end` > `printer_online`. A printer can be online but running out of paper.

```svelte
let dotClass = $derived(
  !status.printer_online
    ? 'bg-gray-500'
    : status.paper_near_end
      ? 'bg-amber-500'
      : 'bg-accent animate-pulse'
)
```

`w-3 h-3` = 12×12px in Tailwind (3 × 4px = 12px) — satisfies 8×8px minimum. Use `rounded-full` for dot shape.

### RollGauge — SVG Arc Calculation

Use a semicircle arc (180°) with SVG path commands. ViewBox `"0 0 100 60"`, center `(50, 55)`, radius `45`.

**Key coordinates:**
- Left point (0%): `(5, 55)` = `cx - r, cy`
- Right point (100%): `(95, 55)` = `cx + r, cy`
- Top point (50%): `(50, 10)` = `cx, cy - r`

**Arc formula:**
- `endAngle = 180 + pct * 1.8` (degrees)
- `endX = cx + r * cos(endAngle * π/180)`
- `endY = cy + r * sin(endAngle * π/180)`

**SVG paths:**
```
Background: M 5 55 A 45 45 0 0 1 95 55   (sweep=1, clockwise through top)
Fill:       M 5 55 A 45 45 0 0 1 {endX} {endY}
```

`sweep-flag=1` = clockwise on screen. From left `(5,55)` clockwise through top `(50,10)` to right `(95,55)`.

**Warning colour:** `pct < 15` → `'#ef4444'` (red-500); otherwise `'#22c55e'` (accent green). Use inline `stroke` attribute (not Tailwind class) since SVG stroke can't use Tailwind utility classes.

**Hide fill at pct=0:** `{#if pct > 0}` around fill path — avoids degenerate zero-length arc.

### PrintButton — Slot via Svelte 5 Snippet

```svelte
<script lang="ts">
  import type { Snippet } from 'svelte'
  interface Props {
    loading?: boolean
    children: Snippet
    onclick?: () => void | Promise<void>
  }
  let { loading = false, children, onclick }: Props = $props()
</script>

<button class="w-full py-3 px-4 rounded-lg bg-accent text-black font-semibold
               disabled:opacity-50 min-h-[44px] flex items-center justify-center"
  disabled={loading}
  {onclick}>
  {#if loading}
    <span class="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin"></span>
  {:else}
    {@render children()}
  {/if}
</button>
```

Callers use it as:
```svelte
<PrintButton {loading} onclick={handlePrint}>Print</PrintButton>
```
This pattern is used in Stories 3.5–3.8.

### PrintCard — Navigation via `<a>` tag

SvelteKit handles client-side navigation automatically for `<a href>` links. Do NOT use `goto()` or any programmatic navigation.

```svelte
<a href={href} class="block p-4 rounded-xl bg-surface min-h-[44px] ...">
  <h2 class="font-semibold text-white">{title}</h2>
  <p class="text-sm text-gray-400 mt-1">{description}</p>
</a>
```

The `<a>` element naturally has at least 44px height from the padding + text, satisfying the touch target requirement.

### File Locations (exact)

```
frontend/src/lib/components/
├── StatusDot.svelte
├── RollGauge.svelte
├── PrintButton.svelte
└── PrintCard.svelte
```

Architecture rule: component filenames are `PascalCase.svelte`. The `components/` directory does not yet exist — create it.

### No Vitest Component Tests Required

Story 3.3 ACs are rendering/visual ACs (pulsing dot, arc fill, spinner). `@testing-library/svelte` is not installed. Verification is via `npm run build` (TypeScript correctness) and visual inspection. Do NOT attempt to install testing libraries for this story.

### Import Paths in Components

Use `$lib/types` alias (SvelteKit auto-configured):
```typescript
import type { PrinterStatus } from '$lib/types'
```
Do NOT use relative paths like `'../types'` or `'../../types'`.

### Architecture Rules (all Epic 3 stories)

- Components: `PascalCase.svelte` in `src/lib/components/`
- Never fetch API in components — always via `api.ts`
- Touch targets: minimum 44×44px for interactive elements
- Dark mode: use `bg-surface`, `bg-bg` Tailwind tokens; avoid hardcoded colours in class attributes

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 3.3 ACs]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Frontend Components section]
- [Source: `frontend/src/routes/+layout.svelte` — Svelte 5 runes syntax pattern confirmed]
- [Source: `frontend/src/app.css` — @theme color tokens]
- [Source: `frontend/src/lib/types.ts` — PrinterStatus interface]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — all 4 components compiled first attempt; build clean.

### Completion Notes List

- AC1 ✅: `StatusDot.svelte` — 12×12px dot; `paper_near_end` priority over `printer_online`; `animate-pulse` on green; `role="status"` + `aria-label` for accessibility
- AC2 ✅: `RollGauge.svelte` — SVG semicircle arc, viewBox 0 0 100 60; clockwise from left (5,55) through top to proportional endpoint; `#ef4444` when pct<15; fill hidden at pct=0
- AC3 ✅: `PrintButton.svelte` — `w-full min-h-[44px]`; spinner with `animate-spin` + `disabled` when loading; `{@render children()}` when not loading; Svelte 5 snippet API
- AC4 ✅: `PrintCard.svelte` — `<a href>` for native SvelteKit navigation; `bg-surface` token; `min-h-[44px]` touch target; hover opacity transition
- Build: CSS bundle 4.67 KB → 7.04 KB (component styles included); 844ms clean build

### File List

- `frontend/src/lib/components/StatusDot.svelte` — NEW
- `frontend/src/lib/components/RollGauge.svelte` — NEW
- `frontend/src/lib/components/PrintButton.svelte` — NEW
- `frontend/src/lib/components/PrintCard.svelte` — NEW
