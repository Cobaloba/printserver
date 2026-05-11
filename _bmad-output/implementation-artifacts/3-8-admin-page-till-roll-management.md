# Story 3.8: Admin Page — Till Roll Management

Status: ready-for-dev

## Story

As a developer,
I want the admin page to display current roll state and let users log a new roll,
So that till roll tracking can be reset and monitored without SSH.

## Acceptance Criteria

1. **Given** `frontend/src/routes/admin/+page.svelte` **When** loaded **Then** `GET /api/v1/admin/roll` is called and the response populates current `bytes_printed`, `estimated_remaining_pct`, and `last_reset`; the New Roll form pre-fills `width_mm` and `diameter_mm` from the retrieved values

2. **Given** the user changes `diameter_mm` to 35 and taps Save **When** `api.postAdminRoll({width_mm: 57, diameter_mm: 35})` succeeds **Then** `toast.success('Roll updated')` fires and the displayed roll state refreshes

3. **Given** the Save button is tapped and the API returns an error **When** the error is caught **Then** `toast.error(detail)` fires and the form values remain unchanged

4. **Given** the Admin card on the home screen **When** tapped **Then** navigation to `/admin` occurs (already handled by PrintCard `href="/admin"`)

## Tasks / Subtasks

- [ ] Task 1: Create `frontend/src/routes/admin/+page.svelte` (AC: 1, 2, 3)
  - [ ] `onMount` calls `getAdminRoll()` and populates display + form inputs
  - [ ] Display `bytes_printed`, `estimated_remaining_pct`, `last_reset`
  - [ ] Form inputs for `width_mm` and `diameter_mm` pre-filled from API
  - [ ] Save calls `postAdminRoll(width_mm, diameter_mm)` → refreshes state on success
  - [ ] `toast.success('Roll updated')` on success; `toast.error(message)` on failure
  - [ ] On error: form values unchanged (don't overwrite inputs with pre-error values)

- [ ] Task 2: Verify build and tests
  - [ ] `cd frontend && npm run build` — clean
  - [ ] `cd frontend && npm run test` — 12/12 passing

## Dev Notes

### `getAdminRoll` / `postAdminRoll` signatures

```typescript
getAdminRoll(): Promise<RollState>
postAdminRoll(width_mm: number, diameter_mm: number): Promise<void>

interface RollState {
  bytes_printed: number
  roll_width_mm: number
  roll_diameter_mm: number
  last_reset: string       // ISO 8601 string
  estimated_remaining_pct: number
}
```

### State Pattern

Use local state — not the `rollState` store — since this is a self-contained admin page:

```typescript
let roll: RollState | null = $state(null)
let width_mm = $state(57)
let diameter_mm = $state(40)
let saving = $state(false)

onMount(async () => {
  try {
    roll = await getAdminRoll()
    width_mm = roll.roll_width_mm
    diameter_mm = roll.roll_diameter_mm
  } catch (e) {
    toast.error('Failed to load roll state')
  }
})
```

### Refresh After Save

After successful `postAdminRoll`, call `getAdminRoll()` again to refresh the displayed state. Do NOT update `roll` optimistically — fetch fresh from the server:

```typescript
async function handleSave() {
  saving = true
  try {
    await postAdminRoll(width_mm, diameter_mm)
    roll = await getAdminRoll()          // refresh display
    toast.success('Roll updated')
  } catch (e) {
    toast.error(e instanceof Error ? e.message : 'Save failed')
    // width_mm and diameter_mm unchanged — form retains user's values
  } finally {
    saving = false
  }
}
```

### Displaying `last_reset`

Format the ISO string for readability:
```typescript
new Date(roll.last_reset).toLocaleString()
```

### `bytes_printed` Display

Show in a human-readable unit. Raw bytes is not meaningful to users — convert to KB:
```typescript
(roll.bytes_printed / 1024).toFixed(1) + ' KB'
```
Or just show the raw number with a "bytes" label — keep it simple.

### AC4 Already Done

The Admin card on the home screen already has `href="/admin"` from Story 3.4. No work needed here.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 3.8 ACs]
- [Source: `frontend/src/lib/api.ts` — `getAdminRoll`, `postAdminRoll`]
- [Source: `frontend/src/lib/types.ts` — `RollState`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
