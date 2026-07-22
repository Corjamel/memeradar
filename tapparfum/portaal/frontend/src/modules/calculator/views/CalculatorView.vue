<script setup>
// Calculator — rekent vrij; pas bij "Vastleggen" wordt er iets op de winkel
// geschreven (t.be / t.goal / t.pakket / t.doel, exact de v71-velden).
import { computed, onMounted, reactive, ref } from 'vue'
import { useTappunten } from '../../tappunten/store.js'
import { PKG, beModel, goalModel } from '../logic.js'
import { eur0 } from '../../../lib/format.js'

const st = useTappunten()
const tab = ref('terug')          // 'terug' | 'doel'
const winkel = ref('')
const melding = ref('')
const fout = ref('')
const sel = reactive({ pkg: 0, type: 'std', mode: 'bottle', size: '50', rate: 25, doel: 15000, refills: 8 })

onMounted(async () => { if (!st.items.length) await st.laad() })

const be = computed(() => beModel(sel))
const goal = computed(() => goalModel({ doel: +sel.doel || 0, refills: +sel.refills || 0, type: sel.type, size: sel.size }))

async function vastleggen() {
  fout.value = ''; melding.value = ''
  const t = st.byCode(winkel.value)
  if (!t) { fout.value = 'Kies eerst een winkel om op vast te leggen.'; return }
  try {
    if (tab.value === 'terug') {
      const m = be.value
      await st.bewaar({ ...t, pakket: String(sel.pkg), be: { inv: m.inv, rev: m.rev, perWk: m.perWk, days: m.days, bottles: m.bottles } })
      melding.value = `✓ Break-even-plan vastgelegd op ${t.name}: ${m.bottles} flessen in ±${m.days} dagen.`
    } else {
      const g = goal.value
      await st.bewaar({ ...t, doel: g.doel, goal: { doel: g.doel, klanten: g.klanten, flWeek: g.flWeek, flJaar: g.flJaar, flDag: g.flDag, refills: g.refills } })
      melding.value = `✓ Jaardoel vastgelegd op ${t.name}: ${eur0(g.doel)} → ±${g.flWeek} flessen per week.`
    }
  } catch (e) { fout.value = 'Vastleggen mislukt: ' + e.message }
}
</script>

<template>
  <div>
    <h1>Calculator</h1>
    <p class="sub">Reken het verhaal vóór het gesprek: terugverdientijd van een pakket, of het klant- en flessentempo voor een jaardoel.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <p v-if="melding" class="ok" role="status">{{ melding }}</p>

    <div class="tabs">
      <button type="button" :class="{ aan: tab === 'terug' }" data-test="tab-terug" @click="tab = 'terug'">💶 Terugverdienen</button>
      <button type="button" :class="{ aan: tab === 'doel' }" data-test="tab-doel" @click="tab = 'doel'">🎯 Jaardoel</button>
    </div>

    <!-- gedeelde keuzes -->
    <div class="kaart vorm">
      <div class="rij">
        <label v-if="tab === 'terug'">Pakket
          <select v-model.number="sel.pkg" data-test="calc-pakket">
            <option v-for="(p, i) in PKG" :key="p.n" :value="i">{{ p.n }} — {{ eur0(p.inv) }}</option>
          </select>
        </label>
        <label>Lijn
          <select v-model="sel.type" data-test="calc-type">
            <option value="std">Standaard</option>
            <option value="excl">Exclusive</option>
          </select>
        </label>
        <label v-if="tab === 'terug'">Soort
          <select v-model="sel.mode">
            <option value="bottle">Fles</option>
            <option value="refill">Refill</option>
          </select>
        </label>
        <label>Maat
          <select v-model="sel.size" data-test="calc-maat">
            <option value="30">30ml</option>
            <option value="50">50ml</option>
            <option value="100">100ml</option>
          </select>
        </label>
        <label v-if="tab === 'terug'">Tempo (flessen/week)
          <input v-model.number="sel.rate" type="number" min="1" data-test="calc-rate" />
        </label>
        <label v-if="tab === 'doel'">Jaardoel (€)
          <input v-model.number="sel.doel" type="number" min="0" data-test="calc-doel" />
        </label>
        <label v-if="tab === 'doel'">Refills per klant/jaar
          <input v-model.number="sel.refills" type="number" min="0" data-test="calc-refills" />
        </label>
      </div>
    </div>

    <!-- resultaat -->
    <div v-if="tab === 'terug'" class="kaart resultaat" data-test="res-terug">
      <div class="groot"><b data-test="be-bottles">{{ be.bottles }}</b><span>flessen tot break-even</span></div>
      <div class="groot"><b data-test="be-days">{{ be.days }}</b><span>dagen bij {{ be.perWk }}/week</span></div>
      <p class="uitleg">Investering {{ eur0(be.inv) }} ÷ {{ eur0(be.rev) }} omzet per fles = <b>{{ be.bottles }} flessen</b>. In dit tempo is dat ≈ <b>{{ Math.round(be.days / 7) }} weken</b>.</p>
    </div>
    <div v-else class="kaart resultaat" data-test="res-doel">
      <div class="groot"><b data-test="goal-klanten">{{ goal.klanten }}</b><span>vaste klanten nodig</span></div>
      <div class="groot"><b data-test="goal-flweek">{{ goal.flWeek }}</b><span>flessen per week</span></div>
      <p class="uitleg">Elke klant koopt 1 fles + {{ goal.refills }} refills = <b>{{ eur0(goal.revKlant) }}</b> per jaar. Voor {{ eur0(goal.doel) }} heb je ≈ <b>{{ goal.klanten }} klanten</b> nodig — samen <b>{{ goal.flJaar }} flessen per jaar</b> (≈ {{ goal.flDag }} per dag).</p>
    </div>

    <!-- vastleggen op winkel -->
    <div class="kaart vastleg">
      <label>Vastleggen op winkel
        <select v-model="winkel" data-test="calc-winkel">
          <option value="">— kies winkel (optioneel) —</option>
          <option v-for="t in st.items" :key="t.snelstart" :value="t.snelstart">{{ t.name }}</option>
        </select>
      </label>
      <button class="btn" type="button" data-test="calc-vastleggen" @click="vastleggen">
        {{ tab === 'terug' ? 'Break-even-plan vastleggen' : 'Jaardoel vastleggen' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.tabs{display:flex;gap:8px;margin-bottom:12px}
.tabs button{background:#fff;border:1.5px solid var(--line);border-radius:10px;padding:9px 16px;font-weight:800;font-size:13.5px;color:var(--grey);cursor:pointer}
.tabs button.aan{border-color:var(--coral);background:var(--soft);color:var(--coral-d)}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.rij{display:flex;gap:12px;flex-wrap:wrap}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:150px}
select,input{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
select:focus,input:focus{border-color:var(--coral)}
.resultaat{display:flex;gap:18px;flex-wrap:wrap;align-items:center}
.groot{display:flex;flex-direction:column;gap:2px;min-width:130px}
.groot b{font-size:30px;color:var(--coral-d);font-variant-numeric:tabular-nums}
.groot span{font-size:12px;color:var(--grey);font-weight:700}
.uitleg{flex:1;min-width:240px;margin:0;font-size:13.5px;color:var(--grey)}
.vastleg{display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap}
.vastleg label{max-width:320px}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer}
.btn:hover{background:var(--coral-d)}
.fout{color:#b3261e}
.ok{color:#2c5a12;background:#f4faf0;border-radius:8px;padding:8px 10px;font-size:13.5px}
</style>
