<script lang="ts">
  import type { Snippet } from 'svelte'

  interface Props {
    loading?: boolean
    children: Snippet
    onclick?: () => void | Promise<void>
  }

  let { loading = false, children, onclick }: Props = $props()
</script>

<button
  class="w-full py-3 px-4 rounded-lg bg-accent text-black font-semibold
         disabled:opacity-50 min-h-[44px] flex items-center justify-center
         transition-opacity"
  disabled={loading}
  {onclick}
>
  {#if loading}
    <span
      class="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin"
      role="status"
      aria-label="Loading"
    ></span>
  {:else}
    {@render children()}
  {/if}
</button>
