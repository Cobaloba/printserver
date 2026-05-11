<script lang="ts">
  import PrintCard from '$lib/components/PrintCard.svelte'
</script>

<main class="p-4">
  <div class="grid grid-cols-2 gap-3">
    <PrintCard title="Free Text" description="Print any text" href="/free-text" />
    <PrintCard title="QR Code" description="Print a QR code" href="/qr-code" />
    <PrintCard title="Todo" description="Print a to-do list" href="/todo" />
    <PrintCard title="Receipt" description="Print a fake receipt" href="/receipt" />
    <PrintCard title="Goatse" description="You know what this is" href="/goatse" />
    <PrintCard title="Admin" description="Manage till roll" href="/admin" />
  </div>
</main>
