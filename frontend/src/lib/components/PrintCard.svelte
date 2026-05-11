<script lang="ts">
  let { title, description, href }: { title: string; description: string; href: string } = $props()
</script>

<a
  {href}
  class="block p-4 rounded-xl bg-surface min-h-[44px] hover:opacity-90 transition-opacity"
>
  <h2 class="font-semibold text-white">{title}</h2>
  <p class="mt-1 text-sm text-gray-400">{description}</p>
</a>
