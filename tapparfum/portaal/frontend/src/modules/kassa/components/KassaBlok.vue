<script setup>
// Kassa — tik elke winkelverkoop, per flesmaat. 1-op-1 datacompatibel met v71:
//  * t.verkopen['YYYY-MM-DD'][maat] telt de stuks per dag;
//  * elke tik schrijft OOK een flesLog-regel {at, n:1, ti:t.dagType??1, src:'kassa'}
//    (de flessenteller blijft leidend voor break-even/jaardoel);
//  * de min-knop draait beide terug.
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { haalFlesMaten, haalModules, vkTotaal, vkPeriode } from '../api.js'
import { eur0 } from '../../../lib/format.js'
import { SALE_TYPES } from '../../rekenhart/logic.js'
import { omzetPF } from '../../calculator/logic.js'
import { checkMilestones } from '../../beloningen/logic.js'
import { haalRekenConfig } from '../../beloningen/api.js'
import { stuurWinkelvraag } from '../../winkelvragen/api.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const emit = defineEmits(['bijgewerkt'])
const auth = useAuth()
const st = useTappunten()
const maten = ref([])
const fout = ref('')
const bezig = ref(false)
const marge = ref(1)
const mijlpaal = ref('')
const zichtbaar = ref(true)      // kantoor kan de kassa-module netwerkbreed uitzetten
const vandaag = new Date().toISOString().slice(0, 10)

onMounted(async () => {
  try {
    const mo = await haalModules()
    zichtbaar.value = !mo || mo.kassa !== false
    if (zichtbaar.value) {
      maten.value = await haalFlesMaten()
      marge.value = (await haalRekenConfig()).marge
    }
  } catch (e) { fout.value = 'Kon kassaprijzen niet laden: ' + e.message }
})

const dagCounts = computed(() => (props.tappunt.verkopen || {})[vandaag] || {})
const totVandaag = computed(() => vkTotaal(dagCounts.value, maten.value))
const week = computed(() => vkPeriode(props.tappunt, new Date(Date.now() - 6 * 864e5).toISOString().slice(0, 10), maten.value))
const jaar = computed(() => vkPeriode(props.tappunt, new Date().getFullYear() + '-01-01', maten.value))

async function bewaar(t2) {
  bezig.value = true; fout.value = ''
  try { await st.bewaar(t2); emit('bijgewerkt', t2) }
  catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function plus(maat) {
  if (bezig.value) return
  const t = props.tappunt
  const verkopen = { ...(t.verkopen || {}) }
  const dag = { ...(verkopen[vandaag] || {}) }
  dag[maat] = (+dag[maat] || 0) + 1
  verkopen[vandaag] = dag
  const flesLog = [...(t.flesLog || []), { at: vandaag, n: 1, ti: (t.dagType ?? 1), src: 'kassa' }]
    .sort((a, b) => (a.at < b.at ? -1 : 1))
  // v71 checkMilestones: een kassatik kan break-even (of een beloning) kruisen.
  let t2 = { ...t, verkopen, flesLog }
  const res = checkMilestones(t2, Number(t.jaaromzet) || 0, marge.value)
  if (res) {
    t2 = res.t2
    mijlpaal.value = res.meldingen.join(' · ')
    if (auth.isPartner || auth.isKantoor) {
      for (const m of res.meldingen) {
        try { await stuurWinkelvraag({ tappunt_snelstart: t2.snelstart, type: 'mijlpaal', txt: m }) }
        catch { /* melding is een extraatje */ }
      }
    }
  }
  await bewaar(t2)
}

// v71-dagtype: het standaard verkooptype waarmee elke kassatik in de
// flessenteller landt (t.dagType = index in SALE_TYPES).
async function zetDagType(v) {
  await bewaar({ ...props.tappunt, dagType: parseInt(v) || 0 })
}

async function min(maat) {
  if (bezig.value) return
  const t = props.tappunt
  const dagOud = (t.verkopen || {})[vandaag] || {}
  if (!(+dagOud[maat] > 0)) return
  const verkopen = { ...(t.verkopen || {}) }
  const dag = { ...dagOud, [maat]: (+dagOud[maat]) - 1 }
  if (dag[maat] <= 0) delete dag[maat]
  if (Object.keys(dag).length) verkopen[vandaag] = dag; else delete verkopen[vandaag]
  // laatste kassaregel van vandaag uit de flessenlog terugdraaien
  const flesLog = [...(t.flesLog || [])]
  for (let i = flesLog.length - 1; i >= 0; i--) {
    if (flesLog[i].at === vandaag && flesLog[i].src === 'kassa') { flesLog.splice(i, 1); break }
  }
  await bewaar({ ...t, verkopen, flesLog })
}
</script>

<template>
  <section v-if="zichtbaar" class="blok">
    <h2>🧾 Kassa — tik elke verkoop</h2>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <p v-if="mijlpaal" class="mijlpaal" role="status" data-test="kassa-mijlpaal">🎉 {{ mijlpaal }}</p>

    <div class="maten">
      <div v-for="x in maten" :key="x.m" class="maat" data-test="kassa-maat">
        <button class="tik" type="button" :disabled="bezig" :data-test="'kassa-plus-' + x.m"
                :aria-label="'Verkoop ' + x.m + ' registreren'" @click="plus(x.m)">
          + {{ x.m }}
          <span class="prijs">{{ eur0(x.p) }}</span>
        </button>
        <div class="onder">
          <span class="n" :data-test="'kassa-n-' + x.m">{{ dagCounts[x.m] || 0 }}× vandaag</span>
          <button v-if="(dagCounts[x.m] || 0) > 0" class="corr" type="button" :data-test="'kassa-min-' + x.m"
                  :aria-label="'Correctie: één ' + x.m + ' eraf'" @click="min(x.m)">−1</button>
        </div>
      </div>
    </div>

    <label class="dagtype">Standaardtype voor de flessenteller:
      <select :value="tappunt.dagType ?? 1" :disabled="bezig" data-test="kassa-dagtype"
              @change="zetDagType($event.target.value)">
        <option v-for="(x, i) in SALE_TYPES" :key="i" :value="i">{{ x.label }} · {{ eur0(omzetPF(x.tp, x.md, x.sz)) }}</option>
      </select>
    </label>

    <div class="totalen">
      <div class="tot"><b data-test="kassa-vandaag">{{ eur0(totVandaag) }}</b><span>vandaag</span></div>
      <div class="tot"><b data-test="kassa-week">{{ eur0(week.tot) }}</b><span>deze week · {{ week.stuks }} st.</span></div>
      <div class="tot"><b data-test="kassa-jaar">{{ eur0(jaar.tot) }}</b><span>dit jaar · {{ jaar.stuks }} st.</span></div>
    </div>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-top:14px}
h2{margin:0 0 12px;font-size:16px}
.maten{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px}
.maat{display:flex;flex-direction:column;gap:5px}
.tik{display:flex;flex-direction:column;align-items:center;gap:2px;background:var(--soft);border:1.5px solid var(--coral);color:var(--coral-d);border-radius:12px;padding:12px 8px;font-weight:800;font-size:15px;cursor:pointer}
.tik:hover{background:var(--coral);color:#fff}
.tik:disabled{opacity:.6}
.prijs{font-size:11.5px;font-weight:700;opacity:.8}
.onder{display:flex;align-items:center;justify-content:space-between;gap:6px;min-height:22px}
.dagtype{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:12px;font-size:12px;font-weight:700;color:var(--grey)}
.dagtype select{padding:7px 9px;border:1.5px solid var(--line);border-radius:9px;font-size:12.5px;font-family:inherit;max-width:280px}
.dagtype select:focus{border-color:var(--coral)}
.n{font-size:12px;color:var(--grey);font-weight:700}
.corr{background:none;border:1px solid var(--line);border-radius:6px;font-size:11px;font-weight:700;color:var(--grey);cursor:pointer;padding:1px 7px}
.corr:hover{border-color:#b3261e;color:#b3261e}
.totalen{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px;border-top:1px solid var(--line);padding-top:12px}
.tot{flex:1;min-width:120px;background:var(--cream);border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:flex;flex-direction:column;gap:2px}
.tot b{font-size:17px;color:var(--coral-d)}
.tot span{font-size:11.5px;color:var(--grey);font-weight:700}
.fout{color:#b3261e;font-size:13px}
.mijlpaal{background:var(--green-soft);border:1px solid #bcd9a0;color:#2c5a12;border-radius:10px;padding:8px 12px;font-size:13px;margin:0 0 10px}
</style>
