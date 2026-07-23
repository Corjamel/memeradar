<script setup>
// Logboek & bezoeken bij één winkel (v71). AM/kantoor schrijft verslagen en
// plant bezoeken; afspraken zijn ook voor de partner zichtbaar én afvinkbaar.
import { computed, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import {
  LOG_TYPES, fmtDuur, logToevoegen, logNextDone, logVerwijder, dagenSindsBezoek, bezoekStil,
  BEZOEK_RITME_DAGEN, afsprakenOpen, afspraakToevoegen, afspraakDone,
  planBezoek, registreerBezoek, visitOpenClaims
} from '../logic.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const emit = defineEmits(['bijgewerkt'])
const auth = useAuth()
const st = useTappunten()
const vandaag = new Date().toISOString().slice(0, 10)

const fout = ref('')
const bezig = ref(false)
const wis = ref(null)
const vorm = reactive({ type: 'bezoek', at: vandaag, txt: '', nextDate: '', dir: 'uit', duurMin: '' })
const afspraakTekst = ref('')
const planDatum = ref('')

const t = computed(() => props.tappunt)
const log = computed(() => t.value.logboek || [])
const dagen = computed(() => dagenSindsBezoek(t.value))
const stil = computed(() => bezoekStil(t.value))
const open = computed(() => afsprakenOpen(t.value))
const klaar = computed(() => (t.value.afspraken || []).filter(a => a.done).slice(0, 3))
const claims = computed(() => visitOpenClaims(t.value))

async function bewaar(t2) {
  bezig.value = true; fout.value = ''
  try { await st.bewaar(t2); emit('bijgewerkt', t2) }
  catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function schrijf() {
  if (bezig.value) return
  const res = logToevoegen(t.value, vorm)
  if (!res) { fout.value = 'Schrijf eerst een verslag of notitie.'; return }
  await bewaar(res.t2)
  Object.assign(vorm, { type: 'bezoek', at: vandaag, txt: '', nextDate: '', dir: 'uit', duurMin: '' })
}

async function vinkNext(e, v) { await bewaar(logNextDone(t.value, e.id, v)) }
async function verwijder(e) {
  if (wis.value !== e.id) { wis.value = e.id; return }
  wis.value = null
  await bewaar(logVerwijder(t.value, e.id))
}
async function plan() { if (planDatum.value) { await bewaar(planBezoek(t.value, planDatum.value)); planDatum.value = '' } }
async function checkin() {
  const res = registreerBezoek(t.value)
  if (res) await bewaar(res.t2)
}
async function nieuweAfspraken() {
  const t2 = afspraakToevoegen(t.value, afspraakTekst.value)
  if (!t2) return
  await bewaar(t2)
  afspraakTekst.value = ''
}
async function vinkAfspraak(a, v) {
  await bewaar(afspraakDone(t.value, a.id, v, auth.isPartner ? 'partner' : 'am'))
}
</script>

<template>
  <section class="blok">
    <div class="kop">
      <h2>🗓️ Bezoeken & logboek</h2>
      <span class="badge" :class="stil ? 'amber' : 'groen'" data-test="bezoek-ritme">
        {{ dagen == null ? 'nog nooit bezocht' : (stil ? `⚠ ${dagen} dgn niet bezocht (drempel ${BEZOEK_RITME_DAGEN})` : `laatste bezoek ${dagen} dgn geleden`) }}
      </span>
    </div>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Bezoek plannen / registreren (AM/kantoor) -->
    <div v-if="!auth.isPartner" class="planrij">
      <span v-if="claims" class="badge amber" data-test="claims-banner">✋ {{ claims }} geclaimde punt(en) wachten op controle bij een bezoek</span>
      <span v-if="t.bezoekGepland" class="mo" data-test="bezoek-gepland">Gepland: <b>{{ t.bezoekGepland }}</b></span>
      <input v-model="planDatum" type="date" aria-label="Bezoekdatum plannen" data-test="plan-datum" />
      <button class="klein" type="button" :disabled="!planDatum || bezig" data-test="plan-knop" @click="plan">Plan bezoek</button>
      <button class="klein" type="button" :disabled="bezig" data-test="checkin-knop" @click="checkin">📍 Bezoek registreren (vandaag)</button>
    </div>

    <!-- Afspraken -->
    <h3>📌 Afspraken met de winkel</h3>
    <label v-for="a in open" :key="a.id" class="afspraak" :data-test="'afspraak-' + a.id">
      <input type="checkbox" :disabled="bezig" @change="vinkAfspraak(a, $event.target.checked)" />
      <span>{{ a.txt }} <i class="mo">· {{ a.at }}</i></span>
    </label>
    <p v-if="!open.length" class="stil">Geen open afspraken ✓</p>
    <div v-for="a in klaar" :key="a.id" class="afspraak af">
      ✓ {{ a.txt }} <i class="mo">· {{ a.doneAt }}{{ a.doneBy === 'partner' ? ' · door de winkel' : '' }}</i>
    </div>
    <div v-if="!auth.isPartner" class="afsvorm">
      <textarea v-model="afspraakTekst" rows="2" data-test="afspraak-tekst"
                placeholder="Nieuwe afspraken — één per regel"></textarea>
      <button class="klein" type="button" :disabled="bezig" data-test="afspraak-toevoegen" @click="nieuweAfspraken">Vastleggen</button>
    </div>

    <!-- Logboek (AM/kantoor) -->
    <template v-if="!auth.isPartner">
      <h3>Logboek</h3>
      <form class="vorm" @submit.prevent="schrijf">
        <select v-model="vorm.type" aria-label="Soort" data-test="log-type">
          <option v-for="(v, k) in LOG_TYPES" :key="k" :value="k">{{ v.ic }} {{ v.l }}</option>
        </select>
        <select v-if="vorm.type === 'mail'" v-model="vorm.dir" aria-label="Mailrichting" data-test="log-dir">
          <option value="uit">↑ verstuurd</option>
          <option value="in">↓ ontvangen</option>
        </select>
        <input v-if="vorm.type === 'bezoek'" v-model="vorm.duurMin" type="number" min="0" placeholder="duur (min)"
               aria-label="Bezoekduur in minuten" class="duurin" data-test="log-duur" />
        <input v-model="vorm.at" type="date" aria-label="Datum" />
        <input v-model="vorm.txt" placeholder="verslag of notitie…" class="lang" data-test="log-tekst" />
        <label class="next">opvolgen op <input v-model="vorm.nextDate" type="date" data-test="log-next" /></label>
        <button class="btn" type="submit" :disabled="bezig" data-test="log-toevoegen">Toevoegen</button>
      </form>
      <div v-for="e in log.slice(0, 8)" :key="e.id" class="rij" data-test="log-rij">
        <span class="soort" :style="{ background: LOG_TYPES[e.type]?.bg, color: LOG_TYPES[e.type]?.fg }">{{ LOG_TYPES[e.type]?.ic }} {{ LOG_TYPES[e.type]?.l }}</span>
        <span v-if="e.dir" class="mdir" :class="e.dir" data-test="log-mdir">{{ e.dir === 'in' ? '↓ ontvangen' : '↑ verstuurd' }}</span>
        <a v-if="e.gps" class="gps" :href="'https://maps.google.com/?q=' + e.gps.lat + ',' + e.gps.lng" target="_blank" rel="noopener noreferrer"
           :title="'Locatiestempel' + (e.gps.loc ? ' · ' + e.gps.loc : '')">📍<span v-if="e.gps.loc" class="mo"> {{ e.gps.loc }}</span></a>
        <span v-if="e.duurMin != null" class="duur" data-test="log-duur-badge">⏱ {{ fmtDuur(e.duurMin) }}</span>
        <span class="datum">{{ e.at }}</span>
        <span class="txt">{{ e.txt }}</span>
        <label v-if="e.nextDate" class="opvolg" :class="{ af: e.nextDone }">
          <input type="checkbox" :checked="e.nextDone" :disabled="bezig" :data-test="'log-next-' + e.id"
                 @change="vinkNext(e, $event.target.checked)" />
          opvolgen {{ e.nextDate }}
        </label>
        <button class="wisknop" type="button" :data-test="'log-wis-' + e.id"
                :aria-label="'Logregel verwijderen van ' + e.at" @click="verwijder(e)">
          {{ wis === e.id ? 'Zeker?' : '×' }}
        </button>
      </div>
      <p v-if="!log.length" class="stil">Nog geen logboekregels.</p>
      <p v-if="log.length > 8" class="mo">… en nog {{ log.length - 8 }} oudere regels.</p>
    </template>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-top:14px}
.kop{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
h2{margin:0;font-size:16px;flex:1}
h3{margin:16px 0 6px;font-size:12px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--grey)}
.badge{font-size:11.5px;font-weight:800;border-radius:6px;padding:3px 10px}
.badge.groen{background:var(--green-soft);color:#2c5a12}
.badge.amber{background:var(--amber);color:#412402}
.planrij{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:10px}
.mo{color:var(--grey);font-size:12.5px;font-style:normal}
.klein{background:none;border:1.5px solid var(--line);border-radius:8px;padding:5px 11px;font-size:12.5px;font-weight:700;color:var(--grey);cursor:pointer;white-space:nowrap}
.klein:hover{border-color:var(--coral);color:var(--coral-d)}
.klein:disabled{opacity:.5}
input,select,textarea{padding:7px 9px;border:1.5px solid var(--line);border-radius:9px;font-size:13px;font-family:inherit}
input:focus,select:focus,textarea:focus{border-color:var(--coral)}
.afspraak{display:flex;align-items:flex-start;gap:9px;padding:6px 0;font-size:13.5px;cursor:pointer}
.afspraak input{width:16px;height:16px;accent-color:var(--coral);margin-top:1px}
.afspraak.af{color:var(--grey);cursor:default}
.afsvorm{display:flex;gap:8px;align-items:flex-start;margin-top:8px}
.afsvorm textarea{flex:1}
.vorm{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0 10px}
.lang{flex:1;min-width:180px}
.next{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--grey);font-weight:700}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:8px 14px;font-weight:800;cursor:pointer;font-size:13px}
.btn:disabled{opacity:.6}
.rij{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid var(--line);font-size:13.5px;flex-wrap:wrap}
.rij:last-of-type{border-bottom:0}
.soort{font-size:11px;font-weight:800;background:var(--cream);border-radius:6px;padding:2px 8px;white-space:nowrap}
.mdir,.duur{font-size:10.5px;font-weight:800;border-radius:6px;padding:2px 8px;white-space:nowrap}
.mdir.in{background:#dcd9e8;color:#3a2f5a}
.mdir.uit{background:#C0DD97;color:#173404}
.duur{background:var(--mist);color:#21343f}
.gps{text-decoration:none;font-size:13px;color:var(--coral-d);white-space:nowrap}
.duurin{max-width:110px}
.datum{color:var(--grey);font-size:12.5px;font-variant-numeric:tabular-nums}
.txt{flex:1;min-width:150px}
.opvolg{display:flex;align-items:center;gap:5px;font-size:12px;font-weight:700;color:var(--coral-d)}
.opvolg.af{color:var(--grey);text-decoration:line-through}
.opvolg input{width:15px;height:15px;accent-color:var(--coral)}
.wisknop{background:none;border:1.5px solid var(--line);border-radius:8px;padding:2px 9px;font-size:12px;font-weight:700;color:var(--coral-d);cursor:pointer}
.fout{color:#b3261e;font-size:13px}
.stil{color:var(--grey);font-size:13px}
</style>
