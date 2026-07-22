<script setup>
// De signatuur van het portaal: een parfumfles die zich vult met voortgang.
import { computed } from 'vue'
let teller = 0
const props = defineProps({
  pct: { type: Number, default: 0 },
  label: { type: String, default: '' }
})
const uid = `flesclip-${++teller}`
const p = computed(() => Math.max(0, Math.min(100, Math.round(props.pct))))
const FLES = 'M20 16 h20 v6 c8 4 12 10 12 20 v46 a8 8 0 0 1 -8 8 h-28 a8 8 0 0 1 -8 -8 v-46 c0 -10 4 -16 12 -20 z'
</script>

<template>
  <div class="fles" role="img" :aria-label="`Gevuld: ${p}%${label ? ' — ' + label : ''}`">
    <svg viewBox="0 0 60 100" width="52" height="88" aria-hidden="true">
      <rect x="24" y="3" width="12" height="11" rx="2.5" class="dop" />
      <clipPath :id="uid"><path :d="FLES" /></clipPath>
      <rect x="6" :y="96 - 0.78 * p" width="48" :height="0.78 * p + 4" :clip-path="`url(#${uid})`" class="parfum" />
      <path :d="FLES" class="glas" />
    </svg>
    <div class="pct"><b>{{ p }}%</b><span v-if="label">{{ label }}</span></div>
  </div>
</template>

<style scoped>
.fles{display:flex;align-items:center;gap:10px}
.dop{fill:var(--ink);opacity:.85}
.glas{fill:none;stroke:var(--ink);stroke-width:2.5;stroke-linejoin:round;opacity:.75}
.parfum{fill:var(--coral);opacity:.85;transition:y .6s ease,height .6s ease}
.pct{display:flex;flex-direction:column;line-height:1.15}
.pct b{font-size:22px;color:var(--coral-d)}
.pct span{font-size:11.5px;color:var(--grey);font-weight:700;max-width:110px}
</style>
