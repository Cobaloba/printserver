<script lang="ts">
  import QRCode from 'qrcode'
  import { toast } from 'svelte-sonner'
  import { printQr } from '$lib/api'
  import PrintButton from '$lib/components/PrintButton.svelte'

  let url = $state('')
  let qrDataUrl = $state('')
  let urlError = $state('')
  let loading = $state(false)

  function isValidUrl(s: string): boolean {
    if (!s) return false
    try { new URL(s); return true } catch { return false }
  }

  $effect(() => {
    const trimmed = url.trim()
    if (isValidUrl(trimmed)) {
      QRCode.toDataURL(trimmed, { width: 200, margin: 1 })
        .then(data => { qrDataUrl = data })
        .catch(() => { qrDataUrl = '' })
    } else {
      qrDataUrl = ''
    }
  })

  async function handlePrint() {
    const trimmed = url.trim()
    if (!isValidUrl(trimmed)) {
      urlError = 'Enter a valid URL (e.g. https://example.com)'
      return
    }
    urlError = ''
    loading = true
    try {
      await printQr(trimmed)
      toast.success('Sent to printer ✓')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Print failed')
    } finally {
      loading = false
    }
  }
</script>

<main class="p-4 flex flex-col gap-4">
  <h1 class="text-xl font-bold">QR Code</h1>

  <div class="flex flex-col gap-1">
    <label class="text-sm text-gray-400" for="url">URL</label>
    <input
      id="url"
      bind:value={url}
      class="w-full rounded-lg bg-surface px-3 py-2 text-white min-h-[44px]"
      placeholder="https://example.com"
      type="url"
      autocapitalize="none"
    />
    {#if urlError}
      <p class="text-sm text-red-400">{urlError}</p>
    {/if}
  </div>

  {#if qrDataUrl}
    <div class="flex justify-center">
      <img src={qrDataUrl} alt="QR code preview" class="rounded-lg" width="200" height="200" />
    </div>
  {/if}

  <PrintButton {loading} onclick={handlePrint}>Print</PrintButton>
</main>
