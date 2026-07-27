<script setup>
// Eén icoon uit de v71-lijnset (lib/icons.js) — vervangt de emoji in koppen,
// tabs en kaarten zodat het hele portaal dezelfde rustige iconentaal spreekt.
import { computed } from 'vue'
import { ICONS } from '../lib/icons.js'
const props = defineProps({ naam: { type: String, required: true } })
const svg = computed(() => ICONS[props.naam] || '')
</script>

<template>
  <span class="tp-ic" aria-hidden="true" v-html="svg"></span>
</template>

<style>
/* Bewust niet scoped: v-html-inhoud + gebruik in veel views. */
.tp-ic{display:inline-flex;width:1.1em;height:1.1em;vertical-align:-.14em;color:var(--coral-d);flex-shrink:0}
.tp-ic svg{width:100%;height:100%}
</style>
