<script setup>
// Bestellingen — de hartslag van het netwerk (v71 'am:bestellingen').
// Alle bestellingen over de zichtbare winkels, de stiltelijst (60+ dagen) en
// de CSV-import: één poort voor handwerk, CSV én straks de B2B-API.
import Icoon from '../../../components/Icoon.vue'
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { eur0 } from '../../../lib/format.js'
import { bestellingenVan, dagenSindsBestelling, bestelStil, parseBestelCSV, importBestellingen, BESTEL_STIL_DAGEN } from '../logic.js'

const auth = useAuth()
const st = useTappunten()
const fout = ref('')
const melding = ref('')
const bezig = ref(false)
const csv = ref('')

onMounted(async () => {
  try { if (!st.items.length) await st.laad() }
  catch (e) { fout.value = 'Kon winkels niet laden: ' + e.message }
})

const alle = computed(() => {
  const uit = []
  st.items.forEach(t => bestellingenVan(t).forEach(b => uit.push({ t, b })))
  return uit.sort((a, b) => (a.b.at < b.b.at ? 1 : -1))
})
const maand = computed(() => {
  const m = new Date().toISOString().slice(0, 7)
  return alle.value.filter(x => String(x.b.at || '').slice(0, 7) === m).length
})
const stilte = computed(() => st.items
  .filter(t => bestelStil(t))
  .map(t => ({ t, dagen: dagenSindsBestelling(t) }))
  .sort((a, b) => b.dagen - a.dagen))

const preview = computed(() => parseBestelCSV(csv.value))

async function importeer() {
  if (bezig.value || !preview.value.length) return
  bezig.value = true; fout.value = ''; melding.value = ''
  try {
    const res = importBestellingen(st.items, preview.value, 'csv')
    for (const t2 of res.updates) await st.bewaar(t2)
    melding.value = `✓ ${res.ok} geïmporteerd · ${res.dup} dubbel overgeslagen` +
      (res.miss.length ? ` · niet gevonden: ${res.miss.join(', ')}` : '')
    if (res.ok) csv.value = ''
  } catch (e) { fout.value = 'Import mislukt: ' + e.message }
  bezig.value = false
}
</script>

<template>
  <div>
    <header class="vheld"><div>
      <p class="eyebrow">Bestelritme</p>
      <h1><Icoon naam="bestellen" /> Bestellingen</h1>
      <p class="sub">Het bestelritme is de hartslag van een winkel — stilte die je vroeg hoort, is een klant die je nog kunt redden.</p>
    </div></header>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <div class="tegels">
      <div class="tegel"><div class="cijfer" data-test="best-maand">{{ maand }}</div><div class="lbl">bestellingen deze maand</div></div>
      <div class="tegel"><div class="cijfer" data-test="best-stil">{{ stilte.length }}</div><div class="lbl">winkels {{ BESTEL_STIL_DAGEN }}+ dagen stil</div></div>
    </div>

    <!-- Stiltelijst -->
    <div v-if="stilte.length" class="kaart">
      <h2>⚠ Bestelritme gevallen</h2>
      <router-link v-for="r in stilte" :key="r.t.snelstart" class="rij klik" data-test="stil-winkel"
                   :to="{ name: 'winkel', params: { code: r.t.snelstart } }">
        <b>{{ r.t.name }}</b>
        <span class="badge amber">{{ r.dagen }} dagen stil</span>
        <span class="mo">bel of plan een bezoek →</span>
      </router-link>
    </div>

    <!-- CSV-import -->
    <details class="kaart imp">
      <summary>CSV-import (kolommen: datum · tappunt/snelstart · ordernr · totaal · omschrijving)</summary>
      <textarea v-model="csv" rows="6" data-test="csv-tekst"
                placeholder="datum;snelstart;ordernr;totaal&#10;22-07-2026;kl-1;F1001;€ 1.234,56"></textarea>
      <div class="acties">
        <span class="mo" data-test="csv-preview">{{ preview.length }} regels herkend</span>
        <button class="btn" type="button" :disabled="bezig || !preview.length" data-test="csv-import" @click="importeer">Importeren</button>
        <span v-if="melding" class="mo" role="status" data-test="csv-resultaat">{{ melding }}</span>
      </div>
      <p class="mo">Dezelfde poort als straks de automatische B2B-koppeling — dubbel ordernummer wordt altijd overgeslagen.</p>
    </details>

    <!-- Laatste bestellingen -->
    <div class="kaart">
      <h2>Laatste bestellingen</h2>
      <div v-for="x in alle.slice(0, 30)" :key="x.b.id" class="rij" data-test="best-rij">
        <span class="datum">{{ x.b.at }}</span>
        <b>{{ x.t.name }}</b>
        <span class="mo" v-if="x.b.ref">#{{ x.b.ref }}</span>
        <span class="bedrag">{{ eur0(x.b.totaal) }}</span>
      </div>
      <p v-if="!alle.length" class="stil">Nog geen bestellingen geregistreerd — voeg ze toe op de winkelpagina of via de CSV-import.</p>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 10px;font-size:15px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.tegels{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-bottom:12px}
.tegel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.cijfer{font-size:22px;font-weight:800;color:var(--coral)}
.lbl{font-size:12px;color:var(--grey);font-weight:700}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.rij{display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--line);font-size:14px;color:inherit;text-decoration:none}
.rij:last-of-type{border-bottom:0}
.rij.klik:hover b{color:var(--coral)}
.badge{font-size:11.5px;font-weight:800;border-radius:6px;padding:2px 9px}
.badge.amber{background:var(--amber);color:#412402}
.mo{color:var(--grey);font-size:12.5px}
.datum{color:var(--grey);font-size:12.5px;font-variant-numeric:tabular-nums}
.bedrag{margin-left:auto;font-weight:700;font-variant-numeric:tabular-nums}
.imp summary{cursor:pointer;font-weight:800;font-size:14px}
textarea{width:100%;margin-top:10px;padding:10px;border:1.5px solid var(--line);border-radius:10px;font-family:ui-monospace,monospace;font-size:12.5px}
textarea:focus{border-color:var(--coral)}
.acties{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:8px}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:8px 14px;font-weight:800;cursor:pointer;font-size:13px}
.btn:disabled{opacity:.5}
.fout{color:#b3261e}
.stil{color:var(--grey);font-size:13px}
</style>
