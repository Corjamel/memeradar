<script setup>
// Vandaag — de dagstart van de accountmanager (v71 VIEWS.vandaag, r.3930-3973).
// Eén werklijst uit zeven bronnen, gegroepeerd op urgentie:
//   🔥 Nu       — te laat/vandaag: opvolgcadans, logboek-opvolgingen, open winkelvragen
//   📋 Deze week — opvolgingen binnen 7 dagen, open afspraken, geplande/controle-bezoeken
//   🔁 Ritme    — bezoekritme (90 dgn), bestelritme (60 dgn), acties zonder deelname
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { haalWinkelvragen } from '../../winkelvragen/api.js'
import { haalActies, isActief } from '../../acties/api.js'
import {
  followups, markFU, logOpenNext, logNextDone, afsprakenOpen, afspraakDone,
  dagenSindsBezoek, planBezoek, visitOpenClaims, dagenTot
} from '../../logboek/logic.js'
import { dagenSindsBestelling } from '../../bestellingen/logic.js'
import { reactOpenLijst, reactDone } from '../../trajecten/logic.js'

const auth = useAuth()
const st = useTappunten()
const vragen = ref([])
const acties = ref([])
const fout = ref('')
const bezig = ref(false)
const planVoor = ref(null)     // snelstart waarvoor de plan-datepicker open staat
const planDatum = ref('')

onMounted(async () => {
  try {
    if (!st.items.length) await st.laad()
    const [v, a] = await Promise.all([haalWinkelvragen(), haalActies().catch(() => [])])
    vragen.value = v.filter(x => x.status === 'open')
    acties.value = a
  } catch (e) { fout.value = 'Kon de werklijst niet volledig laden: ' + e.message }
})

/* De v71-sortering: bak 'nu' vóór 'week' vóór 'ritme', binnen de bak op prioriteit p. */
const items = computed(() => {
  const uit = []
  const cl = st.items

  // 1+2. Opvolgcadans (fu d7/d30/d60/d90) + logboek-opvolgingen → agenda-items
  followups(cl).filter(f => !f.done && f.diff != null).forEach(f => {
    const lbl = f.diff < 0 ? `${f.lab} · ${Math.abs(f.diff)} dgn te laat` : (f.diff === 0 ? f.lab + ' · vandaag' : `${f.lab} · over ${f.diff} dgn`)
    if (f.diff < 0) uit.push({ b: 'nu', p: f.diff / 1000, ic: '⏰', kind: 'fu', t: f.t, f, lbl, laat: true })
    else if (f.diff === 0) uit.push({ b: 'nu', p: 1, ic: '📅', kind: 'fu', t: f.t, f, lbl })
    else if (f.diff <= 7) uit.push({ b: 'week', p: 10 + f.diff, ic: '📅', kind: 'fu', t: f.t, f, lbl })
  })
  logOpenNext(cl).forEach(o => {
    const lbl = o.diff < 0 ? `opvolgen · ${Math.abs(o.diff)} dgn te laat` : (o.diff === 0 ? 'opvolgen · vandaag' : `opvolgen · over ${o.diff} dgn`)
    if (o.diff < 0) uit.push({ b: 'nu', p: o.diff / 1000, ic: '⏰', kind: 'lognext', t: o.t, e: o.e, lbl, laat: true })
    else if (o.diff === 0) uit.push({ b: 'nu', p: 1, ic: '📅', kind: 'lognext', t: o.t, e: o.e, lbl })
    else if (o.diff <= 7) uit.push({ b: 'week', p: 10 + o.diff, ic: '📅', kind: 'lognext', t: o.t, e: o.e, lbl })
  })

  // 2b. Heractivatie-opvolgingen (v71 reactOpen) → zelfde cadans als agenda-items
  reactOpenLijst(cl).forEach(o => {
    const lbl = o.diff < 0 ? `heractivatie · ${Math.abs(o.diff)} dgn te laat` : (o.diff === 0 ? 'heractivatie · vandaag' : `heractivatie · over ${o.diff} dgn`)
    const extra = o.goalW ? ` · doel ≈ ${o.goalW} flessen/week` : ''
    if (o.diff < 0) uit.push({ b: 'nu', p: o.diff / 1000, ic: '🔁', kind: 'react', t: o.t, r: o.r, idx: o.idx, lbl: lbl + extra, laat: true })
    else if (o.diff === 0) uit.push({ b: 'nu', p: 1, ic: '🔁', kind: 'react', t: o.t, r: o.r, idx: o.idx, lbl: lbl + extra })
    else if (o.diff <= 7) uit.push({ b: 'week', p: 10 + o.diff, ic: '🔁', kind: 'react', t: o.t, r: o.r, idx: o.idx, lbl: lbl + extra })
  })

  // 3. Open winkelvragen (de berichtlijn) → nu
  const naam = Object.fromEntries(cl.map(t => [t.snelstart, t.name]))
  vragen.value.forEach(v => uit.push({ b: 'nu', p: 2, ic: '📨', kind: 'vraag', v, naam: naam[v.tappunt_snelstart] || v.tappunt_snelstart, lbl: 'Vraag van de winkel · ' + String(v.created_at || '').slice(0, 10) }))

  // 4. Open afspraken → week
  cl.forEach(t => afsprakenOpen(t).forEach(a => uit.push({ b: 'week', p: 20, ic: '📌', kind: 'afspraak', t, a, lbl: 'Open afspraak · ' + a.at })))

  // 5. Geplande bezoeken + punten-controle-bezoeken → week
  cl.forEach(t => {
    const n = visitOpenClaims(t)
    if (t.bezoekGepland) {
      uit.push({ b: 'week', p: 15 + (dagenTot(t.bezoekGepland) || 0), ic: '🗓️', kind: 'gepland', t, lbl: 'Gepland bezoek · ' + t.bezoekGepland + (n ? ` · ${n} punt(en) controleren` : '') })
    } else if (n) {
      uit.push({ b: 'week', p: 18, ic: '✋', kind: 'controle', t, lbl: `${n} geclaimd(e) punt(en) controleren — nog geen bezoek gepland` })
    }
  })

  // 6. Bezoekritme (90 dgn) → ritme
  cl.forEach(t => {
    const d = dagenSindsBezoek(t)
    if ((d == null || d > 90) && !t.bezoekGepland) {
      uit.push({ b: 'ritme', p: 30 + (d == null ? 400 : Math.min(d, 400)) * -0.01, ic: '⚠', kind: 'bezoek', t, lbl: d == null ? 'Nog nooit bezocht — plan een bezoek' : `${d} dgn niet bezocht — plan een bezoek` })
    }
  })

  // 7. Bestelritme (60 dgn) + acties zonder deelname → ritme
  cl.forEach(t => {
    const d = dagenSindsBestelling(t)
    if (d == null || d > 60) uit.push({ b: 'ritme', p: 40, ic: '🛒', kind: 'bestel', t, lbl: d == null ? 'Nog geen bestelling — bel over de nieuwe geuren' : `${d} dgn geen bestelling — bel over de nieuwe geuren` })
  })
  acties.value.filter(a => isActief(a)).forEach(a => {
    const miss = cl.filter(t => !(t.actieDeelname && t.actieDeelname[a.id] && t.actieDeelname[a.id].done)).length
    if (miss) uit.push({ b: 'ritme', p: 50, ic: '📣', kind: 'actie', a, lbl: `${miss} winkel${miss > 1 ? 's doen' : ' doet'} nog niet mee` })
  })

  return uit.sort((x, y) => x.p - y.p)
})

const nu = computed(() => items.value.filter(i => i.b === 'nu'))
const week = computed(() => items.value.filter(i => i.b === 'week'))
const ritme = computed(() => items.value.filter(i => i.b === 'ritme'))
const groet = (h => h < 6 ? 'Goedenacht' : h < 12 ? 'Goedemorgen' : h < 18 ? 'Goedemiddag' : 'Goedenavond')(new Date().getHours())

async function bewaar(t2) {
  bezig.value = true; fout.value = ''
  try { await st.bewaar(t2) } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}
async function vinkFU(i, v) { await bewaar(markFU(i.f.t, i.f.k, v)) }
async function vinkNext(i, v) { await bewaar(logNextDone(i.t, i.e.id, v)) }
async function vinkReact(i, v) { await bewaar(reactDone(i.t, i.idx, v)) }
async function vinkAfspraak(i, v) { await bewaar(afspraakDone(i.t, i.a.id, v, 'am')) }
async function plan(i) {
  if (!planDatum.value) return
  await bewaar(planBezoek(i.t, planDatum.value))
  planVoor.value = null; planDatum.value = ''
}
</script>

<template>
  <div>
    <header class="held">
      <div>
        <h1>{{ groet }} ☀️</h1>
        <p class="sub" data-test="vandaag-sub">Je dagstart — wat nú aandacht vraagt{{ items.length ? ` · ${nu.length ? nu.length + ' urgent, ' : ''}alles direct af te handelen vanuit deze lijst.` : ' · alles bij — geen openstaande acties. Sterk!' }}</p>
      </div>
    </header>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <template v-for="[titel, groep, klas] in [['🔥 Nu', nu, 'nu'], ['📋 Deze week', week, 'week'], ['🔁 Ritme — voorkom stilte', ritme, 'ritme']]" :key="klas">
      <h2 v-if="groep.length" :data-test="'kop-' + klas">{{ titel }}</h2>
      <div v-for="(i, idx) in (klas === 'ritme' ? groep.slice(0, 10) : groep)" :key="klas + idx"
           class="item" :class="{ laat: i.laat }" :data-test="'item-' + i.kind">
        <!-- afvinkbaar -->
        <input v-if="i.kind === 'fu'" type="checkbox" :disabled="bezig" :data-test="'vink-fu-' + i.f.k" @change="vinkFU(i, $event.target.checked)" />
        <input v-else-if="i.kind === 'lognext'" type="checkbox" :disabled="bezig" @change="vinkNext(i, $event.target.checked)" />
        <input v-else-if="i.kind === 'react'" type="checkbox" :disabled="bezig" :data-test="'vink-react-' + i.t.snelstart" @change="vinkReact(i, $event.target.checked)" />
        <input v-else-if="i.kind === 'afspraak'" type="checkbox" :disabled="bezig" @change="vinkAfspraak(i, $event.target.checked)" />
        <span v-else class="ic">{{ i.ic }}</span>

        <div class="mid">
          <b v-if="i.t">{{ i.t.name }}</b>
          <b v-else-if="i.a && i.kind === 'actie'">{{ i.a.titel }}</b>
          <b v-else-if="i.v">{{ i.naam }}</b>
          <span class="lbl">
            <template v-if="i.kind === 'fu' && i.f.tgt">{{ i.f.tgt }} · </template>
            <template v-if="i.kind === 'lognext'">{{ i.e.txt.slice(0, 90) }} · </template>
            <template v-if="i.kind === 'react'">{{ i.r.actie }} · </template>
            <template v-if="i.kind === 'afspraak'">{{ i.a.txt }} · </template>
            <template v-if="i.kind === 'vraag'">{{ i.v.txt }} · </template>
            {{ i.lbl }}
          </span>
        </div>

        <a v-if="i.t && i.t.tel" class="klein" :href="'tel:' + i.t.tel" :aria-label="'Bel ' + i.t.name">📞</a>
        <template v-if="i.kind === 'bezoek'">
          <template v-if="planVoor === i.t.snelstart">
            <input v-model="planDatum" type="date" class="datum" data-test="plan-datum" />
            <button class="klein" type="button" :disabled="!planDatum || bezig" data-test="plan-ok" @click="plan(i)">OK</button>
          </template>
          <button v-else class="klein" type="button" :data-test="'plan-' + i.t.snelstart" @click="planVoor = i.t.snelstart">Plan</button>
        </template>
        <router-link v-if="i.kind === 'vraag'" class="klein" :to="{ name: 'berichten' }">Beantwoord →</router-link>
        <router-link v-else-if="i.kind === 'actie'" class="klein" :to="{ name: 'acties' }">→</router-link>
        <router-link v-else-if="i.t" class="klein" :to="{ name: 'winkel', params: { code: i.t.snelstart } }">→</router-link>
      </div>
      <p v-if="klas === 'ritme' && groep.length > 10" class="mo">… en {{ groep.length - 10 }} meer — zie Winkels en Bestellingen.</p>
    </template>

    <div v-if="!items.length" class="leeg" data-test="vandaag-leeg">🎉 Lege lijst — tijd voor proactief werk: plan bezoeken vooruit of bel je toppers.</div>
  </div>
</template>

<style scoped>
.held{background:linear-gradient(115deg,var(--soft),#fff 72%);border:1px solid var(--line);border-radius:18px;padding:18px 22px;margin-bottom:14px}
h1{margin:0;font-size:24px}
h2{margin:18px 0 8px;font-size:13px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--grey)}
.sub{color:var(--grey);margin:4px 0 0;font-size:13.5px}
.item{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin-bottom:8px;font-size:13.5px;flex-wrap:wrap}
.item.laat{border-color:var(--amber);background:linear-gradient(90deg,#fdf6e8,#fff 60%)}
.item input[type=checkbox]{width:17px;height:17px;accent-color:var(--coral);flex-shrink:0}
.ic{font-size:16px;flex-shrink:0}
.mid{flex:1;min-width:220px;display:flex;flex-direction:column;gap:1px}
.lbl{color:var(--grey);font-size:12.5px}
.klein{background:none;border:1.5px solid var(--line);border-radius:8px;padding:4px 11px;font-size:12px;font-weight:700;color:var(--grey);cursor:pointer;text-decoration:none;white-space:nowrap}
.klein:hover{border-color:var(--coral);color:var(--coral-d)}
.klein:disabled{opacity:.5}
.datum{padding:5px 8px;border:1.5px solid var(--line);border-radius:8px;font-size:12.5px;font-family:inherit}
.mo{color:var(--grey);font-size:12.5px}
.leeg{background:#fff;border:1px dashed var(--line);border-radius:14px;padding:26px;text-align:center;color:var(--grey)}
.fout{color:#b3261e}
</style>
