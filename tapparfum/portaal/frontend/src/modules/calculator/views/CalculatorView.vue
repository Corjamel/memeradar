<script setup>
// Calculator — het v71-aanzicht: links de knoppen (segmenten + schuif), rechts
// het verhaal met KPI-tegels, de 12-maanden-tijdlijn en het verkoopschema.
// Rekent vrij; pas bij "Vastleggen" wordt er iets op de winkel geschreven
// (t.be / t.goal / t.pakket / t.doel, exact de v71-velden).
import { computed, onMounted, reactive, ref } from 'vue'
import { useTappunten } from '../../tappunten/store.js'
import { PKG, beModel, goalModel, omzetPF } from '../logic.js'
import { eur0 } from '../../../lib/format.js'

const st = useTappunten()
const tab = ref('terug')          // 'terug' | 'doel'
const winkel = ref('')
const melding = ref('')
const fout = ref('')
const sel = reactive({ pkg: 0, type: 'std', mode: 'bottle', size: '50', rate: 25, doel: 15000, refills: 8 })

onMounted(async () => { if (!st.items.length) await st.laad() })

const eur = n => '€ ' + Number(n).toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const be = computed(() => beModel(sel))
const goal = computed(() => goalModel({ doel: +sel.doel || 0, refills: +sel.refills || 0, type: sel.type, size: sel.size }))

// Afgeleiden voor het verhaal en de tijdlijn (v71 calc(), r.3103-3121)
const weken = computed(() => Math.ceil(be.value.bottles / be.value.perWk))
const maanden = computed(() => (be.value.days / 30.44).toFixed(1))
const lijnLabel = computed(() => `${sel.size} ml ${sel.type === 'std' ? 'standaard' : 'Exclusive'}, ${sel.mode === 'bottle' ? 'met flesje' : 'refill'}`)
const frac = computed(() => Math.min(be.value.days / 365, 1))
const winst12 = computed(() => be.value.perWk * 52 * be.value.rev - be.value.inv)
const perDag = computed(() => (be.value.perWk / 5).toFixed(1))
function zetPerDag(v) { sel.rate = Math.max(Math.round((+v || 0) * 5), 1) }

// Verkoopschema ma-vr: het weektempo eerlijk over 5 werkdagen verdeeld.
const DAGEN = ['ma', 'di', 'wo', 'do', 'vr']
const weekSchema = computed(() => {
  const basis = Math.floor(be.value.perWk / 5), rest = be.value.perWk % 5
  return DAGEN.map((d, i) => ({ d, n: basis + (i < rest ? 1 : 0) }))
})
const maxDag = computed(() => Math.max(...weekSchema.value.map(x => x.n), 1))
const beDatum = computed(() => {
  const t = st.byCode(winkel.value)
  const start = (t && t.liveDate) ? new Date(t.liveDate) : new Date()
  start.setDate(start.getDate() + be.value.days)
  return start.toLocaleDateString('nl-NL', { day: 'numeric', month: 'long', year: 'numeric' })
})

// Jaardoel-afgeleiden (v71 jaarCalc)
const fles = computed(() => omzetPF(sel.type, 'bottle', sel.size))
const refillPrijs = computed(() => omzetPF(sel.type, 'refill', sel.size))
const perWeekJ = computed(() => (goal.value.flJaar / 52).toLocaleString('nl-NL', { maximumFractionDigits: 1 }))
const perMaandJ = computed(() => (goal.value.flJaar / 12).toLocaleString('nl-NL', { maximumFractionDigits: 1 }))

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
    <p class="sub">Twee hulpmiddelen voor het verkoopgesprek. We rekenen altijd met de omzet excl. btw per fles.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <p v-if="melding" class="ok" role="status">{{ melding }}</p>

    <div class="tabs">
      <button type="button" :class="{ aan: tab === 'terug' }" data-test="tab-terug" @click="tab = 'terug'">Terugverdienen</button>
      <button type="button" :class="{ aan: tab === 'doel' }" data-test="tab-doel" @click="tab = 'doel'">Jaardoel</button>
    </div>

    <!-- ============ TERUGVERDIENEN ============ -->
    <template v-if="tab === 'terug'">
      <p class="note intro">Na hoeveel dagen verdient een tappunt de investering terug? De voorraad zit al in de eerste order, dus elke verkochte fles is omzet.</p>
      <div class="grid2">
        <!-- Links: de knoppen -->
        <div class="kaart">
          <label class="fl">Pakket (investering, excl. btw)
            <select v-model.number="sel.pkg" data-test="calc-pakket">
              <option v-for="(p, i) in PKG" :key="p.n" :value="i">{{ p.n }} — {{ eur0(p.inv) }}</option>
            </select>
          </label>
          <span class="fl">Soort</span>
          <div class="seg" data-test="calc-type">
            <button type="button" :class="{ on: sel.type === 'std' }" @click="sel.type = 'std'">Standaard</button>
            <button type="button" :class="{ on: sel.type === 'excl' }" @click="sel.type = 'excl'">Exclusive</button>
          </div>
          <span class="fl">Met flesje of refill</span>
          <div class="seg" data-test="calc-mode">
            <button type="button" :class="{ on: sel.mode === 'bottle' }" @click="sel.mode = 'bottle'">Parfum + flesje</button>
            <button type="button" :class="{ on: sel.mode === 'refill' }" @click="sel.mode = 'refill'">Refill</button>
          </div>
          <span class="fl">Formaat</span>
          <div class="seg" data-test="calc-maat">
            <button v-for="m in ['30', '50', '100']" :key="m" type="button" :class="{ on: sel.size === m }" @click="sel.size = m">{{ m }} ml</button>
          </div>
          <label class="fl">Verwachte verkoop per week (flessen)
            <span class="slider-rij">
              <input v-model.number="sel.rate" type="range" min="1" max="80" data-test="calc-rate" />
              <span class="pil">{{ sel.rate }}</span>
            </span>
          </label>
          <label class="fl">of: flessen per werkdag (ma–vr)
            <input :value="perDag" type="number" min="0.5" step="0.5" data-test="calc-perdag" @input="zetPerDag($event.target.value)" />
          </label>
          <p class="note">Per dag × 5 werkdagen = per week. Een gemiddeld tappunt verkoopt 20–40 flessen per week (≈ 4–8 per werkdag).</p>
        </div>

        <!-- Rechts: het verhaal -->
        <div class="kaart" data-test="res-terug">
          <p class="story">Het tappunt investeert <b>{{ eur0(be.inv) }}</b>. De voorraad is daarmee al betaald, dus elke verkochte fles ({{ lijnLabel }}) brengt <b>{{ eur(be.rev) }}</b> omzet (excl. btw) binnen. Na <b>{{ be.bottles.toLocaleString('nl-NL') }} flessen</b> is de investering terugverdiend — bij <b>{{ be.perWk }} flessen per week</b> is dat na <b>{{ weken }} {{ weken === 1 ? 'week' : 'weken' }}</b> (≈ {{ be.days }} dagen / {{ maanden }} maanden).</p>
          <div class="calckpis">
            <div class="ckpi"><b>{{ eur0(be.inv) }}</b><span>Investering</span></div>
            <div class="ckpi"><b class="coral">{{ eur(be.rev) }}</b><span>Omzet / fles (excl. btw)</span></div>
            <div class="ckpi"><b data-test="be-bottles">{{ be.bottles }}</b><span>Flessen tot terugverdiend</span></div>
            <div class="ckpi"><b class="coral"><span data-test="be-days">{{ be.days }}</span> dgn</b><span>Terugverdiend in</span></div>
          </div>
          <div class="tijdkop"><span>Eerste 12 maanden</span><span>{{ winst12 >= 0 ? 'Boven investering na 12 mnd: ' : 'Resterend na 12 mnd: ' }}{{ eur0(winst12) }}</span></div>
          <div class="tijdlijn">
            <div class="vul" :style="{ width: frac * 100 + '%' }"></div>
            <div class="bepunt" :style="{ left: frac * 100 + '%' }"></div>
            <div class="belabel" :style="{ left: frac * 100 + '%' }">{{ be.days > 365 ? '> 1 jaar' : 'terugverdiend dag ' + be.days }}</div>
          </div>
          <p class="note">Aannames: {{ be.perWk }} flessen/week (≈ {{ perDag }} per werkdag), {{ be.perWk * 52 }} flessen/jaar, omzet {{ eur(be.rev) }} per fles (excl. btw).</p>
          <div class="vastleg">
            <select v-model="winkel" data-test="calc-winkel" aria-label="Winkel om op vast te leggen">
              <option value="">— kies winkel —</option>
              <option v-for="t in st.items" :key="t.snelstart" :value="t.snelstart">{{ t.name }}</option>
            </select>
            <button class="btn" type="button" data-test="calc-vastleggen" @click="vastleggen">Plan &amp; pakket vastleggen</button>
          </div>
        </div>
      </div>

      <!-- Verkoopschema ma-vr -->
      <div class="kaart schema">
        <div class="sec-t">Verkoopschema — flessen per week (ma–vr)</div>
        <div class="weekgrid" aria-label="Flessen per werkdag">
          <div v-for="d in weekSchema" :key="d.d" class="wkol">
            <span class="wn">{{ d.n }}</span>
            <span class="wbar" :style="{ height: Math.max(8, d.n / maxDag * 64) + 'px' }"></span>
            <span class="wd">{{ d.d }}</span>
          </div>
        </div>
        <p class="note">Doel: <b>{{ be.perWk }} flessen per week</b> (≈ {{ perDag }} per werkdag) om dit pakket terug te verdienen. Bij dit tempo break-even in <b>{{ be.days }} dagen</b> — rond <b>{{ beDatum }}</b>.</p>
      </div>
    </template>

    <!-- ============ JAARDOEL ============ -->
    <template v-else>
      <p class="note intro">Vul een jaardoel in en zie wat er nodig is: hoeveel flessen, hoeveel per dag, en hoeveel vaste klanten — uitgaande van een klant die na de eerste fles nog een aantal keer terugkomt om te hervullen.</p>
      <div class="grid2">
        <!-- Links: de knoppen -->
        <div class="kaart">
          <label class="fl">Jaardoel (omzet excl. btw)
            <input v-model.number="sel.doel" type="number" min="0" data-test="calc-doel" />
          </label>
          <label class="fl">Hoe vaak komt een klant hervullen?
            <span class="slider-rij">
              <input v-model.number="sel.refills" type="range" min="1" max="20" data-test="calc-refills" />
              <span class="pil">{{ sel.refills }}</span>
            </span>
          </label>
          <p class="note">Standaard 8 hervullingen: 1 eerste fles + 8 refills = 9 flessen per klant.</p>
          <span class="fl">Soort</span>
          <div class="seg" data-test="calc-type">
            <button type="button" :class="{ on: sel.type === 'std' }" @click="sel.type = 'std'">Standaard</button>
            <button type="button" :class="{ on: sel.type === 'excl' }" @click="sel.type = 'excl'">Exclusive</button>
          </div>
          <span class="fl">Formaat</span>
          <div class="seg" data-test="calc-maat">
            <button v-for="m in ['30', '50', '100']" :key="m" type="button" :class="{ on: sel.size === m }" @click="sel.size = m">{{ m }} ml</button>
          </div>
          <p class="note">Prijs per fles/refill volgt de gekozen soort en maat.</p>
        </div>

        <!-- Rechts: het verhaal -->
        <div class="kaart" data-test="res-doel">
          <p v-if="goal.doel > 0" class="story">Om <b>{{ eur0(goal.doel) }}</b> omzet (excl. btw) per jaar te halen — met een klant die na de eerste fles nog <b>{{ goal.refills }}×</b> terugkomt om te hervullen — heb je ≈ <b>{{ goal.klanten }} vaste klanten</b> nodig. Elke klant koopt <b>{{ 1 + goal.refills }} flessen</b> (1 fles + {{ goal.refills }} refills) en is samen goed voor <b>{{ eur(goal.revKlant) }}</b>. Samen kopen ze ≈ <b>{{ goal.flJaar.toLocaleString('nl-NL') }} flessen per jaar</b> = ≈ <b>{{ goal.flDag }} per dag</b>.</p>
          <p v-else class="story">Vul een jaardoel in om te zien hoeveel klanten en flessen je nodig hebt.</p>
          <div class="calckpis">
            <div class="ckpi"><b class="coral" data-test="goal-klanten">{{ goal.klanten }}</b><span>Vaste klanten nodig</span></div>
            <div class="ckpi"><b>{{ goal.flJaar.toLocaleString('nl-NL') }}</b><span>Flessen per jaar</span></div>
            <div class="ckpi"><b class="coral">{{ goal.flDag }}</b><span>Flessen per dag</span></div>
            <div class="ckpi"><b>{{ eur(goal.revKlant) }}</b><span>Omzet per klant</span></div>
          </div>
          <div class="rijtjes">
            <div class="rijtje"><span>Per week</span><b data-test="goal-flweek">{{ goal.flWeek }}</b></div>
            <div class="rijtje"><span>Per maand</span><b>{{ perMaandJ }} flessen</b></div>
            <div class="rijtje"><span>Omzet per fles · per refill</span><b>{{ eur(fles) }} · {{ eur(refillPrijs) }}</b></div>
          </div>
          <p class="note">Aannames: {{ sel.size }} ml {{ sel.type === 'std' ? 'standaard' : 'Exclusive' }}, 1 eerste fles ({{ eur(fles) }}) + {{ sel.refills }} refills ({{ eur(refillPrijs) }}) per klant. Flessen per dag = totaal ÷ 365.</p>
          <div class="vastleg">
            <select v-model="winkel" data-test="calc-winkel" aria-label="Winkel om op vast te leggen">
              <option value="">— kies winkel —</option>
              <option v-for="t in st.items" :key="t.snelstart" :value="t.snelstart">{{ t.name }}</option>
            </select>
            <button class="btn" type="button" data-test="calc-vastleggen" @click="vastleggen">Jaardoel vastleggen</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.tabs{display:flex;gap:0;margin-bottom:14px;max-width:420px;border:1.5px solid var(--line);border-radius:12px;overflow:hidden;background:#fff}
.tabs button{flex:1;background:#fff;border:0;padding:10px 16px;font-weight:800;font-size:13.5px;color:var(--grey);cursor:pointer}
.tabs button.aan{background:var(--coral);color:#fff}
.note{font-size:12.5px;color:var(--grey);background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:9px 11px;margin:10px 0 0;line-height:1.5}
.note.intro{margin:0 0 14px}
.grid2{display:grid;grid-template-columns:1fr 1.15fr;gap:14px}
@media(max-width:900px){.grid2{grid-template-columns:1fr}}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px}
.fl{display:block;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:var(--grey);margin:14px 0 6px}
.fl:first-child{margin-top:0}
label.fl{text-transform:none;letter-spacing:0;font-size:12.5px}
select,input[type=number]{width:100%;padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit;margin-top:6px}
select:focus,input:focus{border-color:var(--coral);outline:none}
/* Segment-knoppen (v71 .seg) */
.seg{display:flex;border:1.5px solid var(--line);border-radius:10px;overflow:hidden;background:#fff}
.seg button{flex:1;background:#fff;border:0;padding:9px 6px;font-weight:700;font-size:13px;color:var(--grey);cursor:pointer;border-left:1px solid var(--line)}
.seg button:first-child{border-left:0}
.seg button.on{background:var(--soft);color:var(--coral-d)}
/* Schuif + pil */
.slider-rij{display:flex;align-items:center;gap:10px;margin-top:8px}
.slider-rij input[type=range]{flex:1;accent-color:var(--coral);margin:0}
.pil{background:var(--coral);color:#fff;font-weight:900;font-size:13px;border-radius:999px;padding:4px 12px;min-width:40px;text-align:center;font-variant-numeric:tabular-nums}
/* Verhaal + KPI's */
.story{margin:0 0 14px;font-size:13.5px;line-height:1.65}
.story b{color:var(--coral-d)}
.calckpis{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.ckpi{background:var(--cream);border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.ckpi b{display:block;font-size:20px;font-variant-numeric:tabular-nums}
.ckpi b.coral{color:var(--coral-d)}
.ckpi span{font-size:11px;color:var(--grey);font-weight:700}
/* Tijdlijn 12 maanden */
.tijdkop{display:flex;justify-content:space-between;gap:10px;font-size:12px;color:var(--grey);font-weight:700;margin:16px 0 5px}
.tijdlijn{position:relative;height:10px;border-radius:6px;background:#f0ebe3;margin-bottom:26px}
.tijdlijn .vul{height:100%;border-radius:6px;background:linear-gradient(90deg,var(--peach),var(--coral))}
.bepunt{position:absolute;top:-3px;width:16px;height:16px;border-radius:50%;background:var(--coral-d);border:3px solid #fff;transform:translateX(-50%);box-shadow:0 1px 4px rgba(0,0,0,.25)}
.belabel{position:absolute;top:16px;transform:translateX(-50%);font-size:11px;font-weight:800;color:var(--coral-d);white-space:nowrap}
/* Rijtjes (jaardoel) */
.rijtjes{border-top:1px solid var(--line);margin-top:14px;padding-top:8px}
.rijtje{display:flex;justify-content:space-between;font-size:13.5px;padding:4px 0}
.rijtje span{color:var(--grey)}
/* Vastleggen */
.vastleg{display:flex;gap:10px;align-items:center;margin-top:14px;flex-wrap:wrap}
.vastleg select{flex:1;min-width:170px;margin-top:0;width:auto}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer;font-size:13px}
.btn:hover{background:var(--coral-d)}
/* Verkoopschema */
.schema{margin-top:14px}
.sec-t{font-size:12px;text-transform:uppercase;letter-spacing:1px;color:var(--coral-d);font-weight:800;margin-bottom:12px}
.weekgrid{display:flex;gap:18px;align-items:flex-end;height:96px;padding:0 4px}
.wkol{display:flex;flex-direction:column;align-items:center;gap:4px;justify-content:flex-end}
.wn{font-size:12px;font-weight:800;font-variant-numeric:tabular-nums}
.wbar{width:34px;border-radius:6px 6px 0 0;background:linear-gradient(180deg,var(--coral),var(--peach))}
.wd{font-size:11px;color:var(--grey);font-weight:700;text-transform:uppercase}
.fout{color:#b3261e}
.ok{color:#2c5a12;background:#f4faf0;border-radius:8px;padding:8px 10px;font-size:13.5px}
</style>
