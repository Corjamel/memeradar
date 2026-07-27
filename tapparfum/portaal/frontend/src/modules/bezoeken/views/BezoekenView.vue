<script setup>
// Bezoeken & notities (v71 VIEWS.bezoeken) — het geaggregeerde AM/kantoor-scherm:
// KPI's (bezoeken deze maand, open opvolgingen, langst niet bezocht), het
// bezoekritme per winkel (stilste eerst), en één netwerkbrede logboek-stroom
// met een filter. Loggen zelf gebeurt per winkel op de winkelpagina; dit is de
// vogelvlucht. "✉️ Mail de klant" opent een mailto naar de winkel.
import { computed, onMounted, ref } from 'vue'
import { useTappunten } from '../../tappunten/store.js'
import { LOG_TYPES, fmtDuur, dagenSindsBezoek, bezoekStil, BEZOEK_RITME_DAGEN } from '../../logboek/logic.js'

const st = useTappunten()
const filter = ref('alle')       // alle | bezoek | telefoon | mail | notitie
const maand = new Date().toISOString().slice(0, 7)

onMounted(async () => { if (!st.items.length) await st.laad() })

// Alle logregels van alle zichtbare winkels, met winkel-context, nieuwste eerst.
const alleLogs = computed(() => {
  const uit = []
  st.items.forEach(t => (t.logboek || []).forEach(e => uit.push({ t, e })))
  return uit.sort((a, b) => (a.e.at < b.e.at ? 1 : -1))
})
const zichtbaar = computed(() => filter.value === 'alle'
  ? alleLogs.value
  : alleLogs.value.filter(x => x.e.type === filter.value))

const kpi = computed(() => {
  const bezoekenMaand = alleLogs.value.filter(x => x.e.type === 'bezoek' && String(x.e.at || '').slice(0, 7) === maand).length
  const openOpvolg = alleLogs.value.filter(x => x.e.nextDate && !x.e.nextDone).length
  let langst = null
  st.items.forEach(t => {
    const d = dagenSindsBezoek(t)
    if (d != null && (!langst || d > langst.d)) langst = { t, d }
  })
  return { bezoekenMaand, openOpvolg, langst }
})

// Bezoekritme per winkel — stilste (langst niet bezocht) eerst; toon top 8.
const ritme = computed(() => st.items
  .map(t => ({ t, dagen: dagenSindsBezoek(t), stil: bezoekStil(t) }))
  .sort((a, b) => (b.dagen == null ? 1e9 : b.dagen) - (a.dagen == null ? 1e9 : a.dagen))
  .slice(0, 8))
</script>

<template>
  <div>
    <header class="vheld"><div>
      <p class="eyebrow">Relatiebeheer</p>
      <h1>🗓️ Bezoeken &amp; notities</h1>
      <p class="sub">Het netwerkbrede overzicht — wie is er lang niet bezocht, welke opvolgingen staan open, en de laatste contactmomenten.</p>
    </div></header>

    <div class="kpirow">
      <div class="kpi"><b>{{ kpi.bezoekenMaand }}</b><span>bezoeken deze maand</span></div>
      <div class="kpi"><b :class="{ amber: kpi.openOpvolg > 0 }">{{ kpi.openOpvolg }}</b><span>open opvolgingen</span></div>
      <div class="kpi">
        <b :class="{ amber: kpi.langst && kpi.langst.d >= BEZOEK_RITME_DAGEN }">{{ kpi.langst ? kpi.langst.d + ' dgn' : '—' }}</b>
        <span>langst niet bezocht{{ kpi.langst ? ' · ' + kpi.langst.t.name : '' }}</span>
      </div>
    </div>

    <div class="kaart">
      <h2>Bezoekritme (stilste eerst)</h2>
      <router-link v-for="r in ritme" :key="r.t.snelstart" class="rij klik" data-test="ritme-rij"
                   :to="{ name: 'winkel', params: { code: r.t.snelstart } }">
        <b>{{ r.t.name }}</b>
        <span class="badge" :class="r.stil ? 'amber' : 'groen'">
          {{ r.dagen == null ? 'nooit bezocht' : (r.stil ? `⚠ ${r.dagen} dgn` : `${r.dagen} dgn geleden`) }}
        </span>
        <a v-if="r.t.email" class="mail geen-print" :href="'mailto:' + r.t.email" data-test="mail-klant"
           @click.stop>✉️ Mail de klant</a>
      </router-link>
      <p v-if="!ritme.length" class="stil">Nog geen winkels.</p>
    </div>

    <div class="kaart">
      <div class="kop">
        <h2>Logboek — hele netwerk</h2>
        <div class="filters geen-print">
          <button v-for="f in ['alle', 'bezoek', 'telefoon', 'mail', 'notitie']" :key="f" class="fchip"
                  :class="{ aan: filter === f }" type="button" :data-test="'filter-' + f" @click="filter = f">
            {{ f === 'alle' ? 'Alles' : (LOG_TYPES[f]?.l || f) }}
          </button>
        </div>
      </div>
      <div v-for="(x, i) in zichtbaar.slice(0, 40)" :key="i" class="logrij" data-test="netlog-rij">
        <router-link class="wnaam" :to="{ name: 'winkel', params: { code: x.t.snelstart } }">{{ x.t.name }}</router-link>
        <span class="soort" :style="{ background: LOG_TYPES[x.e.type]?.bg, color: LOG_TYPES[x.e.type]?.fg }">{{ LOG_TYPES[x.e.type]?.ic }} {{ LOG_TYPES[x.e.type]?.l }}</span>
        <span v-if="x.e.dir" class="mdir">{{ x.e.dir === 'in' ? '↓' : '↑' }}</span>
        <span v-if="x.e.duurMin != null" class="duur">⏱ {{ fmtDuur(x.e.duurMin) }}</span>
        <span class="txt">{{ x.e.txt }}</span>
        <span v-if="x.e.nextDate" class="opvolg" :class="{ af: x.e.nextDone }">opvolgen {{ x.e.nextDate }}{{ x.e.nextDone ? ' ✓' : '' }}</span>
        <span class="datum">{{ x.e.at }}</span>
      </div>
      <p v-if="!zichtbaar.length" class="stil">Geen logregels{{ filter === 'alle' ? '' : ' van dit type' }}.</p>
      <p v-else-if="zichtbaar.length > 40" class="mo">… en nog {{ zichtbaar.length - 40 }} oudere regels — verfijn met het filter.</p>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 10px;font-size:15px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kpirow{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid var(--line);background:#fff;margin-bottom:14px}
.kpi{padding:14px 16px;border-right:1px solid var(--line);display:flex;flex-direction:column;gap:3px}
.kpi:last-child{border-right:0}
.kpi b{font-size:22px;font-weight:800;font-variant-numeric:tabular-nums}
.kpi b.amber{color:var(--amber)}
.kpi span{font-size:11px;color:var(--grey);text-transform:uppercase;letter-spacing:.4px;font-weight:700}
@media(max-width:620px){.kpirow{grid-template-columns:1fr}.kpi{border-right:0;border-bottom:1px solid var(--line)}}
.kaart{background:#fff;border:1px solid var(--line);padding:16px;margin-bottom:14px}
.kop{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.rij{display:flex;align-items:center;gap:12px;padding:9px 0;border-bottom:1px solid var(--line);text-decoration:none;color:inherit}
.rij:last-child{border-bottom:0}
.rij.klik:hover b{color:var(--coral)}
.badge{font-size:11px;font-weight:800;border-radius:6px;padding:2px 9px}
.badge.groen{background:var(--green-soft);color:#2c5a12}
.badge.amber{background:var(--amber);color:#412402}
.mail{margin-left:auto;color:var(--coral);font-weight:700;font-size:12.5px;text-decoration:none}
.mail:hover{text-decoration:underline}
.filters{display:flex;gap:6px;flex-wrap:wrap}
.fchip{border:1.5px solid var(--line);background:#fff;padding:5px 11px;font-size:12px;font-weight:700;color:var(--grey);cursor:pointer}
.fchip.aan{border-color:var(--coral);background:var(--soft);color:var(--coral-d)}
.logrij{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid var(--line);font-size:13.5px;flex-wrap:wrap}
.logrij:last-child{border-bottom:0}
.wnaam{font-weight:800;color:var(--ink);text-decoration:none;min-width:110px}
.wnaam:hover{color:var(--coral)}
.soort{font-size:10.5px;font-weight:800;border-radius:6px;padding:2px 8px;white-space:nowrap}
.mdir,.duur{font-size:10.5px;font-weight:800;background:var(--mist);color:#21343f;border-radius:6px;padding:2px 7px}
.txt{flex:1;min-width:140px}
.opvolg{font-size:11.5px;font-weight:700;color:var(--coral-d)}
.opvolg.af{color:var(--grey);text-decoration:line-through}
.datum{color:var(--grey);font-size:12px;font-variant-numeric:tabular-nums}
.mo{color:var(--grey);font-size:12.5px}
.stil{color:var(--grey)}
</style>
