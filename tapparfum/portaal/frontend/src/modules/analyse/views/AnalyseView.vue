<script setup>
// Analyse — het netwerk in cijfers (v71 kanalyse, r.4180-4210). Sturen op
// feiten: alle bedragen zijn inkoop bij TapParfum; kassa = door partners
// geregistreerde winkelverkoop. Kantoor ziet het hele netwerk, een AM die
// hier komt alleen de eigen portefeuille (RLS bepaalt de uitsnede).
import { computed, onMounted, ref } from 'vue'
import { useTappunten } from '../../tappunten/store.js'
import { haalAms } from '../../dashboard/api.js'
import { useAuth } from '../../../stores/auth.js'
import { eur0 } from '../../../lib/format.js'
import { statusKey, STATUS, jaaromzet, kassaJaar } from '../../rekenhart/logic.js'
import { inTraject } from '../../beloningen/logic.js'
import { dagenSindsBestelling } from '../../bestellingen/logic.js'
import { haalRekenConfig } from '../../beloningen/api.js'
import { haalFlesMaten } from '../../kassa/api.js'

const auth = useAuth()
const st = useTappunten()
const ams = ref([])
const marge = ref(1)
const maten = ref([])
const fout = ref('')

onMounted(async () => {
  try {
    if (!st.items.length) await st.laad()
    if (auth.isKantoor) ams.value = await haalAms()
    marge.value = (await haalRekenConfig()).marge
    maten.value = await haalFlesMaten().catch(() => [])
  } catch (e) { fout.value = 'Kon de analyse niet laden: ' + e.message }
})

// Sell-through (kassa): hoeveel winkels registreren écht verkoop en voor
// hoeveel euro (v71 vkActief14 + geregistreerde winkelverkoop dit jaar).
const heeftKassa = (t) => Object.keys(t.verkopen || {}).length > 0
function actief14(t) {
  const grens = new Date(Date.now() - 14 * 864e5).toISOString().slice(0, 10)
  return Object.keys(t.verkopen || {}).some(d => d >= grens)
}
const sellThrough = computed(() => {
  const tot = st.items.length || 0
  const metKassa = st.items.filter(heeftKassa).length
  const recent = st.items.filter(actief14).length
  const euroJaar = st.items.reduce((s, t) => s + kassaJaar(t, maten.value), 0)
  const stuksJaar = Object.values(perMaat.value).reduce((s, n) => s + n, 0)
  return {
    tot, metKassa, recent,
    activatiePct: tot ? Math.round(recent / tot * 100) : 0,
    dekkingPct: tot ? Math.round(metKassa / tot * 100) : 0,
    euroJaar: Math.round(euroJaar), stuksJaar
  }
})

// Per accountmanager: winkels, inkoop-omzet, kassa (echte winkelverkoop).
const perAm = computed(() => {
  const naam = Object.fromEntries(ams.value.map(a => [a.id, a.naam]))
  const m = new Map()
  st.items.forEach(t => {
    const k = t.am_id || '-'
    if (!m.has(k)) m.set(k, { naam: naam[k] || 'Geen AM', n: 0, omzet: 0, kassa: 0, traject: 0 })
    const r = m.get(k)
    r.n++; r.omzet += jaaromzet(t)
    if (inTraject(t)) r.traject++
    Object.values(t.verkopen || {}).forEach(cs => Object.values(cs).forEach(x => { r.kassa += +x || 0 }))
  })
  return [...m.values()].sort((a, b) => b.omzet - a.omzet)
})
const maxOmzet = computed(() => Math.max(1, ...perAm.value.map(r => r.omzet)))

// Statusverdeling over het netwerk (v71 stc).
const statussen = computed(() => {
  const c = { nieuw: 0, groeit: 0, stagneert: 0, top: 0 }
  st.items.forEach(t => { c[statusKey(t, marge.value)] = (c[statusKey(t, marge.value)] || 0) + 1 })
  return c
})
const nTraject = computed(() => st.items.filter(t => inTraject(t)).length)

// Kassa: verkochte flesjes per maat (dit jaar).
const perMaat = computed(() => {
  const y = String(new Date().getFullYear())
  const m = {}
  st.items.forEach(t => Object.entries(t.verkopen || {}).forEach(([dag, cs]) => {
    if (dag.slice(0, 4) !== y) return
    Object.entries(cs).forEach(([maat, n]) => { m[maat] = (m[maat] || 0) + (+n || 0) })
  }))
  return m
})

const top5 = computed(() => [...st.items].sort((a, b) => jaaromzet(b) - jaaromzet(a)).slice(0, 5))
const stilte = computed(() => st.items
  .map(t => ({ t, d: dagenSindsBestelling(t) ?? 9999 }))
  .sort((a, b) => b.d - a.d).slice(0, 5))
</script>

<template>
  <div>
    <header class="vheld"><div>
      <p class="eyebrow">Cijfers</p>
      <h1>📊 Analyse</h1>
      <p class="sub">Het netwerk in cijfers — sturen op feiten. Bedragen = inkoop bij TapParfum; kassa = geregistreerde winkelverkoop.</p>
    </div></header>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Sell-through (kassa): activatie + geregistreerde winkelverkoop -->
    <div class="kaart" data-test="sellthrough">
      <h2>🛒 Sell-through — kassa</h2>
      <div class="stband">
        <div class="stkpi">
          <b :class="{ amber: sellThrough.activatiePct < 40 }" data-test="st-activatie">{{ sellThrough.recent }}<small>/ {{ sellThrough.tot }}</small></b>
          <span>actief (14 dgn) · {{ sellThrough.activatiePct }}%</span>
        </div>
        <div class="stkpi">
          <b data-test="st-euro">{{ eur0(sellThrough.euroJaar) }}</b>
          <span>geregistreerde winkelverkoop dit jaar</span>
        </div>
        <div class="stkpi">
          <b data-test="st-stuks">{{ sellThrough.stuksJaar }}</b>
          <span>verkochte flesjes dit jaar</span>
        </div>
        <div class="stkpi">
          <b data-test="st-dekking">{{ sellThrough.dekkingPct }}%</b>
          <span>winkels met kassaregistratie</span>
        </div>
      </div>
      <p class="mo">Activatie = winkels die de afgelopen 14 dagen verkoop tikten. Kassa is échte winkelverkoop; inkoop bij TapParfum staat daar los van.</p>
    </div>

    <!-- Per accountmanager -->
    <div v-if="perAm.length" class="kaart">
      <h2>Per accountmanager (dit jaar)</h2>
      <div v-for="r in perAm" :key="r.naam" class="amrij" data-test="analyse-am">
        <div class="amkop">
          <b>{{ r.naam }}</b>
          <span class="mo">inkoop {{ eur0(r.omzet) }} · {{ r.n }} winkels · {{ r.traject }} in traject · kassa {{ r.kassa }} st.</span>
        </div>
        <div class="balk"><div class="vul" :style="{ width: (r.omzet / maxOmzet * 100) + '%' }"></div></div>
      </div>
    </div>

    <div class="twee">
      <!-- Netwerk-status -->
      <div class="kaart">
        <h2>Netwerk</h2>
        <div class="chips">
          <span v-for="(v, k) in statussen" :key="k" class="chip" :data-test="'analyse-status-' + k"
                :style="{ background: STATUS[k].bg, color: STATUS[k].fg }">{{ STATUS[k].l }} <b>{{ v }}</b></span>
          <span class="chip grijs">🚀 traject <b data-test="analyse-traject">{{ nTraject }}</b></span>
          <span class="chip grijs">🏬 totaal <b>{{ st.items.length }}</b></span>
        </div>
      </div>
      <!-- Kassa per maat -->
      <div class="kaart">
        <h2>Kassa — flesjes per maat (dit jaar)</h2>
        <div class="chips">
          <span v-for="(n, m) in perMaat" :key="m" class="chip grijs" data-test="analyse-maat">{{ m }} <b>{{ n }}</b></span>
          <span v-if="!Object.keys(perMaat).length" class="stil">Nog geen kassaregistraties.</span>
        </div>
      </div>
    </div>

    <div class="twee">
      <!-- Top 5 -->
      <div class="kaart">
        <h2>Top 5 omzet</h2>
        <div v-for="(t, i) in top5" :key="t.snelstart" class="rij" data-test="analyse-top">
          <span>{{ i + 1 }}. <b>{{ t.name }}</b></span>
          <span class="bedrag">{{ eur0(jaaromzet(t)) }}</span>
        </div>
      </div>
      <!-- Bestelstilte -->
      <div class="kaart">
        <h2>Langste bestelstilte</h2>
        <router-link v-for="x in stilte" :key="x.t.snelstart" class="rij klik" data-test="analyse-stil"
                     :to="{ name: 'winkel', params: { code: x.t.snelstart } }">
          <b>{{ x.t.name }}</b>
          <span class="bedrag" :class="{ rood: x.d > 60 }">{{ x.d === 9999 ? 'nooit besteld' : x.d + ' dgn' }}</span>
        </router-link>
        <p class="mo">Stilte is het eerste churn-signaal — dit is de bellijst.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 10px;font-size:15px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.twee{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.amrij{margin:10px 0}
.amkop{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:13.5px}
.mo{color:var(--grey);font-size:12.5px;margin:6px 0 0}
.balk{height:8px;border-radius:6px;background:#f0ebe3;overflow:hidden;margin-top:5px}
.vul{height:100%;background:var(--coral)}
.stband{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.stkpi{background:var(--cream);border:1px solid var(--line);border-radius:12px;padding:12px 14px;text-align:center}
.stkpi b{display:block;font-size:22px;font-weight:800;color:var(--ink);font-variant-numeric:tabular-nums}
.stkpi b small{font-size:13px;color:var(--grey);font-weight:600}
.stkpi b.amber{color:var(--amber)}
.stkpi span{font-size:11.5px;color:var(--grey);display:block;margin-top:2px}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{font-size:12.5px;font-weight:700;border-radius:999px;padding:5px 12px}
.chip b{font-variant-numeric:tabular-nums}
.chip.grijs{background:var(--cream);color:var(--ink);border:1px solid var(--line)}
.rij{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:7px 0;border-bottom:1px solid var(--line);font-size:13.5px;color:inherit;text-decoration:none}
.rij:last-of-type{border-bottom:0}
.rij.klik:hover b{color:var(--coral)}
.bedrag{font-weight:700;font-variant-numeric:tabular-nums}
.bedrag.rood{color:var(--coral-d)}
.fout{color:#b3261e}
.stil{color:var(--grey);font-size:13px}
</style>
