<script setup>
// Beloningen-pagina (v71): partner ziet de eigen niveau-kaart + spaarcadeaus;
// AM/kantoor ziet per winkel niveau, status en het aantal vrijgespeelde
// beloningen. De drempels zelf zijn commercieel beleid en leven in
// modules/beloningen/logic.js (zoals in v71 — aanpassen = besluit kantoor).
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { eur0 } from '../../../lib/format.js'
import { levelOf, statusKey, STATUS, jaaromzet } from '../../rekenhart/logic.js'
import { REWARDS } from '../logic.js'
import { haalRekenConfig } from '../api.js'
import BeloningBlok from '../components/BeloningBlok.vue'

const auth = useAuth()
const st = useTappunten()
const fout = ref('')
const marge = ref(1)
// Eigen winkel lokaal bijhouden: het blok geeft bij een uitkering de nieuwe
// versie terug via @bijgewerkt — niet opnieuw laden, anders draait de engine
// op verse (oude) data nóg een keer.
const eigen = ref(null)

onMounted(async () => {
  try {
    if (!st.items.length) await st.laad()
    if (auth.isPartner) eigen.value = st.items[0] || null
    marge.value = (await haalRekenConfig()).marge
  } catch (e) { fout.value = 'Kon beloningen niet laden: ' + e.message }
})

const perWinkel = computed(() => st.items.map(t => {
  const lv = levelOf(jaaromzet(t), marge.value)
  const s = STATUS[statusKey(t, marge.value)] || STATUS.groeit
  const gewonnen = Object.keys(t.beloond || {}).length
  return { t, lv, s, gewonnen }
}).sort((a, b) => jaaromzet(b.t) - jaaromzet(a.t)))
</script>

<template>
  <div>
    <h1>Beloningen</h1>
    <p class="sub" v-if="auth.isPartner">Vijf spaarcadeaus — eerst leren, dan verdienen. De balkjes laten je zwakste schakel zien.</p>
    <p class="sub" v-else>Per winkel: niveau (op winkelomzet), situatie en vrijgespeelde beloningen. De uitkering regel je zelf met de winkel.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Partner: eigen winkel, volledige engine -->
    <BeloningBlok v-if="auth.isPartner && eigen" :tappunt="eigen" @bijgewerkt="eigen = $event" />

    <!-- AM/kantoor: overzicht per winkel -->
    <div v-if="!auth.isPartner" class="kaart">
      <h2>Winkels & niveaus</h2>
      <router-link v-for="r in perWinkel" :key="r.t.snelstart" class="rij klik" data-test="winkel-niveau"
                   :to="{ name: 'winkel', params: { code: r.t.snelstart } }">
        <span class="niveau">{{ r.lv.k }}</span>
        <b>{{ r.t.name }}</b>
        <span class="badge" :style="{ background: r.s.bg, color: r.s.fg }">{{ r.s.l }}</span>
        <span class="mo">{{ eur0(r.t.jaaromzet) }} inkoop</span>
        <span class="mo won" :data-test="'won-' + r.t.snelstart">🎁 {{ r.gewonnen }}/{{ REWARDS.length + 2 }}</span>
      </router-link>
      <p v-if="!perWinkel.length" class="stil">Geen winkels.</p>
      <p class="mo uitleg">🎁 = vrijgespeelde beloningen (5 spaarcadeaus + de A+/A++-korting). Open de winkel voor de details.</p>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 10px;font-size:15px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.rij{display:flex;align-items:center;gap:12px;padding:9px 0;border-bottom:1px solid var(--line);font-size:14px;color:inherit;text-decoration:none}
.rij:last-child{border-bottom:0}
.rij.klik:hover b{color:var(--coral)}
.niveau{width:30px;height:30px;border-radius:9px;background:var(--coral);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:12.5px;flex-shrink:0}
.badge{font-size:11px;font-weight:800;border-radius:6px;padding:2px 9px}
.mo{color:var(--grey);font-size:12.5px}
.mo.won{margin-left:auto;font-weight:700}
.uitleg{margin-top:10px}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
