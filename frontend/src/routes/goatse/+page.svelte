<script lang="ts">
  import { toast } from 'svelte-sonner'
  import { printGoatse } from '$lib/api'
  import PrintButton from '$lib/components/PrintButton.svelte'

  let loading = $state(false)

  async function handlePrint() {
    loading = true
    try {
      await printGoatse()
      toast.success('Sent to printer ✓')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Print failed')
    } finally {
      loading = false
    }
  }
</script>

<main class="p-4 flex flex-col gap-4">
  <h1 class="text-xl font-bold">Goatse</h1>
  <PrintButton {loading} onclick={handlePrint}>Print</PrintButton>
</main>
