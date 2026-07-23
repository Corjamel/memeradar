<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useTappunten } from '../store.js'
import { useAuth } from '../../../stores/auth.js'
import DocumentenBlok from '../../documenten/components/DocumentenBlok.vue'
import ContactenBlok from '../../contacten/components/ContactenBlok.vue'
import KassaBlok from '../../kassa/components/KassaBlok.vue'
import SetupBlok from '../../setup/components/SetupBlok.vue'
import PuntenBlok from '../../punten/components/PuntenBlok.vue'
import BeloningBlok from '../../beloningen/components/BeloningBlok.vue'
import BestellingenBlok from '../../bestellingen/components/BestellingenBlok.vue'
import LogboekBlok from '../../logboek/components/LogboekBlok.vue'
import SituatieBlok from '../components/SituatieBlok.vue'
import { haalRekenConfig } from '../../beloningen/api.js'
import VerkoopBlok from '../../verkoop/components/VerkoopBlok.vue'
import { eur0 } from '../../../lib/format.js'
import { jaaromzet, winkelOmzet, levelOf, statusKey, STATUS, groeiTxt } from '../../rekenhart/logic.js'
import { omzetGroei, monthsElapsed } from '../../punten/logic.js'

const props = defineProps({ code: { type: String, required: true } })
const st = useTappunten()
const auth = useAuth()

// Volledige v71-gegevensset (GEG_VELDEN).
const GEG = ['name', 'contact', 'tel', 'email', 'adres', 'postcode', 'plaats', 'land', 'type', 'display', 'bezoekmoment', 'web', 'jarig']
const WINKELTYPES = ['', 'Drogisterij', 'Kapper', 'Beauty / nagelsalon', 'Cadeau / boetiek', 'Kleding', 'Supermarkt / gemak', 'Tankstation', 'Overig']
const DISPLAYS = ['', 'Tapbar groot', 'Tapbar klein', 'Strip / hoekelement', 'Anders']
const vorm = reactive({ snelstart: '', name: '', contact: '', tel: '', email: '', adres: '', postcode: '', plaats: '', land: '', type: '', display: '', bezoekmoment: '', web: '', jarig: '' })
const bron = ref(null)
const melding = ref('')
const bezig = ref(false)
const marge = ref(1)

function vulVorm(t) {
  bron.value = t
  vorm.snelstart = t.snelstart || ''
  GEG.forEach(k => { vorm[k] = t[k] || '' })
}
// Compleetheid: hoeveel van de 13 velden zijn ingevuld?
const gegVol = computed(() => GEG.filter(k => String((bron.value || {})[k] || '').trim()).length)

// Kop-metrics (v71 metricrow r.2906) + volgende stap (v71 nextStep r.2796).
const jo = computed(() => bron.value ? winkelOmzet(bron.value, marge.value) : 0)
const lv = computed(() => levelOf(jaaromzet(bron.value || {}), marge.value))
const stat = computed(() => STATUS[statusKey(bron.value || {}, marge.value)] || STATUS.groeit)
const perMaand = computed(() => bron.value ? Math.round(jo.value / monthsElapsed(bron.value)) : 0)
const groei = computed(() => bron.value ? omzetGroei(bron.value) : null)
const volgendeStap = computed(() => {
  const t = bron.value
  if (!t) return ''
  const s = t.setup || {}
  if (!(s.done || s.skipped)) return 'Rond de opstart af met de winkel'
  if (jaaromzet(t) === 0) return 'Vul de huidige jaaromzet in'
  if (statusKey(t, marge.value) === 'stagneert') return 'Stagneert — plan een heractivatie'
  if (lv.value.next) return `Nog ${eur0(lv.value.gap)} tot niveau ${lv.value.next}`
  return 'Hoogste niveau bereikt — houd het vast'
})

onMounted(async () => {
  if (!st.items.length) await st.laad()
  const t = st.byCode(props.code)
  if (t) vulVorm(t)
  try { marge.value = (await haalRekenConfig()).marge } catch { /* factor 1 */ }
})

async function opslaan() {
  if (bezig.value || !bron.value) return
  bezig.value = true; melding.value = ''
  try {
    // beschermde velden (geblokkeerd/am_id) blijven van de bron — api stuurt ze nooit mee
    let t = { ...bron.value, ...vorm, snelstart: bron.value.snelstart }
    // v71: bij een partner-wijziging een logboekregel achterlaten voor de AM.
    if (auth.isPartner) {
      t = { ...t, logboek: [{ id: 'l' + Date.now().toString(36), at: new Date().toISOString().slice(0, 10), type: 'notitie', txt: '📇 Partner heeft de winkelgegevens bijgewerkt', nextDate: '', nextDone: false }, ...(t.logboek || [])] }
    }
    await st.bewaar(t)
    bron.value = t
    melding.value = '✓ Opgeslagen'
  } catch (e) { melding.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function wisselBlokkade() {
  if (!bron.value) return
  try {
    await st.blokkade(bron.value.snelstart, !bron.value.geblokkeerd)
    bron.value = st.byCode(bron.value.snelstart)
    melding.value = bron.value.geblokkeerd ? 'Winkel geblokkeerd.' : 'Winkel gedeblokkeerd.'
  } catch (e) { melding.value = 'Actie mislukt: ' + e.message }
}
</script>

<template>
  <div v-if="!bron" class="stil">
    <p>Winkel «{{ props.code }}» niet gevonden (of je hebt er geen toegang toe).</p>
    <router-link :to="{ name: 'winkels' }">← Terug naar winkels</router-link>
  </div>

  <div v-else>
    <router-link class="terug" :to="{ name: 'winkels' }">← Winkels</router-link>
    <div class="kaart">
      <div class="kop">
        <h1>{{ bron.name }}</h1>
        <span class="code">code {{ bron.snelstart }}</span>
        <span class="niveau" data-test="kop-niveau">{{ lv.k }}</span>
        <span class="badge sit" :style="{ background: stat.bg, color: stat.fg }">{{ stat.l }}</span>
        <span v-if="bron.geblokkeerd" class="badge" data-test="blok-badge">geblokkeerd</span>
      </div>

      <!-- Kerncijfers in één oogopslag (v71 metricrow) -->
      <div class="metricrow" data-test="metricrow">
        <div class="m"><span class="mv">{{ lv.k }}</span><span class="ml">Niveau</span></div>
        <div class="m"><span class="mv">{{ eur0(jo) }}</span><span class="ml">Jaaromzet</span></div>
        <div class="m"><span class="mv">{{ eur0(perMaand) }}</span><span class="ml">Per maand</span></div>
        <div class="m"><span class="mv" :class="{ up: groei > 0, down: groei < 0 }">{{ groeiTxt(groei) }}</span><span class="ml">Groei vs vorig jaar</span></div>
      </div>
      <div class="nextstep" data-test="volgende-stap">
        <span class="ns-t">Volgende stap</span>
        <span class="ns-h">{{ volgendeStap }}</span>
      </div>

      <p class="geg-teller" data-test="geg-teller">📇 Gegevens · {{ gegVol }}/13 ingevuld</p>
      <form class="vorm" @submit.prevent="opslaan">
        <label>Winkelnaam<input v-model="vorm.name" required data-test="geg-name" /></label>
        <label>Contactpersoon<input v-model="vorm.contact" data-test="geg-contact" /></label>
        <label>Telefoon<input v-model="vorm.tel" type="tel" /></label>
        <label>E-mail<input v-model="vorm.email" type="email" /></label>
        <label>Adres<input v-model="vorm.adres" /></label>
        <label>Postcode<input v-model="vorm.postcode" data-test="geg-postcode" /></label>
        <label>Plaats<input v-model="vorm.plaats" /></label>
        <label>Land<input v-model="vorm.land" placeholder="NL" /></label>
        <label>Winkeltype
          <select v-model="vorm.type" data-test="geg-type">
            <option v-for="o in WINKELTYPES" :key="o" :value="o">{{ o || '— kies —' }}</option>
          </select>
        </label>
        <label>Presentatie / display
          <select v-model="vorm.display">
            <option v-for="o in DISPLAYS" :key="o" :value="o">{{ o || '— kies —' }}</option>
          </select>
        </label>
        <label>Beste bezoekmoment<input v-model="vorm.bezoekmoment" placeholder="di/do-ochtend, niet za" /></label>
        <label>Website / Instagram<input v-model="vorm.web" placeholder="@winkel of url" /></label>
        <label>Verjaardag eigenaar<input v-model="vorm.jarig" type="date" data-test="geg-jarig" /></label>

        <div class="acties">
          <button class="btn" type="submit" :disabled="bezig">{{ bezig ? 'Bezig…' : 'Opslaan' }}</button>
          <button v-if="auth.isKantoor" class="btn donker" type="button" data-test="blok-knop" @click="wisselBlokkade">
            {{ bron.geblokkeerd ? 'Deblokkeer winkel' : 'Blokkeer winkel' }}
          </button>
          <span v-if="melding" class="melding" role="status">{{ melding }}</span>
        </div>
      </form>
    </div>

    <SituatieBlok v-if="!auth.isPartner" :tappunt="bron" :marge="marge" @bijgewerkt="bron = $event" />
    <SetupBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <KassaBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <VerkoopBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <PuntenBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <BeloningBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <BestellingenBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <LogboekBlok :tappunt="bron" @bijgewerkt="bron = $event" />
    <ContactenBlok :snelstart="bron.snelstart" />
    <DocumentenBlok :snelstart="bron.snelstart" />
  </div>
</template>

<style scoped>
.terug{display:inline-block;margin-bottom:10px;color:var(--coral);font-weight:700;text-decoration:none}
.kaart{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px}
.kop{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:14px}
h1{margin:0;font-size:20px}
.code{color:var(--grey);font-size:13px}
.badge{background:#333;color:#fff;font-size:11px;font-weight:700;border-radius:6px;padding:2px 8px}
.badge.sit{border-radius:6px}
.niveau{width:30px;height:30px;border-radius:9px;background:var(--coral);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:12.5px}
.metricrow{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);margin-bottom:12px}
.metricrow .m{padding:12px 14px;border-right:1px solid var(--line);display:flex;flex-direction:column;gap:3px}
.metricrow .m:last-child{border-right:0}
.metricrow .mv{font-size:20px;font-weight:800;letter-spacing:-.3px;font-variant-numeric:tabular-nums}
.metricrow .mv.up{color:var(--green)}.metricrow .mv.down{color:var(--coral-d)}
.metricrow .ml{font-size:10.5px;color:var(--grey);text-transform:uppercase;letter-spacing:.4px;font-weight:700}
@media(max-width:620px){.metricrow{grid-template-columns:repeat(2,1fr)}.metricrow .m:nth-child(2){border-right:0}}
.nextstep{display:flex;align-items:center;gap:12px;padding:11px 14px;background:var(--soft);border:1px solid var(--line);margin-bottom:14px}
.ns-t{font-size:10.5px;color:var(--coral-d);text-transform:uppercase;letter-spacing:.5px;font-weight:800;flex-shrink:0}
.ns-h{font-size:13.5px;font-weight:600}
.vorm{display:grid;grid-template-columns:1fr 1fr;gap:12px}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey)}
input{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px}
select{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
input:focus,select:focus{border-color:var(--coral)}
.geg-teller{margin:0 0 12px;font-size:12.5px;font-weight:700;color:var(--grey)}
.acties{grid-column:1 / -1;display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:6px}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer}
.btn.donker{background:#333}
.btn:disabled{opacity:.6}
.melding{font-size:13px;color:var(--grey)}
.stil{color:var(--grey)}
@media (max-width:640px){ .vorm{grid-template-columns:1fr} }
</style>
