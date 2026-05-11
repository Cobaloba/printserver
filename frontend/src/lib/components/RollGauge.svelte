<script lang="ts">
  let { pct }: { pct: number } = $props()

  const r = 45
  const cx = 50
  const cy = 55

  function toCartesian(angleDeg: number) {
    const rad = (angleDeg * Math.PI) / 180
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
  }

  // Semicircle: left point (180°) clockwise through top (270°) to right (360°)
  const left = toCartesian(180)   // {x: 5, y: 55}
  const right = toCartesian(360)  // {x: 95, y: 55}

  let fillEnd = $derived(toCartesian(180 + Math.min(Math.max(pct, 0), 100) * 1.8))
  let strokeColor = $derived(pct < 15 ? '#ef4444' : '#22c55e')

  const bgPath = `M ${left.x} ${left.y} A ${r} ${r} 0 0 1 ${right.x} ${right.y}`
</script>

<svg viewBox="0 0 100 60" aria-label="Roll gauge {pct}%">
  <!-- Background arc -->
  <path
    d={bgPath}
    fill="none"
    stroke="#374151"
    stroke-width="8"
    stroke-linecap="round"
  />
  <!-- Fill arc -->
  {#if pct > 0}
    <path
      d={`M ${left.x} ${left.y} A ${r} ${r} 0 0 1 ${fillEnd.x} ${fillEnd.y}`}
      fill="none"
      stroke={strokeColor}
      stroke-width="8"
      stroke-linecap="round"
    />
  {/if}
</svg>
