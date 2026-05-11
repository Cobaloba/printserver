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

<main class="p-4 flex flex-col gap-4">
  <h1 class="text-xl font-bold">Todo List</h1>

  <div class="flex flex-col gap-2">
    <label class="text-sm text-gray-400" for="title">Title</label>
    <input
      id="title"
      bind:value={title}
      class="w-full rounded-lg bg-surface px-3 py-2 text-white min-h-[44px]"
      placeholder="TO DO"
    />
  </div>

  <div class="flex gap-2">
    <input
      bind:value={newItem}
      onkeydown={(e) => e.key === 'Enter' && addItem()}
      class="flex-1 rounded-lg bg-surface px-3 py-2 text-white min-h-[44px]"
      placeholder="Add an item…"
    />
    <button
      onclick={addItem}
      class="rounded-lg bg-surface px-4 font-semibold text-white min-h-[44px] min-w-[44px] hover:opacity-80"
    >
      Add
    </button>
  </div>

  {#if items.length > 0}
    <ul class="flex flex-col gap-2">
      {#each items as item, i}
        <li class="flex items-center justify-between rounded-lg bg-surface px-3 py-2 min-h-[44px]">
          <span class="text-white">{item}</span>
          <button
            onclick={() => removeItem(i)}
            class="ml-2 text-gray-400 hover:text-white min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Remove {item}"
          >
            ✕
          </button>
        </li>
      {/each}
    </ul>
  {/if}

  <PrintButton {loading} onclick={handlePrint}>Print</PrintButton>
</main>
