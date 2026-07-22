<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useTappunten } from '../../tappunten/store.js'
import { haalDeals, nieuweDeal, zetFase, FASEN } from '../api.js'
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
</script>

<template>
  <div>
    <h1>Deals</h1>
    <p class="sub">Verkoopkansen door de pijplijn — van lead tot gewonnen. Winkels zien dit niet.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

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
          <b>{{ lbl }}</b>
          <span class="totaal" :data-test="'totaal-' + k">{{ eur0(perFase[k].totaal) }}</span>
        </div>
        <div v-for="d in perFase[k].deals" :key="d.id" class="dealkaart" data-test="deal-kaart">
          <b class="dt">{{ d.titel }}</b>
          <span class="mo">{{ WINKEL[d.tappunt_snelstart] || d.tappunt_snelstart }}</span>
          <span class="mo">{{ eur0(d.waarde) }}<template v-if="d.verwacht"> · {{ d.verwacht }}</template></span>
          <select class="fasesel" :value="d.fase" data-test="deal-fase" @change="fase(d, $event)">
            <option v-for="[fk, flbl] in FASEN" :key="fk" :value="fk">{{ flbl }}</option>
          </select>
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
select:focus,input:focus{outline:none;border-color:var(--coral)}
.btn{align-self:flex-start;background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 16px;font-weight:800;cursor:pointer}
.btn:disabled{opacity:.6}
.pijplijn{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}
.kolom{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px;min-height:120px}
.kolom.gewonnen{border-color:#bcd9a0}
.kolom.verloren{opacity:.7}
.kolomkop{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px}
.kolomkop b{font-size:13px}
.totaal{font-size:11.5px;font-weight:800;color:var(--coral)}
.dealkaart{display:flex;flex-direction:column;gap:3px;border:1px solid var(--line);border-radius:10px;padding:10px;margin-bottom:8px;background:#faf7f2}
.dt{font-size:13.5px}
.mo{color:var(--grey);font-size:12px}
.fasesel{margin-top:6px;font-size:12px;padding:5px 8px}
.leeg{color:var(--line);text-align:center;margin:8px 0}
.fout{color:#b3261e}
</style>
