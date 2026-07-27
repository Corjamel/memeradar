<script setup>
// Trajecten / heractiveren — v71 VIEWS.heractiveren (r.3011-3016): elke winkel
// zit op basis van zijn status in één van vier trajecten, elk met een eigen
// focus en actielijst. Stagneert = de heractivatie-werklijst (t.react).
import Icoon from '../../../components/Icoon.vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useTappunten } from '../../tappunten/store.js'
import { eur0 } from '../../../lib/format.js'
import { statusKey, STATUS, levelOf, jaaromzet, beDone, groeiTxt } from '../../rekenhart/logic.js'
import { omzetGroei } from '../../punten/logic.js'
import { inTraject } from '../../beloningen/logic.js'
import { haalRekenConfig } from '../../beloningen/api.js'
import { TRAJ, reactToevoegen, reactDone } from '../logic.js'

const st = useTappunten()
const marge = ref(1)
const fout = ref('')
const bezig = ref(false)
const invoer = reactive({})      // per winkel: { actie, opvolg }
const tdef = new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10)

onMounted(async () => {
  try {
    if (!st.items.length) await st.laad()
    marge.value = (await haalRekenConfig()).marge
  } catch (e) { fout.value = 'Kon trajecten niet laden: ' + e.message }
})

/* Eén statusKey-pass: bucket per traject, gesorteerd op jaaromzet (v71). */
const perTraject = computed(() => {
  const byK = Object.fromEntries(TRAJ.map(tr => [tr.k, []]))
  st.items.filter(inTraject).forEach(t => {
    const b = byK[statusKey(t, marge.value)]
    if (b) b.push(t)
  })
  TRAJ.forEach(tr => byK[tr.k].sort((a, b) => jaaromzet(b) - jaaromzet(a)))
  return byK
})

function info(t) {
  return { lv: levelOf(jaaromzet(t), marge.value).k, jo: jaaromzet(t), g: groeiTxt(omzetGroei(t)) }
}

async function bewaar(t2) {
  bezig.value = true; fout.value = ''
  try { await st.bewaar(t2); const i = st.items.findIndex(x => x.snelstart === t2.snelstart); if (i >= 0) st.items[i] = t2 }
  catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function vastleggen(t) {
  const inv = invoer[t.snelstart] || {}
  const t2 = reactToevoegen(t, inv.actie, inv.opvolg || tdef)
  if (!t2) { fout.value = 'Kies eerst een actie.'; return }
  await bewaar(t2)
  delete invoer[t.snelstart]
}

async function vink(t, idx, v) { await bewaar(reactDone(t, idx, v)) }
function scrollNaar(k) { document.getElementById('traj-' + k)?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }
</script>

<template>
  <div>
    <header class="vheld"><div>
      <p class="eyebrow">Groei</p>
      <h1><Icoon naam="spark" /> Trajecten</h1>
      <p class="sub">Elke winkel zit in één van vier trajecten — met per traject een eigen focus. Stagneert = jouw prioriteit.</p>
    </div></header>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- KPI-tegels -->
    <div class="tegels">
      <button v-for="tr in TRAJ" :key="tr.k" class="tegel" type="button" :style="{ borderTopColor: tr.col }"
              :data-test="'traj-tegel-' + tr.k" @click="scrollNaar(tr.k)">
        <div class="cijfer" :style="{ color: tr.col }">{{ perTraject[tr.k].length }}</div>
        <div class="lbl">{{ STATUS[tr.k].l }}</div>
        <div class="foc">{{ tr.foc }}</div>
      </button>
    </div>

    <!-- Groepen -->
    <details v-for="tr in TRAJ" :key="tr.k" :id="'traj-' + tr.k" class="groep" open :style="{ borderLeftColor: tr.col }">
      <summary>
        <span class="stip" :style="{ background: tr.col }"></span>
        <b>{{ STATUS[tr.k].l }}</b>
        <span class="teller" :style="{ background: tr.col }">{{ perTraject[tr.k].length }}</span>
        <span class="mo">{{ tr.foc }}</span>
      </summary>
      <p class="mo uitleg">{{ tr.desc }}</p>
      <p v-if="!perTraject[tr.k].length" class="stil">Geen winkels in dit traject.</p>

      <div v-for="t in perTraject[tr.k]" :key="t.snelstart" class="winkel" :data-test="'traj-' + tr.k + '-' + t.snelstart">
        <div class="wkop">
          <b>{{ t.name }}</b><span class="mo">Niveau {{ info(t).lv }}</span>
          <span class="mo rechts">{{ eur0(info(t).jo) }} · groei <b class="coral">{{ info(t).g }}</b></span>
        </div>

        <!-- nieuw: break-even-info -->
        <p v-if="tr.k === 'nieuw'" class="mo">
          {{ t.be ? `Break-even: ${t.be.bottles} flessen · ${t.be.days} dgn${beDone(t) ? ' · ✓ terugverdiend' : ''}` : 'Nog geen break-evenplan — open de calculator.' }}
        </p>

        <!-- overige trajecten: actie vastleggen -->
        <div v-else class="actierij">
          <select v-model="(invoer[t.snelstart] ||= { actie: '', opvolg: tdef }).actie" :data-test="'react-actie-' + t.snelstart">
            <option value="" disabled>— kies een actie —</option>
            <option v-for="a in tr.acties" :key="a">{{ a }}</option>
          </select>
          <input v-model="(invoer[t.snelstart] ||= { actie: '', opvolg: tdef }).opvolg" type="date" :data-test="'react-opvolg-' + t.snelstart" />
          <button class="klein" type="button" :disabled="bezig" :data-test="'react-vastleggen-' + t.snelstart" @click="vastleggen(t)">Vastleggen</button>
          <router-link class="klein" :to="{ name: 'winkel', params: { code: t.snelstart } }">Open →</router-link>
        </div>

        <!-- react-historie -->
        <div v-if="(t.react || []).length" class="reactlijst">
          <label v-for="(r, i) in t.react" :key="i" class="react" :class="{ af: r.done }" :data-test="'react-rij-' + t.snelstart">
            <input type="checkbox" :checked="r.done" :disabled="bezig" :data-test="'react-done-' + t.snelstart + '-' + i"
                   @change="vink(t, i, $event.target.checked)" />
            <span>{{ r.date }} · {{ r.actie }}<i v-if="r.opvolg" class="mo"> → opvolgen {{ r.opvolg }}</i></span>
          </label>
        </div>
      </div>
    </details>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.tegels{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:16px}
.tegel{background:#fff;border:1px solid var(--line);border-top:4px solid var(--line);border-radius:14px;padding:12px 14px;text-align:left;cursor:pointer;font-family:inherit}
.tegel:hover{border-color:var(--coral)}
.cijfer{font-size:24px;font-weight:900;line-height:1}
.lbl{font-size:13px;font-weight:800;margin-top:3px}
.foc{font-size:11.5px;color:var(--grey);margin-top:2px}
.groep{background:#fff;border:1px solid var(--line);border-left:4px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:12px}
summary{display:flex;align-items:center;gap:9px;cursor:pointer;font-size:14.5px;flex-wrap:wrap}
.stip{width:11px;height:11px;border-radius:50%;flex-shrink:0}
.teller{color:#fff;font-size:11.5px;font-weight:800;border-radius:999px;padding:1px 9px}
.mo{color:var(--grey);font-size:12.5px}
.mo.uitleg{margin:8px 0 4px}
.mo.rechts{margin-left:auto}
.coral{color:var(--coral-d)}
.winkel{border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-top:10px}
.wkop{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.actierij{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:10px}
.actierij select{flex:1;min-width:220px}
select,input{padding:8px 10px;border:1.5px solid var(--line);border-radius:9px;font-size:13px;font-family:inherit}
select:focus,input:focus{border-color:var(--coral)}
.klein{background:none;border:1.5px solid var(--line);border-radius:8px;padding:6px 12px;font-size:12.5px;font-weight:700;color:var(--grey);cursor:pointer;text-decoration:none;white-space:nowrap}
.klein:hover{border-color:var(--coral);color:var(--coral-d)}
.reactlijst{margin-top:10px;border-top:1px solid var(--line);padding-top:6px}
.react{display:flex;align-items:flex-start;gap:9px;padding:5px 0;font-size:13px;cursor:pointer}
.react input{width:16px;height:16px;accent-color:var(--coral);margin-top:1px}
.react.af span{color:var(--grey);text-decoration:line-through}
.react i{font-style:normal}
.fout{color:#b3261e}
.stil{color:var(--grey);font-size:13px}
</style>
