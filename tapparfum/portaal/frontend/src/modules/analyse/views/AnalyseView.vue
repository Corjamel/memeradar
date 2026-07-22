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
import { statusKey, STATUS, jaaromzet } from '../../rekenhart/logic.js'
import { inTraject } from '../../beloningen/logic.js'
import { dagenSindsBestelling } from '../../bestellingen/logic.js'
import { haalRekenConfig } from '../../beloningen/api.js'

const auth = useAuth()
const st = useTappunten()
const ams = ref([])
const marge = ref(1)
const fout = ref('')

onMounted(async () => {
  try {
    if (!st.items.length) await st.laad()
    if (auth.isKantoor) ams.value = await haalAms()
    marge.value = (await haalRekenConfig()).marge
  } catch (e) { fout.value = 'Kon de analyse niet laden: ' + e.message }
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
    <h1>📊 Analyse</h1>
    <p class="sub">Het netwerk in cijfers — sturen op feiten. Bedragen = inkoop bij TapParfum; kassa = geregistreerde winkelverkoop.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

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
