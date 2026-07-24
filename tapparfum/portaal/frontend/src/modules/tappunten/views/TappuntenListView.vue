<script setup>
// Winkels — voor partners een directe doorverwijzing naar de eigen winkel;
// voor AM/kantoor de cockpit uit v71: KPI-rij, filterchips en kaarten
// gegroepeerd op situatie (statusKey), elk met niveau, omzet, groei en de
// eerstvolgende actie.
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTappunten } from '../store.js'
import { useAuth } from '../../../stores/auth.js'
import { useToast } from '../../../stores/toast.js'
import { eur0 } from '../../../lib/format.js'
import { statusKey, STATUS, levelOf, jaaromzet, beDone, groeiTxt } from '../../rekenhart/logic.js'
import { omzetGroei } from '../../punten/logic.js'
import { setupComplete } from '../../setup/logic.js'
import { haalRekenConfig } from '../../beloningen/api.js'

const st = useTappunten()
const auth = useAuth()
const toast = useToast()
const router = useRouter()
const zoek = ref('')

// Nieuwe winkel toevoegen (v71 addClient). Kantoor mag altijd; een AM voegt toe
// in zijn EIGEN portefeuille — de database (RLS + guard, migratie 015) forceert
// am_id server-side, dus de browser bepaalt dat niet.
const nieuwOpen = ref(false)
const nieuw = reactive({ name: '', snelstart: '', plaats: '' })
const bezigNieuw = ref(false)
const foutNieuw = ref('')
async function winkelToevoegen() {
  if (bezigNieuw.value) return
  foutNieuw.value = ''
  if (!nieuw.name.trim()) { foutNieuw.value = 'Vul een winkelnaam in.'; return }
  const code = (nieuw.snelstart.trim() || ('w-' + Math.random().toString(36).slice(2, 7))).toLowerCase()
  if (st.items.some(t => String(t.snelstart).toLowerCase() === code)) { foutNieuw.value = 'Deze snelstartcode bestaat al.'; return }
  bezigNieuw.value = true
  const dag = new Date().toISOString().slice(0, 10)
  const t = {
    snelstart: code, name: nieuw.name.trim(), plaats: nieuw.plaats.trim(), land: 'NL',
    liveDate: dag, traject: false, jaaromzet: 0, joLog: [], vorigJaar: 0, klanten: 0, doel: 0,
    setup: { done: {}, skipped: true }, forms: {}, react: [], logboek: [], afspraken: [],
    flesLog: [], verkopen: {}, bron: 'am'
  }
  try {
    await st.bewaar(t)
    await st.laad()
    toast.ok(`Winkel "${t.name}" toegevoegd`)
    nieuw.name = ''; nieuw.snelstart = ''; nieuw.plaats = ''; nieuwOpen.value = false
    router.push({ name: 'winkel', params: { code } })
  } catch (e) {
    foutNieuw.value = 'Toevoegen mislukt: ' + e.message
  }
  bezigNieuw.value = false
}
const filter = ref('alle')
const marge = ref(1)

// v71-volgorde: eerst wat aandacht vraagt.
const ORDER = [
  ['stagneert', '⚠ Stagneert'], ['nieuw', '🌱 Nieuw'],
  ['groeit', '📈 Groeit'], ['top', '🏆 Top']
]

onMounted(async () => {
  if (!st.items.length) await st.laad()
  if (auth.isPartner && st.items.length === 1) {
    router.replace({ name: 'winkel', params: { code: st.items[0].snelstart } })
    return
  }
  try { marge.value = (await haalRekenConfig()).marge } catch { /* factor 1 */ }
})

function info(t) {
  return {
    status: statusKey(t, marge.value),
    lv: levelOf(jaaromzet(t), marge.value).k,
    jo: jaaromzet(t),
    g: omzetGroei(t)
  }
}
function nextStep(t) {
  if (!setupComplete(t)) return 'Opstart afronden met de winkel'
  if (t.be && !beDone(t)) return 'Naar break-even — houd het weektempo vast'
  const s = statusKey(t, marge.value)
  if (s === 'stagneert') return 'Bel + check voorraad/presentatie, zet een actie in'
  if (s === 'top') return 'Belonen & opschalen (meer geuren / Exclusive)'
  return 'Sturen op het jaardoel met een positieve actie'
}

const gezocht = computed(() => {
  const q = zoek.value.trim().toLowerCase()
  if (!q) return st.items
  return st.items.filter(t =>
    (t.name || '').toLowerCase().includes(q) ||
    (t.snelstart || '').toLowerCase().includes(q) ||
    (t.plaats || '').toLowerCase().includes(q))
})

const tellingen = computed(() => {
  const c = { alle: gezocht.value.length, nieuw: 0, groeit: 0, stagneert: 0, top: 0 }
  gezocht.value.forEach(t => { c[statusKey(t, marge.value)]++ })
  return c
})

const zichtbaar = computed(() => filter.value === 'alle'
  ? gezocht.value
  : gezocht.value.filter(t => statusKey(t, marge.value) === filter.value))

const perStatus = computed(() => ORDER.map(([k, lbl]) => ({
  k, lbl,
  items: zichtbaar.value.filter(t => statusKey(t, marge.value) === k)
    .sort((a, b) => jaaromzet(b) - jaaromzet(a))
})).filter(g => g.items.length))

// KPI's
const omzetTot = computed(() => gezocht.value.reduce((s, t) => s + jaaromzet(t), 0))
const aKlanten = computed(() => gezocht.value.filter(t => ['A', 'A+', 'A++'].includes(levelOf(jaaromzet(t), marge.value).k)).length)
const groei = computed(() => {
  let nu = 0, vj = 0
  gezocht.value.forEach(t => { const g = omzetGroei(t); if (g != null) { nu += jaaromzet(t); vj += (+t.vorigJaar || 0) } })
  return vj > 0 ? Math.round((nu - vj) / vj * 100) : null
})

function open(t) { router.push({ name: 'winkel', params: { code: t.snelstart } }) }
</script>

<template>
  <div>
    <div class="kop">
      <h1>Winkels</h1>
      <input v-model="zoek" class="zoek" type="search" placeholder="Zoek op naam, code of plaats…" data-test="winkel-zoek" />
      <button v-if="!auth.isPartner" class="nieuwknop" type="button" data-test="winkel-nieuw-knop"
              @click="nieuwOpen = !nieuwOpen">{{ nieuwOpen ? '× Sluiten' : '+ Nieuwe winkel' }}</button>
    </div>

    <!-- Nieuwe winkel (kantoor + AM). Een AM voegt toe in zijn eigen portefeuille. -->
    <form v-if="!auth.isPartner && nieuwOpen" class="nieuwvorm" data-test="winkel-nieuw-vorm" @submit.prevent="winkelToevoegen">
      <label>Winkelnaam<input v-model="nieuw.name" required placeholder="Bijv. Parfumerie Kampen" data-test="nieuw-naam" /></label>
      <label>Snelstartcode<input v-model="nieuw.snelstart" placeholder="bijv. kl-30 (leeg = automatisch)" data-test="nieuw-snelstart" /></label>
      <label>Plaats<input v-model="nieuw.plaats" placeholder="bijv. Kampen" data-test="nieuw-plaats" /></label>
      <button class="knop" type="submit" :disabled="bezigNieuw" data-test="nieuw-opslaan">{{ bezigNieuw ? 'Bezig…' : 'Winkel toevoegen' }}</button>
      <p v-if="foutNieuw" class="fout" role="alert" data-test="nieuw-fout">{{ foutNieuw }}</p>
      <p v-else class="hint">{{ auth.isKantoor ? 'Wijs de winkel daarna toe aan een accountmanager in Beheer.' : 'De winkel komt automatisch in jouw portefeuille.' }}</p>
    </form>
    <p v-if="st.fout" class="fout" role="alert">{{ st.fout }}</p>
    <p v-else-if="st.laden" class="stil">Laden…</p>

    <template v-else>
      <!-- KPI-rij -->
      <div class="kpis">
        <div class="kpi"><b>{{ gezocht.length }}</b><span>winkels</span></div>
        <div class="kpi"><b>{{ aKlanten }}</b><span>A-klanten</span></div>
        <div class="kpi"><b>{{ eur0(omzetTot) }}</b><span>jaaromzet</span></div>
        <div class="kpi"><b :class="groei != null && groei < 0 ? 'rood' : 'groen'">{{ groei == null ? '—' : (groei >= 0 ? '+' : '') + groei + '%' }}</b><span>portfolio-groei</span></div>
      </div>

      <!-- Filterchips -->
      <div class="chips">
        <button v-for="[k, lbl] in [['alle','Alle'], ...ORDER]" :key="k" class="chip"
                :class="{ aan: filter === k }" type="button" :data-test="'filter-' + k" @click="filter = k">
          {{ lbl }} <span class="n">{{ tellingen[k] }}</span>
        </button>
      </div>

      <p v-if="!zichtbaar.length" class="stil">Geen winkels in deze selectie.</p>

      <!-- Gegroepeerd op status -->
      <section v-for="g in perStatus" :key="g.k" class="groep">
        <h2 :data-test="'groep-' + g.k"><span class="stip" :style="{ background: STATUS[g.k].bg }"></span>{{ g.lbl }} <span class="mo">· {{ g.items.length }}</span></h2>
        <button v-for="t in g.items" :key="t.snelstart" class="kaart" data-test="tappunt-rij" @click="open(t)">
          <span class="niveau">{{ info(t).lv }}</span>
          <div class="mid">
            <div class="rij1"><b class="nm">{{ t.name }}</b>
              <span class="badge" :style="{ background: STATUS[info(t).status].bg, color: STATUS[info(t).status].fg }">{{ STATUS[info(t).status].l }}</span>
              <span v-if="t.geblokkeerd" class="badge zwart">geblokkeerd</span>
            </div>
            <div class="rij2 mo">{{ t.snelstart }}<template v-if="t.plaats"> · {{ t.plaats }}</template> · {{ eur0(info(t).jo) }}<template v-if="info(t).g != null"> · groei <b class="coral">{{ groeiTxt(info(t).g) }}</b></template></div>
            <div class="ns">→ {{ nextStep(t) }}</div>
          </div>
        </button>
      </section>
    </template>
  </div>
</template>

<style scoped>
.kop{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:14px}
.nieuwknop{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 15px;font-weight:800;font-size:13px;cursor:pointer;white-space:nowrap}
.nieuwknop:hover{background:var(--coral-d)}
.nieuwvorm{display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap;background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:14px}
.nieuwvorm label{display:flex;flex-direction:column;gap:4px;font-size:12px;font-weight:700;color:var(--grey)}
.nieuwvorm input{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:13.5px;color:var(--ink);min-width:170px}
.nieuwvorm .knop{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;font-size:13px;cursor:pointer}
.nieuwvorm .knop:disabled{opacity:.5;cursor:default}
.nieuwvorm .hint{font-size:12px;color:var(--grey);margin:0;flex-basis:100%}
.nieuwvorm .fout{flex-basis:100%;margin:0}
h1{margin:0;font-size:22px}
h2{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--grey);margin:18px 0 8px}
.stip{width:11px;height:11px;border-radius:50%}
.zoek{flex:1;min-width:220px;max-width:340px;padding:9px 12px;border:1.5px solid var(--line);border-radius:10px;font-size:14px}
.zoek:focus{border-color:var(--coral)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:12px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 14px}
.kpi b{display:block;font-size:20px;color:var(--coral);font-variant-numeric:tabular-nums}
.kpi b.groen{color:var(--green)}
.kpi b.rood{color:var(--coral-d)}
.kpi span{font-size:12px;color:var(--grey);font-weight:700}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px}
.chip{background:#fff;border:1.5px solid var(--line);border-radius:999px;padding:6px 13px;font-size:12.5px;font-weight:700;color:var(--grey);cursor:pointer}
.chip.aan{border-color:var(--coral);background:var(--soft);color:var(--coral-d)}
.chip .n{font-variant-numeric:tabular-nums;opacity:.8}
.kaart{display:flex;align-items:center;gap:12px;width:100%;text-align:left;background:#fff;border:1px solid var(--line);border-radius:12px;padding:11px 14px;cursor:pointer;margin-bottom:8px}
.kaart:hover{border-color:var(--coral)}
.niveau{width:34px;height:34px;flex-shrink:0;border-radius:10px;background:var(--coral);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:13px}
.mid{min-width:0;flex:1}
.rij1{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.nm{font-weight:700}
.badge{font-size:11px;font-weight:800;border-radius:6px;padding:2px 8px}
.badge.zwart{background:#333;color:#fff}
.rij2{margin-top:2px}
.mo{color:var(--grey);font-size:12.5px}
.coral{color:var(--coral)}
.ns{margin-top:3px;font-size:12px;color:var(--coral-d);font-weight:600}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
