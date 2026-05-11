<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import type { Snippet } from 'svelte'
  import { Toaster } from 'svelte-sonner'
  import { page } from '$app/stores'
  import '../app.css'
  import { startPolling, stopPolling } from '$lib/polling'
  import { printerStatus } from '$lib/stores'
  import StatusDot from '$lib/components/StatusDot.svelte'
  import RollGauge from '$lib/components/RollGauge.svelte'

  let { children }: { children: Snippet } = $props()
  let isHome = $derived($page.url.pathname === '/')

  onMount(() => startPolling())
  onDestroy(() => stopPolling())
</script>

<div class="min-h-screen bg-bg text-white">
  <header class="flex items-center justify-between px-4 py-3 bg-surface border-b border-gray-800">
    <div class="flex items-center gap-2">
      {#if !isHome}
        <a href="/" class="flex items-center justify-center w-8 h-8 text-gray-400 hover:text-white -ml-1" aria-label="Back to home">
          ←
        </a>
      {/if}
      <StatusDot status={$printerStatus} />
      <span class="text-sm text-gray-400">
        {$printerStatus.printer_online ? 'Online' : 'Offline'}
      </span>
    </div>
    <div class="w-14 h-8">
      <RollGauge pct={$printerStatus.estimated_remaining_pct} />
    </div>
  </header>

  {@render children()}
</div>

<Toaster />
