<script lang="ts">
  import { toast } from 'svelte-sonner'
  import { printFreeText } from '$lib/api'
  import PrintButton from '$lib/components/PrintButton.svelte'
  import type { FontSize } from '$lib/types'

  let text = $state('')
  let font_size: FontSize = $state('medium')
  let loading = $state(false)

  async function handlePrint() {
    loading = true
    try {
      await printFreeText(text, font_size)
      toast.success('Sent to printer ✓')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Print failed')
    } finally {
      loading = false
    }
  }
</script>

<main class="p-4 flex flex-col gap-4">
  <h1 class="text-xl font-bold">Free Text</h1>

  <div class="flex flex-col gap-2">
    <label class="text-sm text-gray-400" for="text">Text</label>
    <textarea
      id="text"
      bind:value={text}
      class="w-full rounded-lg bg-surface px-3 py-2 text-white resize-none"
      rows="6"
      placeholder="Type anything…"
    ></textarea>
  </div>

  <div class="flex flex-col gap-2">
    <label class="text-sm text-gray-400" for="font-size">Font size</label>
    <select
      id="font-size"
      bind:value={font_size}
      class="w-full rounded-lg bg-surface px-3 py-2 text-white min-h-[44px]"
    >
      <option value="small">Small</option>
      <option value="medium">Medium</option>
      <option value="large">Large</option>
    </select>
  </div>

  <PrintButton {loading} onclick={handlePrint}>Print</PrintButton>
</main>
