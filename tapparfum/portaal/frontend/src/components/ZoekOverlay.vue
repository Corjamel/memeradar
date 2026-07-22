<script setup>
// Globale zoekbalk — v71 (r.1319-1345): één zoekveld over alles heen.
// Doorzoekt namen, snelstartcodes, telefoonnummers, notities, bezoekverslagen,
// afspraken en bestellingen van alle zichtbare winkels (RLS bepaalt de uitsnede).
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTappunten } from '../modules/tappunten/store.js'
import { eur0 } from '../lib/format.js'
import { LOG_TYPES } from '../modules/logboek/logic.js'

const emit = defineEmits(['sluit'])
const st = useTappunten()
const router = useRouter()
const q = ref('')
const veld = ref(null)

onMounted(async () => {
  if (!st.items.length) { try { await st.laad() } catch { /* leeg blijft leeg */ } }
  veld.value?.focus()
})

/* v71 globalSearch: minimaal 2 tekens, vier secties, max 8 per sectie. */
const hits = computed(() => {
  const z = q.value.trim().toLowerCase()
  if (z.length < 2) return null
  const h = { tappunten: [], logs: [], afspraken: [], bestellingen: [] }
  st.items.forEach(t => {
    const kop = [t.name, t.snelstart, t.tel, t.notes, t.contact, t.email, t.plaats, t.postcode, t.type].join(' ').toLowerCase()
    if (kop.includes(z)) h.tappunten.push({ t })
    ;(t.logboek || []).forEach(e => { if (String(e.txt || '').toLowerCase().includes(z)) h.logs.push({ t, e }) })
    ;(t.afspraken || []).forEach(a => { if (String(a.txt || '').toLowerCase().includes(z)) h.afspraken.push({ t, a }) })
    ;(t.bestellingen || []).forEach(b => { if ((String(b.ref || '') + ' ' + String(b.omschrijving || '')).toLowerCase().includes(z)) h.bestellingen.push({ t, b }) })
  })
  return h
})
const leeg = computed(() => hits.value &&
  !hits.value.tappunten.length && !hits.value.logs.length &&
  !hits.value.afspraken.length && !hits.value.bestellingen.length)

function open(t) {
  emit('sluit')
  router.push({ name: 'winkel', params: { code: t.snelstart } })
}
</script>

<template>
  <div class="laag" role="dialog" aria-modal="true" aria-label="Zoeken" @click.self="emit('sluit')" @keydown.esc="emit('sluit')">
    <div class="paneel">
      <div class="balk">
        <input ref="veld" v-model="q" placeholder="Zoek winkel, code, notitie, afspraak of ordernummer…"
               aria-label="Zoekterm" data-test="zoek-veld" />
        <button class="dicht" type="button" aria-label="Zoeken sluiten" data-test="zoek-sluit" @click="emit('sluit')">×</button>
      </div>

      <p v-if="!hits" class="mo">Typ minimaal 2 tekens — doorzoekt namen, snelstartcodes, telefoonnummers, notities, bezoekverslagen, afspraken en bestellingen.</p>
      <p v-else-if="leeg" class="mo" data-test="zoek-leeg">Niets gevonden voor «{{ q.trim() }}».</p>

      <template v-else>
        <template v-for="[titel, lijst, soort] in [['Winkels', hits.tappunten, 'tp'], ['Notities & bezoeken', hits.logs, 'log'], ['Afspraken', hits.afspraken, 'afspraak'], ['Bestellingen', hits.bestellingen, 'bestelling']]" :key="soort">
          <template v-if="lijst.length">
            <h2 :data-test="'zoek-kop-' + soort">{{ titel }} <span class="mo">· {{ lijst.length }}</span></h2>
            <button v-for="(x, i) in lijst.slice(0, 8)" :key="soort + i" class="hit" type="button"
                    :data-test="'zoek-hit-' + soort" @click="open(x.t)">
              <b>{{ x.t.name }}</b>
              <span v-if="soort === 'tp'" class="mo">{{ eur0(x.t.jaaromzet) }} dit jaar · {{ x.t.snelstart }}<template v-if="x.t.tel"> · {{ x.t.tel }}</template></span>
              <span v-else-if="soort === 'log'" class="mo">{{ LOG_TYPES[x.e.type]?.ic }} {{ String(x.e.txt).slice(0, 90) }} · {{ x.e.at }}</span>
              <span v-else-if="soort === 'afspraak'" class="mo">{{ x.a.txt }} · {{ x.a.done ? '✓ afgerond' : 'open' }} · {{ x.a.at }}</span>
              <span v-else class="mo">{{ eur0(x.b.totaal) }}<template v-if="x.b.ref"> · #{{ x.b.ref }}</template> · {{ x.b.at }}</span>
            </button>
            <p v-if="lijst.length > 8" class="mo">… en {{ lijst.length - 8 }} meer — verfijn je zoekterm.</p>
          </template>
        </template>
      </template>
    </div>
  </div>
</template>

<style scoped>
.laag{position:fixed;inset:0;background:rgba(30,20,15,.45);z-index:60;display:flex;justify-content:center;padding:60px 16px 16px}
.paneel{background:#fff;border-radius:18px;padding:18px 20px;width:100%;max-width:620px;max-height:80vh;overflow:auto;box-shadow:0 18px 50px rgba(0,0,0,.25)}
.balk{display:flex;gap:8px;align-items:center}
input{flex:1;padding:11px 14px;border:1.5px solid var(--line);border-radius:12px;font-size:14.5px;font-family:inherit}
input:focus{border-color:var(--coral)}
.dicht{background:none;border:0;font-size:24px;color:var(--grey);cursor:pointer;line-height:1}
.dicht:hover{color:var(--coral-d)}
h2{margin:16px 0 6px;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--grey)}
.mo{color:var(--grey);font-size:12.5px;margin:8px 0 0;font-weight:400}
.hit{display:flex;flex-direction:column;gap:2px;width:100%;text-align:left;background:none;border:0;border-bottom:1px solid var(--line);padding:8px 2px;cursor:pointer;font-family:inherit;font-size:13.5px}
.hit:hover b{color:var(--coral)}
.hit .mo{margin:0}
</style>
