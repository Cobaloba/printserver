<script lang="ts">
  import type { PrinterStatus } from '$lib/types'

  let { status }: { status: PrinterStatus } = $props()

  let dotClass = $derived(
    !status.printer_online
      ? 'bg-gray-500'
      : status.paper_near_end
        ? 'bg-amber-500'
        : 'bg-accent animate-pulse'
  )

  let label = $derived(
    !status.printer_online
      ? 'Printer offline'
      : status.paper_near_end
        ? 'Paper near end'
        : 'Printer online'
  )
</script>

<span
  class="inline-block w-3 h-3 rounded-full {dotClass}"
  role="status"
  aria-label={label}
></span>
