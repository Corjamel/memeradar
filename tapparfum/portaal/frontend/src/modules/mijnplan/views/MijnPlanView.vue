<script setup>
// Mijn plan (v71 VIEWS.mijnplan, r.3357-3370) — de partner ziet hier het plan
// dat de accountmanager met de calculator heeft vastgelegd: het terugverdien-
// plan (t.be) en het jaardoel (t.goal), elk met de eigen voortgang in flessen.
import { computed, onMounted } from 'vue'
import { useTappunten } from '../../tappunten/store.js'
import { flessenVerkocht, beDone } from '../../rekenhart/logic.js'
import { eur0 } from '../../../lib/format.js'

const st = useTappunten()
onMounted(async () => { if (!st.items.length) await st.laad() })
const t = computed(() => st.items[0] || null)

const sold = computed(() => t.value ? flessenVerkocht(t.value) : 0)
const be = computed(() => (t.value && t.value.be) || null)
const bePct = computed(() => be.value ? Math.min(Math.round(sold.value / be.value.bottles * 100), 100) : 0)
const beDatum = computed(() => {
  if (!be.value || !t.value) return ''
  const start = t.value.liveDate ? new Date(t.value.liveDate) : new Date()
  start.setDate(start.getDate() + (be.value.days || 0))
  return start.toLocaleDateString('nl-NL', { day: 'numeric', month: 'long', year: 'numeric' })
})
const goal = computed(() => {
  const g = t.value && t.value.goal
  return g && g.doel > 0 ? g : null
})
const goalPct = computed(() => (goal.value && goal.value.flJaar)
  ? Math.min(Math.round(sold.value / goal.value.flJaar * 100), 100) : 0)

// Weektempo-schema ma-vr (v71 weekGridHTML): tempo eerlijk over 5 dagen.
const DAGEN = ['ma', 'di', 'wo', 'do', 'vr']
function schema(perWk) {
  const wk = Math.max(1, Math.round(perWk || 0))
  const basis = Math.floor(wk / 5), rest = wk % 5
  const kol = DAGEN.map((d, i) => ({ d, n: basis + (i < rest ? 1 : 0) }))
  const max = Math.max(...kol.map(x => x.n), 1)
  return kol.map(x => ({ ...x, h: Math.max(8, x.n / max * 52) }))
}
</script>

<template>
  <div>
    <header class="vheld"><div>
      <p class="eyebrow">Jouw route</p>
      <h1>Mijn plan</h1>
      <p class="sub">Dit plan stelt je accountmanager op met de calculator. Hier zie je het terug — en hoe ver je bent.</p>
    </div></header>

    <p v-if="!t" class="stil">Geen winkel gevonden.</p>
    <template v-else>
      <!-- Terugverdienen -->
      <div class="kaart" data-test="plan-be">
        <div class="zh">Terugverdienen</div>
        <template v-if="be">
          <p class="regel">Investering <b>{{ eur0(be.inv) }}</b> · terugverdiend na <b>{{ be.bottles }} flessen</b>
            (≈ {{ be.days }} dagen · streefdatum <b>{{ beDatum }}</b>).</p>
          <div class="binfo"><span class="sterk" data-test="be-stand">{{ sold }} / {{ be.bottles }} flessen</span>
            <span class="mo">{{ bePct }}%{{ beDone(t) ? ' · terugverdiend ✓' : (sold < be.bottles ? ` · nog ${be.bottles - sold}` : '') }}</span></div>
          <div class="balk"><div class="vul" :class="{ af: beDone(t) }" :style="{ width: bePct + '%' }"></div></div>
          <div class="weekgrid" aria-label="Flessen per werkdag">
            <div v-for="d in schema(be.perWk)" :key="d.d" class="wkol">
              <span class="wn">{{ d.n }}</span><span class="wbar" :style="{ height: d.h + 'px' }"></span><span class="wd">{{ d.d }}</span>
            </div>
          </div>
          <p class="mo">Tempo: ± <b>{{ be.perWk }} flessen per week</b>.</p>
        </template>
        <p v-else class="mo">Je accountmanager bepaalt je terugverdienplan met de calculator.</p>
      </div>

      <!-- Jaardoel -->
      <div class="kaart" data-test="plan-goal">
        <div class="zh">Jaardoel</div>
        <template v-if="goal">
          <p class="regel">Doel <b>{{ eur0(goal.doel) }}</b> · nodig: <b>{{ goal.klanten }} vaste klanten</b> en
            <b>{{ goal.flWeek }} flessen/week</b> ({{ goal.flJaar }} per jaar).</p>
          <div class="binfo"><span class="sterk" data-test="goal-stand">{{ sold }} / {{ goal.flJaar }} flessen dit jaar</span>
            <span class="mo">{{ goalPct }}%</span></div>
          <div class="balk"><div class="vul af" :style="{ width: goalPct + '%' }"></div></div>
          <div class="weekgrid" aria-label="Flessen per werkdag voor het jaardoel">
            <div v-for="d in schema(goal.flWeek)" :key="d.d" class="wkol">
              <span class="wn">{{ d.n }}</span><span class="wbar" :style="{ height: d.h + 'px' }"></span><span class="wd">{{ d.d }}</span>
            </div>
          </div>
        </template>
        <p v-else class="mo">Je jaardoel komt in beeld zodra je tappunt loopt en is terugverdiend.</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
h1{margin:0;font-size:22px}
.sub{color:var(--grey);margin:0;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 20px;margin-bottom:12px}
.zh{font-size:12px;text-transform:uppercase;letter-spacing:1px;color:var(--coral);font-weight:800;margin-bottom:8px}
.regel{margin:0 0 10px;font-size:13.5px;line-height:1.55}
.binfo{display:flex;justify-content:space-between;gap:10px;align-items:baseline;margin-bottom:5px}
.sterk{font-weight:800;font-size:14px;font-variant-numeric:tabular-nums}
.mo{color:var(--grey);font-size:12.5px;margin:6px 0 0}
.balk{height:10px;border-radius:6px;background:#f0ebe3;overflow:hidden}
.vul{height:100%;background:linear-gradient(90deg,var(--peach),var(--coral))}
.vul.af{background:linear-gradient(90deg,#7fb05a,var(--green))}
.weekgrid{display:flex;gap:16px;align-items:flex-end;height:80px;padding:0 2px;margin-top:14px}
.wkol{display:flex;flex-direction:column;align-items:center;gap:3px;justify-content:flex-end}
.wn{font-size:12px;font-weight:800;font-variant-numeric:tabular-nums}
.wbar{width:30px;border-radius:6px 6px 0 0;background:linear-gradient(180deg,var(--coral),var(--peach))}
.wd{font-size:10.5px;color:var(--grey);font-weight:700;text-transform:uppercase}
.stil{color:var(--grey)}
</style>
