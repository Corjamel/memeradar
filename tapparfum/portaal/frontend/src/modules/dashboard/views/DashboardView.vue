<script setup>
// Startscherm per rol: kantoor (netwerk-cockpit), AM (mijn winkels), partner
// (eigen winkel). Alleen weergave — alle data komt RLS-gescoped uit de modules.
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { haalWinkelvragen } from '../../winkelvragen/api.js'
import { haalAgenda } from '../../agenda/api.js'
import { haalRekenConfig } from '../../beloningen/api.js'
import { levelOf, jaaromzet } from '../../rekenhart/logic.js'
import { haalTaken } from '../../taken/api.js'
import { haalAms } from '../api.js'
import { eur0 } from '../../../lib/format.js'
import FlesMeter from '../../../components/FlesMeter.vue'

const auth = useAuth()
const st = useTappunten()
const vragen = ref([])
const agenda = ref([])
const ams = ref([])
const marge = ref(1)
const taken = ref([])
const fout = ref('')

onMounted(async () => {
  try {
    if (!st.items.length) await st.laad()
    ;[vragen.value, agenda.value] = await Promise.all([haalWinkelvragen(), haalAgenda()])
    if (auth.isKantoor) ams.value = await haalAms()
    if (auth.isPartner) marge.value = (await haalRekenConfig()).marge
    else taken.value = await haalTaken()
  } catch (e) { fout.value = 'Kon het overzicht niet volledig laden: ' + e.message }
})

const omzetTot = computed(() => st.items.reduce((s, t) => s + (Number(t.jaaromzet) || 0), 0))
const blok = computed(() => st.items.filter(t => t.geblokkeerd).length)
const openVragen = computed(() => vragen.value.filter(v => v.status === 'open').length)
const openTaken = computed(() => taken.value.filter(t => !t.klaar).length)
const komend = computed(() => agenda.value
  .filter(i => i.status === 'voorgesteld' || i.status === 'geaccepteerd')
  .sort((a, b) => (a.datum < b.datum ? -1 : 1)).slice(0, 3))
const WINKEL = computed(() => Object.fromEntries(st.items.map(t => [t.snelstart, t.name])))
const perAm = computed(() => {
  const naam = Object.fromEntries(ams.value.map(a => [a.id, a.naam]))
  const m = new Map()
  for (const t of st.items) {
    const k = t.am_id || '-'
    if (!m.has(k)) m.set(k, { naam: naam[k] || 'Geen AM', n: 0, omzet: 0 })
    const r = m.get(k); r.n++; r.omzet += Number(t.jaaromzet) || 0
  }
  return [...m.values()].sort((a, b) => b.omzet - a.omzet)
})
const topWinkels = computed(() => [...st.items]
  .sort((a, b) => (Number(b.jaaromzet) || 0) - (Number(a.jaaromzet) || 0)).slice(0, 5))
const eigen = computed(() => st.items[0] || null)
const mijnNiveau = computed(() => eigen.value ? levelOf(jaaromzet(eigen.value), marge.value) : null)
const datum = new Intl.DateTimeFormat('nl-NL', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date())
// Vulmeter (signatuur): voortgang naar het jaardoel, anders naar het volgende niveau.
const meterPct = computed(() => {
  if (!auth.isPartner || !eigen.value) return null
  const jo = Number(eigen.value.jaaromzet) || 0
  const doel = Number(eigen.value.doel) || 0
  if (doel > 0) return Math.min(100, (jo / doel) * 100)
  const lv = mijnNiveau.value
  if (!lv || !lv.nextMin) return null
  return Math.max(0, Math.min(100, ((jo * marge.value - lv.min) / (lv.nextMin - lv.min)) * 100))
})
const meterLabel = computed(() => {
  if (!eigen.value) return ''
  return (Number(eigen.value.doel) || 0) > 0 ? 'van jullie jaardoel'
    : (mijnNiveau.value && mijnNiveau.value.next ? 'naar niveau ' + mijnNiveau.value.next : '')
})
</script>

<template>
  <div>
    <header class="held">
      <div>
        <p class="eyebrow">TapParfum Portaal · {{ datum }}</p>
        <h1>{{ auth.isKantoor ? 'Kantoor-cockpit' : (auth.isAm ? 'Mijn overzicht' : 'Welkom') }}</h1>
      </div>
      <FlesMeter v-if="meterPct != null" :pct="meterPct" :label="meterLabel" />
    </header>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Tegels -->
    <div class="tegels">
      <div class="tegel" data-test="tile-winkels">
        <div class="cijfer">{{ st.items.length }}</div>
        <div class="lbl">{{ auth.isPartner ? 'winkel' : 'winkels' }}</div>
      </div>
      <div class="tegel" data-test="tile-omzet">
        <div class="cijfer">{{ eur0(omzetTot) }}</div>
        <div class="lbl">jaaromzet</div>
      </div>
      <div class="tegel" data-test="tile-open">
        <div class="cijfer">{{ openVragen }}</div>
        <div class="lbl">open meldingen</div>
      </div>
      <router-link v-if="!auth.isPartner" class="tegel klik" data-test="tile-taken" :to="{ name: 'taken' }">
        <div class="cijfer">{{ openTaken }}</div>
        <div class="lbl">open taken</div>
      </router-link>
      <div v-if="auth.isKantoor" class="tegel" data-test="tile-blok">
        <div class="cijfer">{{ blok }}</div>
        <div class="lbl">geblokkeerd</div>
      </div>
    </div>

    <!-- Partner: eigen winkel + niveau -->
    <div v-if="auth.isPartner && eigen" class="kaart" data-test="eigen-kaart">
      <div class="kop"><h2>{{ eigen.name }}</h2><span class="code">code {{ eigen.snelstart }}</span></div>
      <p class="regel">Jaaromzet: <b>{{ eur0(eigen.jaaromzet) }}</b></p>
      <template v-if="mijnNiveau">
        <p class="regel">Niveau:
          <b data-test="niveau-naam">{{ mijnNiveau.k }}</b> — {{ mijnNiveau.r }}
          <template v-if="mijnNiveau.next"> · nog {{ eur0(mijnNiveau.gap) }} tot niveau {{ mijnNiveau.next }}</template>
        </p>
        <div v-if="mijnNiveau.next && meterPct != null" class="balk"><div class="vul" :style="{ width: meterPct + '%' }"></div></div>
      </template>
      <router-link class="link" :to="{ name: 'winkel', params: { code: eigen.snelstart } }">→ Mijn winkelpagina</router-link>
    </div>

    <!-- Kantoor: per accountmanager -->
    <div v-if="auth.isKantoor && perAm.length" class="kaart">
      <h2>Per accountmanager</h2>
      <div v-for="r in perAm" :key="r.naam" class="rij" data-test="am-rij">
        <b>{{ r.naam }}</b>
        <span class="mo">{{ r.n }} winkel{{ r.n === 1 ? '' : 's' }}</span>
        <span class="bedrag">{{ eur0(r.omzet) }}</span>
      </div>
    </div>

    <!-- AM: top-winkels -->
    <div v-if="auth.isAm && topWinkels.length" class="kaart">
      <h2>Jouw winkels (top {{ topWinkels.length }})</h2>
      <router-link v-for="t in topWinkels" :key="t.snelstart" class="rij klik" data-test="top-winkel"
                   :to="{ name: 'winkel', params: { code: t.snelstart } }">
        <b>{{ t.name }}</b>
        <span class="mo">{{ t.snelstart }}</span>
        <span class="bedrag">{{ eur0(t.jaaromzet) }}</span>
      </router-link>
    </div>

    <!-- Iedereen: eerstvolgende bezoeken -->
    <div v-if="komend.length" class="kaart">
      <h2>Eerstvolgend</h2>
      <div v-for="i in komend" :key="i.id" class="rij" data-test="komend-item">
        <b>{{ WINKEL[i.tappunt_snelstart] || i.tappunt_snelstart }}</b>
        <span class="mo">{{ i.type === 'telefoon' ? '📞' : '📍' }} {{ i.datum }}<template v-if="i.tijd"> · {{ i.tijd }}</template></span>
        <span class="mo">{{ i.status === 'voorgesteld' ? 'wacht op winkel' : 'geaccepteerd' }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.held{display:flex;align-items:center;justify-content:space-between;gap:18px;background:linear-gradient(115deg,var(--soft),#fff 72%);border:1px solid var(--line);border-radius:18px;padding:18px 22px;margin-bottom:14px}
.eyebrow{margin:0 0 3px;font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--coral-d)}
h1{margin:0;font-size:24px}
h2{margin:0 0 10px;font-size:15px}
.tegels{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:14px}
.tegel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;color:inherit;text-decoration:none;display:block}
.tegel.klik:hover{border-color:var(--coral)}
.cijfer{font-size:22px;font-weight:800;color:var(--coral)}
.lbl{font-size:12px;color:var(--grey);font-weight:700}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.kop{display:flex;align-items:center;gap:10px}
.code{color:var(--grey);font-size:12.5px}
.regel{margin:6px 0;font-size:14px}
.balk{height:8px;border-radius:6px;background:#f0ebe3;overflow:hidden;margin:8px 0}
.vul{height:100%;background:var(--coral)}
.link{color:var(--coral);font-weight:700;text-decoration:none;font-size:13.5px}
.rij{display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--line);font-size:14px;color:inherit;text-decoration:none}
.rij:last-child{border-bottom:0}
.rij.klik:hover b{color:var(--coral)}
.mo{color:var(--grey);font-size:12.5px}
.bedrag{margin-left:auto;font-weight:700}
.fout{color:#b3261e}
</style>
