# Story 3.6: Receipt Print Page

Status: review

## Story

As a developer,
I want the fake receipt print UI with its mini-ledger builder implemented,
So that users can construct a receipt line by line and print it.

## Acceptance Criteria

1. **Given** `frontend/src/routes/receipt/+page.svelte` **When** rendered **Then** it shows: store name input; optional address and phone inputs; a row builder (item name + price, "Add row" button); a live-updating running total; a tax percentage input; and a `<PrintButton>`

2. **Given** 2 items added (Coffee £2.50, Cake £3.00) with 20% tax **When** the totals area is inspected before printing **Then** subtotal shows £5.50, tax shows £1.10, and total shows £6.60, all updating reactively

3. **Given** no items added **When** Print is tapped **Then** the button is disabled or a client-side validation message appears — no API call is made

4. **Given** a completed receipt form **When** Print is tapped and succeeds **Then** `api.printReceipt({store, address, phone, items, tax_pct})` is called with `snake_case` field names and the success toast fires

## Tasks / Subtasks

- [x] Task 1: Create `frontend/src/routes/receipt/+page.svelte` (AC: 1, 2, 3, 4)
  - [x] Store name input, optional address + phone inputs
  - [x] Row builder: item name + price inputs, "Add row" button, list with remove per row
  - [x] Reactive subtotal, tax, total derived from items + tax_pct
  - [x] PrintButton disabled when `items.length === 0`
  - [x] `printReceipt({store, address: address||null, phone: phone||null, items, tax_pct})` on print
  - [x] `loading` in `finally`; `toast.success` / `toast.error`

- [x] Task 2: Verify build and tests (AC: all)
  - [x] `cd frontend && npm run build` — clean
  - [x] `cd frontend && npm run test` — 12/12 passing

## Dev Notes

### `printReceipt` Signature (from `api.ts`)

```typescript
printReceipt(params: ReceiptParams): Promise<void>

interface ReceiptParams {
  store: string
  items: Array<{ name: string; price: number }>
  address: string | null
  phone: string | null
  tax_pct: number
}
```

Pass `address || null` and `phone || null` — empty string must become `null`, not `""`.

### Reactive Totals with `$derived`

```typescript
let subtotal = $derived(items.reduce((sum, item) => sum + item.price, 0))
let taxAmount = $derived(subtotal * tax_pct / 100)
let total = $derived(subtotal + taxAmount)
```

Display with `toFixed(2)` for 2 decimal places: `£${subtotal.toFixed(2)}`

### State Shape

```typescript
let store = $state('')
let address = $state('')
let phone = $state('')
let tax_pct = $state(0)
let newName = $state('')
let newPrice = $state('')           // string for input binding, parse on add
let items: Array<{ name: string; price: number }> = $state([])
let loading = $state(false)
```

Price input: bind as string (`newPrice`), parse with `parseFloat` on "Add row". Skip if NaN or ≤ 0.

### Disable Print When No Items

```svelte
<PrintButton loading={loading} onclick={handlePrint} disabled={items.length === 0}>
  Print
</PrintButton>
```

Wait — `PrintButton` in Story 3.3 only accepts `loading` and `onclick`. Add `disabled` prop support OR simply don't call the API if items is empty. Cleanest: check in `handlePrint` and show a toast instead:

```typescript
async function handlePrint() {
  if (items.length === 0) {
    toast.error('Add at least one item')
    return
  }
  loading = true
  try { ... } finally { loading = false }
}
```

This satisfies AC3 without needing to modify `PrintButton`.

### Tax Input

`<input type="number" min="0" bind:value={tax_pct} />` — tax_pct is a number, Svelte handles `bind:value` with number inputs correctly when the variable is typed as `number`.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 3.6 ACs]
- [Source: `frontend/src/lib/api.ts` — `printReceipt`, `ReceiptParams`]
- [Source: `backend/app/models/print_models.py` — `ReceiptRequest`, `ReceiptItem`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — clean first attempt.

### Completion Notes List

- AC1 ✅: Store/address/phone inputs; item row builder with name+price+add; remove per row; tax % input; totals panel; PrintButton
- AC2 ✅: `$derived` subtotal/taxAmount/total update reactively; displayed with `toFixed(2)`
- AC3 ✅: `handlePrint` guards `items.length === 0` → `toast.error('Add at least one item')` and returns before API call
- AC4 ✅: `printReceipt({store, items, address: address.trim()||null, phone: phone.trim()||null, tax_pct})` — empty strings become null
- Enter key on name/price inputs triggers `addRow()` for faster mobile entry

### File List

- `frontend/src/routes/receipt/+page.svelte` — NEW
