<script setup>
// Verkoop & omzet bij één winkel — het hart van de oude app, 1-op-1
// datacompatibel met v71: t.jaaromzet (inkoop bij TapParfum), t.doel en
// t.flesLog met regels {at:'YYYY-MM-DD', n:aantal, ti:type}. Beide apps lezen
// en schrijven dezelfde JSON, dus de cijfers blijven overal gelijk.
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { eur0 } from '../../../lib/format.js'
import { checkMilestones } from '../../beloningen/logic.js'
import { haalRekenConfig } from '../../beloningen/api.js'
import { stuurWinkelvraag } from '../../winkelvragen/api.js'
import { SALE_TYPES, flessenVerkocht, beDone } from '../../rekenhart/logic.js'
import { omzetPF } from '../../calculator/logic.js'
import { schemaStatus, dagTotaal, zetDagVerkoop, laatste7Dagen } from '../logic.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const emit = defineEmits(['bijgewerkt'])
const auth = useAuth()
const st = useTappunten()
const vandaag = new Date().toISOString().slice(0, 10)
const marge = ref(1)
const mijlpaal = ref('')

onMounted(async () => {
  try { marge.value = (await haalRekenConfig()).marge } catch { /* factor 1 */ }
})

/* v71 checkMilestones: elke omzet-/flessenmutatie kan een niveau, het jaardoel
   of break-even kruisen — vier het en meld het op de berichtlijn. */
async function metMijlpalen(t2, joVoor) {
  const res = checkMilestones(t2, joVoor, marge.value)
  if (!res) return t2
  mijlpaal.value = res.meldingen.join(' · ')
  if (auth.isPartner || auth.isKantoor) {
    for (const m of res.meldingen) {
      try { await stuurWinkelvraag({ tappunt_snelstart: t2.snelstart, type: 'mijlpaal', txt: m }) }
      catch { /* melding is een extraatje */ }
    }
  }
  return res.t2
}

const fout = ref('')
const melding = ref('')
const bezig = ref(false)
const wis = ref(null)          // twee-staps verwijderen: eerste klik = 'Zeker?'
const omzet = reactive({ jaaromzet: props.tappunt.jaaromzet || '', doel: props.tappunt.doel || '' })
const reg = reactive({ datum: vandaag, aantal: 1, ti: props.tappunt.dagType ?? 1 })

const log = computed(() => props.tappunt.flesLog || [])
function vanafN(vanaf) { return log.value.filter(e => e.at >= vanaf).reduce((s, e) => s + (+e.n || 0), 0) }
const flesVandaag = computed(() => log.value.filter(e => e.at === vandaag).reduce((s, e) => s + (+e.n || 0), 0))
const flesWeek = computed(() => vanafN(new Date(Date.now() - 6 * 864e5).toISOString().slice(0, 10)))
const flesJaar = computed(() => vanafN(new Date().getFullYear() + '-01-01'))
const laatste = computed(() => [...log.value].map((e, i) => ({ e, i })).sort((a, b) => (a.e.at < b.e.at ? 1 : -1)).slice(0, 7))

// v71 SALE_TYPES-keuze: label + omzet per fles voor de <option>-lijst.
const typeOpties = SALE_TYPES.map((x, i) => ({ i, label: `${x.label} · ${eur0(omzetPF(x.tp, x.md, x.sz))}` }))

// Op-schema-strip + doelbalk (v71 schemaStatus/verkoopBlock).
const schema = computed(() => schemaStatus(props.tappunt))
const doel = computed(() => {
  const t = props.tappunt
  const inBe = t.be && !beDone(t)
  const target = inBe ? t.be.bottles : ((t.goal && t.goal.doel > 0) ? t.goal.flJaar : 0)
  const sold = flessenVerkocht(t)
  return { target, sold, lab: inBe ? 'tot break-even' : 'dit jaar (jaardoel)', pct: target ? Math.min(sold / target * 100, 100) : 0 }
})

// Week-invulrij: de laatste 7 dagen als vakjes (eerste-week-ritme).
const week7 = computed(() => laatste7Dagen().map(dg => ({ ...dg, n: dagTotaal(props.tappunt, dg.iso) || '' })))

async function bewaar(t2, ok) {
  bezig.value = true; fout.value = ''; melding.value = ''
  try { await st.bewaar(t2); emit('bijgewerkt', t2); melding.value = ok }
  catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function omzetOpslaan() {
  if (bezig.value) return
  const joVoor = Number(props.tappunt.jaaromzet) || 0
  let t2 = { ...props.tappunt, jaaromzet: Number(omzet.jaaromzet) || 0, doel: Number(omzet.doel) || 0 }
  t2 = await metMijlpalen(t2, joVoor)
  await bewaar(t2, '✓ Omzet & doel bijgewerkt')
}

async function registreer() {
  if (bezig.value) return
  const n = Math.max(parseInt(reg.aantal) || 0, 1)
  const entry = { at: reg.datum || vandaag, n, ti: parseInt(reg.ti) || 0 }
  const joVoor = Number(props.tappunt.jaaromzet) || 0
  let t2 = { ...props.tappunt, flesLog: [...log.value, entry].sort((a, b) => (a.at < b.at ? -1 : 1)) }
  t2 = await metMijlpalen(t2, joVoor)
  await bewaar(t2, `✓ ${n} fles${n === 1 ? '' : 'sen'} geregistreerd`)
  reg.aantal = 1; reg.datum = vandaag
}

// Week-invulrij: het aantal flessen voor één dag rechtstreeks zetten.
async function zetDag(iso, n) {
  if (bezig.value) return
  const joVoor = Number(props.tappunt.jaaromzet) || 0
  let t2 = zetDagVerkoop(props.tappunt, iso, n)
  t2 = await metMijlpalen(t2, joVoor)
  await bewaar(t2, '✓ Dag bijgewerkt')
}

async function verwijder(o) {
  if (bezig.value) return
  if (wis.value !== o.i) { wis.value = o.i; return }   // bevestiging: tweede klik voert uit
  wis.value = null
  const t2 = { ...props.tappunt, flesLog: log.value.filter((_, i) => i !== o.i) }
  await bewaar(t2, 'Regel verwijderd')
}
</script>

<template>
  <section class="blok">
    <h2>🧾 Verkoop & omzet</h2>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <p v-if="mijlpaal" class="mijlpaal" role="status" data-test="mijlpaal">🎉 {{ mijlpaal }}</p>

    <!-- Jaaromzet + doel (drijft niveaus en beloningen) -->
    <div class="rij vorm">
      <label>Jaaromzet dit jaar (inkoop)
        <input v-model="omzet.jaaromzet" type="number" min="0" placeholder="0" data-test="omzet-jaaromzet" />
      </label>
      <label>Jaardoel
        <input v-model="omzet.doel" type="number" min="0" placeholder="0" data-test="omzet-doel" />
      </label>
      <button class="knop" type="button" :disabled="bezig" data-test="omzet-opslaan" @click="omzetOpslaan">Opslaan</button>
    </div>

    <!-- Flessenteller -->
    <div class="teller">
      <div class="tegels">
        <div class="tegel"><b data-test="fles-vandaag">{{ flesVandaag }}</b><span>vandaag</span></div>
        <div class="tegel"><b data-test="fles-week">{{ flesWeek }}</b><span>laatste 7 dagen</span></div>
        <div class="tegel"><b data-test="fles-jaar">{{ flesJaar }}</b><span>dit jaar</span></div>
      </div>

      <!-- Op-schema-strip (v71 schemaHTML) -->
      <div v-if="schema" class="schema" :class="{ op: schema.delta >= 0 }" data-test="schema-strip">
        <div><span class="lbl">Verwacht t/m vandaag</span><b>{{ schema.verwacht }}</b></div>
        <div><span class="lbl">Werkelijk</span><b>{{ schema.werkelijk }}</b></div>
        <span class="pil" :class="{ op: schema.delta >= 0 }">{{ schema.delta >= 0 ? 'op schema · +' : 'achter · ' }}{{ schema.delta }} flessen</span>
        <span class="mo">{{ schema.fase === 'break-even' ? 't.o.v. je terugverdienplan' : 't.o.v. je jaardoel-tempo' }}{{ schema.bron === 'omzet' ? ' · berekend uit omzet' : '' }}</span>
      </div>

      <!-- Doelbalk (sold/target) -->
      <div v-if="doel.target" class="doelbalk" data-test="doelbalk">
        <div class="dinfo"><span><b>{{ doel.sold }}</b> / {{ doel.target }} flessen {{ doel.lab }}</span>
          <span class="mo">{{ Math.round(doel.pct) }}%{{ doel.sold < doel.target ? ` · nog ${doel.target - doel.sold}` : ' · gehaald ✓' }}</span></div>
        <div class="track"><div class="fill" :class="{ af: doel.sold >= doel.target }" :style="{ width: doel.pct + '%' }"></div></div>
      </div>

      <!-- Week-invulrij per dag (eerste-week-ritme, v71) -->
      <div class="blk-t">Deze week — vul per dag in</div>
      <div class="week7">
        <div v-for="dg in week7" :key="dg.iso" class="dag" :class="{ vandaag: dg.iso === vandaag }">
          <div class="wd">{{ dg.wd }}</div><div class="dm">{{ dg.dm }}</div>
          <input type="number" min="0" :value="dg.n" placeholder="0" :disabled="bezig"
                 :data-test="'week-' + dg.iso" :aria-label="'Flessen op ' + dg.iso"
                 @change="zetDag(dg.iso, $event.target.value)" />
        </div>
      </div>

      <!-- Andere dag / ander type (v71 SALE_TYPES-keuze) -->
      <div class="blk-t">Andere dag of ander type</div>
      <div class="rij vorm">
        <label>Datum<input v-model="reg.datum" type="date" data-test="fles-datum" /></label>
        <label>Aantal<input v-model="reg.aantal" type="number" min="1" data-test="fles-aantal" /></label>
        <label class="breed">Type
          <select v-model="reg.ti" data-test="fles-type">
            <option v-for="o in typeOpties" :key="o.i" :value="o.i">{{ o.label }}</option>
          </select>
        </label>
        <button class="knop" type="button" :disabled="bezig" data-test="fles-registreer" @click="registreer">+ Registreer</button>
      </div>

      <div v-if="laatste.length" class="loglijst">
        <div v-for="o in laatste" :key="o.i" class="logrij" data-test="fles-regel">
          <span>{{ o.e.at }}</span>
          <b>{{ o.e.n }}× {{ (SALE_TYPES[o.e.ti] || {}).label || 'fles' }}</b>
          <button class="weg" :class="{ zeker: wis === o.i }" type="button" data-test="fles-verwijder"
                  aria-label="Verkoopregel verwijderen" @click="verwijder(o)">{{ wis === o.i ? 'Zeker?' : '✕' }}</button>
        </div>
      </div>
    </div>
    <p v-if="melding" class="ok" role="status">{{ melding }}</p>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-top:14px}
h2{margin:0 0 12px;font-size:16px}
.rij{display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:140px}
input{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
input:focus{border-color:var(--coral)}
.knop{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer}
.knop:disabled{opacity:.6}
.teller{margin-top:14px;border-top:1px solid var(--line);padding-top:14px}
.tegels{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.tegel{flex:1;min-width:110px;background:#faf7f2;border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:flex;flex-direction:column;gap:2px}
.tegel b{font-size:20px;color:var(--coral)}
.tegel span{font-size:11.5px;color:var(--grey);font-weight:700}
.loglijst{margin-top:12px;display:flex;flex-direction:column;gap:4px}
.logrij{display:flex;align-items:center;gap:12px;font-size:13px;padding:6px 0;border-bottom:1px solid var(--line)}
.logrij:last-child{border-bottom:0}
.logrij b{flex:1}
.weg{background:none;border:0;color:var(--grey);cursor:pointer;font-size:13px}
.weg:hover{color:#b3261e}
.weg.zeker{color:#b3261e;font-weight:800}
.fout{color:#b3261e;font-size:13px}
.mijlpaal{background:var(--green-soft);border:1px solid #bcd9a0;color:#2c5a12;border-radius:10px;padding:8px 12px;font-size:13px;margin:8px 0}
.ok{color:#2c5a12;font-size:13px;margin:8px 0 0}
.breed{flex:2;min-width:200px}
select{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
select:focus{border-color:var(--coral)}
.schema{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:10px 14px;border-radius:12px;background:var(--soft);border:1px solid var(--line);margin-top:12px}
.schema.op{background:#f2f8ec;border-color:#cfe3b8}
.schema .lbl{display:block;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:var(--grey)}
.schema b{font-size:17px;font-variant-numeric:tabular-nums}
.pil{color:#fff;background:var(--coral-d);font-size:11.5px;font-weight:800;border-radius:6px;padding:3px 10px}
.pil.op{background:var(--green)}
.schema .mo{color:var(--grey);font-size:12px;flex:1;min-width:140px}
.doelbalk{margin-top:12px}
.dinfo{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:13.5px;font-weight:700}
.dinfo .mo{color:var(--grey);font-weight:400;font-size:13px}
.track{height:8px;border-radius:6px;background:#f0ebe3;overflow:hidden;margin-top:5px}
.fill{height:100%;background:var(--coral)}
.fill.af{background:var(--green)}
.blk-t{font-weight:800;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--grey);margin-top:16px;margin-bottom:8px}
.week7{display:grid;grid-template-columns:repeat(7,1fr);gap:6px}
.dag{text-align:center;border:1.5px solid var(--line);border-radius:12px;padding:7px 4px;background:#fff}
.dag.vandaag{border-color:var(--coral);background:var(--soft)}
.dag .wd{font-size:10px;font-weight:800;text-transform:uppercase;color:var(--grey)}
.dag.vandaag .wd{color:var(--coral-d)}
.dag .dm{font-size:9.5px;color:var(--grey)}
.dag input{width:100%;text-align:center;font-weight:800;font-size:15px;padding:5px 2px;margin-top:5px;border:1px solid var(--line);border-radius:8px}
.dag input:focus{border-color:var(--coral)}
</style>
