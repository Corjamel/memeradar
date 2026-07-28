<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useTappunten } from '../../tappunten/store.js'
import { haalDeals, nieuweDeal, zetFase, zetReden, FASEN, KANS, OPEN_FASEN } from '../api.js'
import { eur0 } from '../../../lib/format.js'

const st = useTappunten()
const deals = ref([])
const fout = ref('')
const bezig = ref(false)
const nieuw = reactive({ tappunt_snelstart: '', titel: '', waarde: '', verwacht: '' })

const WINKEL = computed(() => Object.fromEntries(st.items.map(t => [t.snelstart, t.name])))
const perFase = computed(() => {
  const m = {}
  for (const [k] of FASEN) m[k] = { deals: [], totaal: 0 }
  for (const d of deals.value) {
    const f = m[d.fase] || m.lead
    f.deals.push(d); f.totaal += Number(d.waarde) || 0
  }
  return m
})
const kans = (fase) => KANS[fase] || 0
const gewogenVan = (d) => Math.round((Number(d.waarde) || 0) * kans(d.fase))

// Forecast-strook: open pijplijn, gewogen forecast (waarde × fase-kans),
// gewonnen dit jaar en win-rate (gewonnen ÷ afgesloten).
const forecast = computed(() => {
  let open = 0, openN = 0, gewogen = 0, won = 0, wonN = 0, lostN = 0
  for (const d of deals.value) {
    const w = Number(d.waarde) || 0
    if (OPEN_FASEN.includes(d.fase)) { open += w; openN++; gewogen += w * kans(d.fase) }
    else if (d.fase === 'gewonnen') { won += w; wonN++ }
    else if (d.fase === 'verloren') { lostN++ }
  }
  const afgesloten = wonN + lostN
  return { open, openN, gewogen: Math.round(gewogen), won, wonN, winRate: afgesloten ? Math.round(wonN / afgesloten * 100) : null }
})

async function laad() {
  fout.value = ''
  try { deals.value = await haalDeals() }
  catch (e) { fout.value = 'Kon deals niet laden: ' + e.message }
}
onMounted(async () => {
  if (!st.items.length) await st.laad()
  await laad()
})

async function toevoegen() {
  if (bezig.value) return
  if (!nieuw.tappunt_snelstart || !nieuw.titel.trim()) { fout.value = 'Kies een winkel en geef de deal een titel.'; return }
  bezig.value = true; fout.value = ''
  try {
    await nieuweDeal(nieuw)
    nieuw.titel = ''; nieuw.waarde = ''; nieuw.verwacht = ''
    await laad()
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function fase(d, ev) {
  try { await zetFase(d.id, ev.target.value); await laad() }
  catch (e) { fout.value = 'Fase wijzigen mislukt: ' + e.message }
}

// Won/lost-reden opslaan op een afgesloten deal (blur/enter).
async function reden(d, ev) {
  const v = (ev.target.value || '').trim()
  if (v === (d.reden || '')) return
  try { await zetReden(d.id, v); await laad() }
  catch (e) { fout.value = 'Reden opslaan mislukt: ' + e.message }
}
</script>

<template>
  <div>
    <p class="eyebrow">Pijplijn</p>
    <h1>Deals</h1>
    <p class="sub">Verkoopkansen door de pijplijn — van lead tot gewonnen. Winkels zien dit niet.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Forecast-strook: gewogen pijplijn op één rij -->
    <div class="kpis" data-test="deal-forecast">
      <div class="kpi"><b>{{ eur0(forecast.open) }}</b><span>Open pijplijn · {{ forecast.openN }} deals</span></div>
      <div class="kpi"><b class="coral" data-test="forecast-gewogen">{{ eur0(forecast.gewogen) }}</b><span>Gewogen forecast</span></div>
      <div class="kpi"><b data-test="forecast-won">{{ eur0(forecast.won) }}</b><span>Gewonnen · {{ forecast.wonN }}</span></div>
      <div class="kpi"><b data-test="forecast-winrate">{{ forecast.winRate == null ? '—' : forecast.winRate + '%' }}</b><span>Win-rate</span></div>
    </div>

    <form class="kaart nieuw" @submit.prevent="toevoegen">
      <div class="rij">
        <label>Winkel
          <select v-model="nieuw.tappunt_snelstart" required data-test="deal-winkel">
            <option value="" disabled>Kies winkel…</option>
            <option v-for="t in st.items" :key="t.snelstart" :value="t.snelstart">{{ t.name }}</option>
          </select>
        </label>
        <label>Titel<input v-model="nieuw.titel" required placeholder="Bijv. Tweede display" data-test="deal-titel" /></label>
        <label>Waarde (€)<input v-model="nieuw.waarde" type="number" min="0" placeholder="1500" data-test="deal-waarde" /></label>
        <label>Verwacht<input v-model="nieuw.verwacht" type="date" /></label>
      </div>
      <button class="btn" type="submit" :disabled="bezig" data-test="deal-toevoegen">{{ bezig ? 'Bezig…' : 'Deal toevoegen' }}</button>
    </form>

    <div class="pijplijn">
      <div v-for="[k, lbl] in FASEN" :key="k" class="kolom" :class="k" :data-test="'kolom-' + k">
        <div class="kolomkop">
          <b>{{ lbl }} <span class="n" :data-test="'aantal-' + k">{{ perFase[k].deals.length }}</span></b>
          <span class="totaal" :data-test="'totaal-' + k">{{ eur0(perFase[k].totaal) }}<template v-if="kans(k) > 0 && kans(k) < 1"> · {{ Math.round(kans(k) * 100) }}%</template></span>
        </div>
        <div v-for="d in perFase[k].deals" :key="d.id" class="dealkaart" data-test="deal-kaart">
          <b class="dt">{{ d.titel }}</b>
          <span class="mo">{{ WINKEL[d.tappunt_snelstart] || d.tappunt_snelstart }}</span>
          <span class="mo">{{ eur0(d.waarde) }}<template v-if="d.verwacht"> · {{ d.verwacht }}</template></span>
          <span v-if="kans(d.fase) > 0 && kans(d.fase) < 1" class="mo gewogen">gewogen {{ eur0(gewogenVan(d)) }}</span>
          <select class="fasesel" :value="d.fase" :aria-label="'Fase van deal ' + d.titel" data-test="deal-fase" @change="fase(d, $event)">
            <option v-for="[fk, flbl] in FASEN" :key="fk" :value="fk">{{ flbl }}</option>
          </select>
          <input v-if="d.fase === 'gewonnen' || d.fase === 'verloren'" class="reden"
                 :value="d.reden || ''" :data-test="'deal-reden-' + d.id"
                 :placeholder="d.fase === 'gewonnen' ? 'Waarom gewonnen?' : 'Waarom verloren?'"
                 :aria-label="'Reden voor ' + d.titel" @change="reden(d, $event)" />
        </div>
        <p v-if="!perFase[k].deals.length" class="leeg">—</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:14px}
.nieuw{display:flex;flex-direction:column;gap:10px}
.rij{display:flex;gap:12px;flex-wrap:wrap}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:140px}
select,input{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
select:focus,input:focus{border-color:var(--coral)}
.btn{align-self:flex-start;background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 16px;font-weight:800;cursor:pointer}
.btn:disabled{opacity:.6}
.pijplijn{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}
.kolom{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px;min-height:120px}
.kolom.gewonnen{border-color:#bcd9a0}
.kolom.verloren{opacity:.7}
.kolomkop{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px}
.kolomkop b{font-size:13px}
.kolomkop .n{display:inline-block;min-width:18px;text-align:center;background:var(--soft);color:var(--coral-d);font-size:10.5px;font-weight:800;border-radius:999px;padding:1px 6px;margin-left:2px}
.totaal{font-size:11.5px;font-weight:800;color:var(--coral-d)}
.gewogen{color:var(--coral-d);font-weight:700;font-size:11px}
/* Forecast-strook */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:14px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 14px}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi b.coral{color:var(--coral-d)}
.kpi span{color:var(--grey);font-size:11.5px;font-weight:700}
.dealkaart{display:flex;flex-direction:column;gap:3px;border:1px solid var(--line);border-radius:10px;padding:10px;margin-bottom:8px;background:#faf7f2}
.dt{font-size:13.5px}
.mo{color:var(--grey);font-size:12px}
.fasesel{margin-top:6px;font-size:12px;padding:5px 8px}
.reden{margin-top:6px;font-size:12px;padding:6px 8px;border:1.5px solid var(--line);border-radius:8px;width:100%}
.reden:focus{border-color:var(--coral);outline:none}
.leeg{color:var(--line);text-align:center;margin:8px 0}
.fout{color:#b3261e}
</style>
