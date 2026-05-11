<script lang="ts">
  import { onMount } from 'svelte'
  import { toast } from 'svelte-sonner'
  import { getAdminRoll, postAdminRoll } from '$lib/api'
  import type { RollState } from '$lib/types'
  import PrintButton from '$lib/components/PrintButton.svelte'
  import RollGauge from '$lib/components/RollGauge.svelte'

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

  async function handleSave() {
    saving = true
    try {
      await postAdminRoll(width_mm, diameter_mm)
      roll = await getAdminRoll()
      toast.success('Roll updated')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Save failed')
    } finally {
      saving = false
    }
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
</main>
