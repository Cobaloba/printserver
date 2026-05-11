<script lang="ts">
  import { onMount } from 'svelte'
  import { toast } from 'svelte-sonner'
  import { getAdminRoll, postAdminRoll, restartService, getBotLog } from '$lib/api'
  import type { RollState, BotMessage, BotLogResponse } from '$lib/types'
  import PrintButton from '$lib/components/PrintButton.svelte'
  import RollGauge from '$lib/components/RollGauge.svelte'

  let roll: RollState | null = $state(null)
  let width_mm = $state(57)
  let diameter_mm = $state(40)
  let saving = $state(false)
  let restarting = $state(false)
  let botLog: BotMessage[] = $state([])
  let botPage = $state(1)
  let botTotal = $state(0)
  const PER_PAGE = 20

  let totalPages = $derived(Math.max(1, Math.ceil(botTotal / PER_PAGE)))

  async function loadBotLog(page: number) {
    try {
      const res = await getBotLog(page, PER_PAGE)
      botLog = res.messages
      botTotal = res.total
      botPage = res.page
    } catch {
      // bot may not be configured — silent
    }
  }

  onMount(async () => {
    try {
      roll = await getAdminRoll()
      width_mm = roll.roll_width_mm
      diameter_mm = roll.roll_diameter_mm
    } catch (e) {
      toast.error('Failed to load roll state')
    }
    await loadBotLog(1)
  })

  async function handleRestart() {
    restarting = true
    try {
      await restartService()
    } catch {
      // Server may kill itself before the response arrives — that's fine
    }
    toast.success('Restarting… reload the page in ~15 seconds')
    restarting = false
  }

  async function handleSave() {
    if (!Number.isFinite(width_mm) || width_mm < 1 || !Number.isFinite(diameter_mm) || diameter_mm < 1) {
      toast.error('Width and diameter must be positive numbers')
      return
    }
    saving = true
    try {
      await postAdminRoll(width_mm, diameter_mm)
      toast.success('Roll updated')
      roll = await getAdminRoll().catch(() => roll)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Save failed')
    } finally {
      saving = false
    }
  }

  const statusColour: Record<string, string> = {
    printed: 'text-accent',
    error: 'text-red-400',
    not_allowed: 'text-amber-400',
    help: 'text-gray-400',
  }

  const statusLabel: Record<string, string> = {
    printed: '✓ printed',
    error: '✗ error',
    not_allowed: '⊘ blocked',
    help: '? help',
  }

  function formatTime(iso: string): string {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
</script>

<main class="p-4 flex flex-col gap-6">
  <h1 class="text-xl font-bold">Admin — Till Roll</h1>

  {#if roll}
    <section class="rounded-xl bg-surface p-4 flex flex-col gap-3">
      <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Current Roll</h2>

      <div class="w-32 h-16 mx-auto">
        <RollGauge pct={roll.estimated_remaining_pct} />
      </div>

      <div class="grid grid-cols-2 gap-2 text-sm">
        <div class="text-gray-400">Remaining</div>
        <div class="text-right text-white">{roll.estimated_remaining_pct}%</div>

        <div class="text-gray-400">Printed</div>
        <div class="text-right text-white">{(roll.bytes_printed / 1024).toFixed(1)} KB</div>

        <div class="text-gray-400">Last reset</div>
        <div class="text-right text-white text-xs">{new Date(roll.last_reset).toLocaleString()}</div>

        <div class="text-gray-400">Roll size</div>
        <div class="text-right text-white">{roll.roll_width_mm}mm × ⌀{roll.roll_diameter_mm}mm</div>
      </div>
    </section>
  {:else}
    <p class="text-gray-400 text-sm">Loading roll state…</p>
  {/if}

  <section class="rounded-xl bg-surface p-4 flex flex-col gap-4">
    <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Log New Roll</h2>

    <div class="flex flex-col gap-1">
      <label class="text-sm text-gray-400" for="width">Width (mm)</label>
      <input
        id="width"
        bind:value={width_mm}
        type="number"
        min="1"
        class="w-full rounded-lg bg-bg px-3 py-2 text-white min-h-[44px]"
      />
    </div>

    <div class="flex flex-col gap-1">
      <label class="text-sm text-gray-400" for="diameter">Diameter (mm)</label>
      <input
        id="diameter"
        bind:value={diameter_mm}
        type="number"
        min="1"
        class="w-full rounded-lg bg-bg px-3 py-2 text-white min-h-[44px]"
      />
    </div>

    <PrintButton loading={saving} onclick={handleSave}>Save New Roll</PrintButton>
  </section>

  <section class="rounded-xl bg-surface p-4 flex flex-col gap-3">
    <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Service</h2>
    <p class="text-sm text-gray-400">Restart after a printer power cycle to reconnect USB.</p>
    <PrintButton loading={restarting} onclick={handleRestart}>Restart Service</PrintButton>
  </section>

  <section class="rounded-xl bg-surface p-4 flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Printy — Bot Messages</h2>
      {#if botTotal > 0}
        <span class="text-xs text-gray-600">{botTotal} total</span>
      {/if}
    </div>

    {#if botLog.length === 0}
      <p class="text-sm text-gray-400">No messages yet — or bot is not configured.</p>
    {:else}
      <ul class="flex flex-col gap-3">
        {#each botLog as msg}
          <li class="flex flex-col gap-0.5 text-sm border-b border-gray-800 pb-3">
            <div class="flex items-center justify-between gap-2">
              <span class="text-white font-medium">{msg.sender_name}</span>
              <div class="flex items-center gap-2 shrink-0">
                <span class="{statusColour[msg.status] ?? 'text-gray-400'} text-xs font-medium">
                  {statusLabel[msg.status] ?? msg.status}
                </span>
                <span class="text-gray-600 text-xs">{formatTime(msg.timestamp)}</span>
              </div>
            </div>
            <span class="text-gray-400 break-words">{msg.text}</span>
          </li>
        {/each}
      </ul>

      {#if totalPages > 1}
        <div class="flex items-center justify-between pt-1">
          <button
            onclick={() => loadBotLog(botPage - 1)}
            disabled={botPage <= 1}
            class="px-3 py-2 rounded-lg bg-bg text-white text-sm disabled:opacity-30 min-h-[44px] min-w-[44px]"
          >← Prev</button>
          <span class="text-xs text-gray-400">Page {botPage} of {totalPages}</span>
          <button
            onclick={() => loadBotLog(botPage + 1)}
            disabled={botPage >= totalPages}
            class="px-3 py-2 rounded-lg bg-bg text-white text-sm disabled:opacity-30 min-h-[44px] min-w-[44px]"
          >Next →</button>
        </div>
      {/if}
    {/if}
  </section>
</main>
