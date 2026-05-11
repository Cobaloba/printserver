<script lang="ts">
  import { toast } from 'svelte-sonner'
  import { printReceipt } from '$lib/api'
  import PrintButton from '$lib/components/PrintButton.svelte'

  let store = $state('')
  let address = $state('')
  let phone = $state('')
  let tax_pct = $state(0)
  let newName = $state('')
  let newPrice = $state('')
  let items: Array<{ name: string; price: number }> = $state([])
  let loading = $state(false)

  let subtotal = $derived(items.reduce((sum, item) => sum + item.price, 0))
  let taxAmount = $derived(subtotal * tax_pct / 100)
  let total = $derived(subtotal + taxAmount)

  function addRow() {
    const name = newName.trim()
    const price = parseFloat(newPrice)
    if (!name || isNaN(price) || price <= 0) return
    items = [...items, { name, price }]
    newName = ''
    newPrice = ''
  }

  function removeRow(i: number) {
    items = items.filter((_, idx) => idx !== i)
  }

  async function handlePrint() {
    if (items.length === 0) {
      toast.error('Add at least one item')
      return
    }
    loading = true
    try {
      await printReceipt({
        store,
        items,
        address: address.trim() || null,
        phone: phone.trim() || null,
        tax_pct
      })
      toast.success('Sent to printer ✓')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Print failed')
    } finally {
      loading = false
    }
  }
</script>

<main class="p-4 flex flex-col gap-4">
  <h1 class="text-xl font-bold">Receipt</h1>

  <div class="flex flex-col gap-3">
    <div class="flex flex-col gap-1">
      <label class="text-sm text-gray-400" for="store">Store name</label>
      <input
        id="store"
        bind:value={store}
        class="w-full rounded-lg bg-surface px-3 py-2 text-white min-h-[44px]"
        placeholder="Store name"
      />
    </div>

    <div class="flex flex-col gap-1">
      <label class="text-sm text-gray-400" for="address">Address (optional)</label>
      <input
        id="address"
        bind:value={address}
        class="w-full rounded-lg bg-surface px-3 py-2 text-white min-h-[44px]"
        placeholder="123 High Street"
      />
    </div>

    <div class="flex flex-col gap-1">
      <label class="text-sm text-gray-400" for="phone">Phone (optional)</label>
      <input
        id="phone"
        bind:value={phone}
        class="w-full rounded-lg bg-surface px-3 py-2 text-white min-h-[44px]"
        placeholder="01234 567890"
      />
    </div>
  </div>

  <div class="flex flex-col gap-2">
    <span class="text-sm text-gray-400">Items</span>
    <div class="flex gap-2">
      <input
        bind:value={newName}
        onkeydown={(e) => e.key === 'Enter' && addRow()}
        class="flex-1 rounded-lg bg-surface px-3 py-2 text-white min-h-[44px]"
        placeholder="Item name"
      />
      <input
        bind:value={newPrice}
        onkeydown={(e) => e.key === 'Enter' && addRow()}
        type="number"
        min="0"
        step="0.01"
        class="w-24 rounded-lg bg-surface px-3 py-2 text-white min-h-[44px]"
        placeholder="0.00"
      />
      <button
        onclick={addRow}
        class="rounded-lg bg-surface px-4 font-semibold text-white min-h-[44px] min-w-[44px] hover:opacity-80"
      >
        Add
      </button>
    </div>

    {#if items.length > 0}
      <ul class="flex flex-col gap-1">
        {#each items as item, i}
          <li class="flex items-center justify-between rounded-lg bg-surface px-3 py-2 min-h-[44px]">
            <span class="text-white">{item.name}</span>
            <div class="flex items-center gap-3">
              <span class="text-gray-300">£{item.price.toFixed(2)}</span>
              <button
                onclick={() => removeRow(i)}
                class="text-gray-400 hover:text-white min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="Remove {item.name}"
              >
                ✕
              </button>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </div>

  <div class="flex flex-col gap-1">
    <label class="text-sm text-gray-400" for="tax">Tax %</label>
    <input
      id="tax"
      bind:value={tax_pct}
      type="number"
      min="0"
      step="1"
      class="w-full rounded-lg bg-surface px-3 py-2 text-white min-h-[44px]"
      placeholder="0"
    />
  </div>

  {#if items.length > 0}
    <div class="rounded-lg bg-surface px-4 py-3 flex flex-col gap-1 text-sm">
      <div class="flex justify-between text-gray-400">
        <span>Subtotal</span><span>£{subtotal.toFixed(2)}</span>
      </div>
      {#if tax_pct > 0}
        <div class="flex justify-between text-gray-400">
          <span>Tax ({tax_pct}%)</span><span>£{taxAmount.toFixed(2)}</span>
        </div>
      {/if}
      <div class="flex justify-between font-semibold text-white border-t border-gray-700 pt-1 mt-1">
        <span>Total</span><span>£{total.toFixed(2)}</span>
      </div>
    </div>
  {/if}

  <PrintButton {loading} onclick={handlePrint}>Print</PrintButton>
</main>
