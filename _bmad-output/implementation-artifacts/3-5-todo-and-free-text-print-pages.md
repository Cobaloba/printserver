# Story 3.5: Todo and Free Text Print Pages

Status: review

## Story

As a developer,
I want the todo list and free text print UIs implemented end-to-end,
So that users can make their first successful phone-to-paper prints.

## Acceptance Criteria

1. **Given** `frontend/src/routes/todo/+page.svelte` **When** rendered **Then** it shows a text input for title, "Add item" button, a list of added items (each with a remove button), and a full-width `<PrintButton>`

2. **Given** 2 items added and Print tapped **When** `api.printTodo(title, items)` succeeds **Then** `toast.success('Sent to printer ✓')` fires; `loading` resets to `false` in a `finally` block

3. **Given** Print tapped when the printer is offline (API returns 503) **When** the error is caught **Then** `toast.error('Printer offline')` (or the returned `detail`) fires within 3 seconds

4. **Given** `frontend/src/routes/free-text/+page.svelte` **When** rendered **Then** it shows a `<textarea>`, a font size selector with options Small / Medium / Large, and a `<PrintButton>`; on print success/failure, the appropriate toast fires

## Tasks / Subtasks

- [x] Task 1: Create `frontend/src/routes/todo/+page.svelte` (AC: 1, 2, 3)
  - [x] Title text input (default value "TO DO")
  - [x] Item text input + "Add item" button (adds to list on click or Enter)
  - [x] Rendered list of items, each with a remove button
  - [x] `<PrintButton {loading}>Print</PrintButton>` — calls `printTodo(title, items)` on click
  - [x] `loading` reset in `finally`; `toast.success` / `toast.error` on outcome

- [x] Task 2: Create `frontend/src/routes/free-text/+page.svelte` (AC: 4)
  - [x] `<textarea>` for free text input
  - [x] Font size selector: Small / Medium / Large (maps to `'small'|'medium'|'large'`)
  - [x] `<PrintButton {loading}>Print</PrintButton>` — calls `printFreeText(text, font_size)`
  - [x] `loading` reset in `finally`; `toast.success` / `toast.error` on outcome

- [x] Task 3: Verify build (AC: all)
  - [x] Run `cd frontend && npm run build` — clean, no errors
  - [x] Run `cd frontend && npm run test` — 12/12 passing

## Dev Notes

### Route Folder Names (architecture rule: kebab-case)

- `frontend/src/routes/todo/+page.svelte` — new directory
- `frontend/src/routes/free-text/+page.svelte` — new directory (matches `/free-text` href in PrintCard)

### Svelte 5 Pattern for These Pages

Use local `let` variables — NOT stores — for all form state:

```svelte
<script lang="ts">
  import { toast } from 'svelte-sonner'
  import { printTodo } from '$lib/api'
  import PrintButton from '$lib/components/PrintButton.svelte'

  let title = $state('TO DO')
  let newItem = $state('')
  let items: string[] = $state([])
  let loading = $state(false)

  function addItem() {
    const trimmed = newItem.trim()
    if (trimmed) {
      items = [...items, trimmed]
      newItem = ''
    }
  }

  function removeItem(i: number) {
    items = items.filter((_, idx) => idx !== i)
  }

  async function handlePrint() {
    loading = true
    try {
      await printTodo(title, items)
      toast.success('Sent to printer ✓')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Print failed')
    } finally {
      loading = false
    }
  }
</script>
```

**In Svelte 5 runes mode**, use `$state()` instead of `let` for reactive variables that update the DOM. Use `$state()` for `title`, `newItem`, `items`, `loading`, `text`, `font_size`.

### `toast` Import

```typescript
import { toast } from 'svelte-sonner'
```

`toast.success(message)` and `toast.error(message)` — the `<Toaster />` in `+layout.svelte` renders them.

### `printTodo` Default Title

The backend model has `title: str = "TO DO"` — initialise the title input to `"TO DO"` so the default matches.

### Adding Items on Enter Key

Handle `onkeydown` on the item input to call `addItem()` when Enter is pressed — better mobile UX:
```svelte
<input
  bind:value={newItem}
  onkeydown={(e) => e.key === 'Enter' && addItem()}
  ...
/>
```

### Font Size Selector

Map display labels to API values:

| Display | API value |
|---|---|
| Small | `'small'` |
| Medium | `'medium'` |
| Large | `'large'` |

Use `<select bind:value={font_size}>` or three radio/toggle buttons. Select is simplest.

### PrintButton onclick Wiring (Svelte 5)

```svelte
<PrintButton {loading} onclick={handlePrint}>Print</PrintButton>
```

`PrintButton` accepts `onclick?: () => void | Promise<void>` — defined in Story 3.3.

### Touch Target Rule

All buttons (Add, Remove, Print) must be minimum 44×44px. Use `min-h-[44px]` or sufficient padding.

### Architecture Rules

- Never call `getStatus()` directly — polling handles status
- `loading = false` always in `finally` — never in try or catch only
- Error message: `e instanceof Error ? e.message : 'Print failed'` — matches `api.ts` pattern where errors always throw `Error(detail)`

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 3.5 ACs]
- [Source: `frontend/src/lib/api.ts` — `printTodo`, `printFreeText` signatures]
- [Source: `frontend/src/lib/components/PrintButton.svelte` — `onclick` prop]
- [Source: `backend/app/models/print_models.py` — `TodoRequest`, `FreeTextRequest` field names]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — compiled cleanly first attempt.

### Completion Notes List

- AC1 ✅: Todo page has title input (default "TO DO"), item input with Enter key support, item list with per-item remove buttons, PrintButton
- AC2 ✅: `printTodo(title, items)` → `toast.success('Sent to printer ✓')`; `loading = false` in `finally`
- AC3 ✅: Caught errors use `e.message` (api.ts always throws `Error(detail)`); `toast.error(message)`
- AC4 ✅: Free text page has `<textarea>`, `<select>` with Small/Medium/Large, PrintButton with same toast pattern
- Svelte 5 `$state()` used for all reactive variables; `$derived` not needed in these pages
- Build: 24 precache entries (14→24, new routes included); 12/12 tests passing

### File List

- `frontend/src/routes/todo/+page.svelte` — NEW
- `frontend/src/routes/free-text/+page.svelte` — NEW
