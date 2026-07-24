<script setup>
// Beheer — het kantoorpaneel, opgezet zoals v71: tabbladen per taakgebied.
// Mensen | Winkels | Instellingen | AVG & back-up | Audit
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import {
  haalAms, voegAmToe, verwijderAm, zetWinkelAm,
  haalCentral, bewaarCentral, haalLog, log, anonimiseer
} from '../api.js'
import { STANDAARD_MATEN } from '../../kassa/api.js'
import { eur0 } from '../../../lib/format.js'
import { LEVELS, NIVEAU_DREMPELS_STANDAARD, setNiveauDrempels } from '../../rekenhart/logic.js'

const auth = useAuth()
const st = useTappunten()
const tab = ref('mensen')
const TABS = [
  ['mensen', '🚗 Mensen'],
  ['winkels', '🏬 Winkels'],
  ['instellingen', '⚙️ Instellingen'],
  ['regels', '⚖️ Regels'],
  ['avg', '🔐 AVG & back-up'],
  ['audit', '📜 Audit']
]
// Regels-editor: ABCD-drempels (D=0 vast) + AM-score-weging.
const WEGING_STANDAARD = { groei: 35, activatie: 25, retentie: 20, data: 20 }
const regels = reactive({ drempels: [...NIVEAU_DREMPELS_STANDAARD], weging: { ...WEGING_STANDAARD } })
const NIVEAU_LABELS = LEVELS.map(l => l.k)

const ams = ref([])
const logboek = ref([])
const fout = ref('')
const melding = ref('')
const bezig = ref(false)
const nieuw = reactive({ naam: '', email: '' })
const wis = ref(null)            // twee-staps: AM verwijderen
const anon = ref(null)           // twee-staps: winkel anonimiseren
const inst = reactive({ maten: [], marge: 1, shopUrl: '', b2bUrl: '', b2bActief: false })
const mod = reactive({ game: true, kassa: true, producten: true })
const rechten = ref({})          // rechten-matrix kantoor-accounts (v71)
const RECHT_KEYS = ['acties', 'game', 'producten', 'team', 'analyse']   // v71 ALLE_RECHTEN
const rechtNieuw = reactive({ email: '', rol: 'kantoor' })

const wie = () => auth.user?.email || 'kantoor'
const AANTAL = computed(() => {
  const m = {}
  st.items.forEach(t => { if (t.am_id) m[t.am_id] = (m[t.am_id] || 0) + 1 })
  return m
})

async function laad() {
  fout.value = ''
  try {
    ams.value = await haalAms()
    if (!st.items.length) await st.laad()
    const m = await haalCentral('flesMaten')
    inst.maten = (Array.isArray(m) && m.length ? m : STANDAARD_MATEN).map(x => ({ ...x }))
    inst.marge = Number(await haalCentral('margeFactor')) || 1
    inst.shopUrl = String(await haalCentral('shopUrl') || '')
    const b2b = await haalCentral('b2bApi') || {}
    inst.b2bUrl = String(b2b.url || ''); inst.b2bActief = !!b2b.actief
    const mo = await haalCentral('modules') || {}
    mod.game = mo.game !== false; mod.kassa = mo.kassa !== false; mod.producten = mo.producten !== false
    rechten.value = (await haalCentral('kantoorRechten')) || {}
    const rg = (await haalCentral('regels')) || {}
    regels.drempels = Array.isArray(rg.drempels) && rg.drempels.length === NIVEAU_DREMPELS_STANDAARD.length
      ? rg.drempels.map(Number) : [...NIVEAU_DREMPELS_STANDAARD]
    regels.weging = { ...WEGING_STANDAARD, ...(rg.weging || {}) }
    logboek.value = await haalLog()
  } catch (e) { fout.value = 'Kon beheer niet laden: ' + e.message }
}
onMounted(laad)

function meld(m) { melding.value = m; fout.value = '' }

// ---- Mensen -----------------------------------------------------------
async function toevoegen() {
  if (bezig.value) return
  if (!nieuw.naam.trim() || !nieuw.email.trim()) { fout.value = 'Vul naam én e-mailadres in.'; return }
  bezig.value = true; fout.value = ''
  try {
    await voegAmToe(nieuw.naam.trim(), nieuw.email.trim())
    await log(wie(), `AM uitgenodigd: ${nieuw.naam.trim()} (${nieuw.email.trim()})`)
    meld(`✓ ${nieuw.naam.trim()} uitgenodigd.`)
    nieuw.naam = ''; nieuw.email = ''
    await laad()
  } catch (e) { fout.value = 'Toevoegen mislukt: ' + e.message }
  bezig.value = false
}

async function weg(a) {
  if (wis.value !== a) { wis.value = a; return }
  wis.value = null
  try {
    await verwijderAm(a.id)
    await log(wie(), `AM verwijderd: ${a.naam}`)
    await laad()
  } catch (e) { fout.value = 'Verwijderen mislukt: ' + e.message }
}

// ---- Rechten-matrix kantoor-accounts (central ns 'kantoorRechten') -----
async function rechtToevoegen() {
  const mail = rechtNieuw.email.trim().toLowerCase()
  if (!mail || bezig.value) return
  bezig.value = true; fout.value = ''
  try {
    const nieuweRechten = rechtNieuw.rol === 'beheer'
      ? { rol: 'beheer' }
      : { rol: 'kantoor', ...Object.fromEntries(RECHT_KEYS.map(k => [k, true])) }
    const m = { ...rechten.value, [mail]: nieuweRechten }
    await bewaarCentral('kantoorRechten', m)
    rechten.value = m
    await log(wie(), `Rechten vastgelegd: ${mail} = ${rechtNieuw.rol}`)
    meld(`✓ Rechten voor ${mail} vastgelegd.`)
    rechtNieuw.email = ''
  } catch (e) { fout.value = 'Vastleggen mislukt: ' + e.message }
  bezig.value = false
}

async function rechtZet(mail, k, v) {
  try {
    const m = { ...rechten.value, [mail]: { ...rechten.value[mail], [k]: !!v } }
    await bewaarCentral('kantoorRechten', m)
    rechten.value = m
    await log(wie(), `Rechten gewijzigd: ${mail} · ${k}=${v ? 'aan' : 'uit'}`)
  } catch (e) { fout.value = 'Wijzigen mislukt: ' + e.message }
}

async function rechtWeg(mail) {
  if (wis.value !== mail) { wis.value = mail; return }
  wis.value = null
  try {
    const m = { ...rechten.value }
    delete m[mail]
    await bewaarCentral('kantoorRechten', m)
    rechten.value = m
    await log(wie(), `Rechten-regel verwijderd: ${mail}`)
  } catch (e) { fout.value = 'Verwijderen mislukt: ' + e.message }
}

// ---- Winkels ----------------------------------------------------------
async function wijsToe(t, ev) {
  try {
    const amId = ev.target.value || null
    await zetWinkelAm(t.snelstart, amId)
    const naam = amId ? (ams.value.find(a => a.id === amId)?.naam || 'AM') : 'geen AM'
    await log(wie(), `Winkel ${t.name} toegewezen aan ${naam}`)
    await st.laad()
  } catch (e) { fout.value = 'Toewijzen mislukt: ' + e.message }
}

async function blok(t) {
  try {
    await st.blokkade(t.snelstart, !t.geblokkeerd)
    await log(wie(), `${t.geblokkeerd ? 'Geblokkeerd' : 'Gedeblokkeerd'}: ${t.name}`)
    meld(t.geblokkeerd ? `${t.name} geblokkeerd.` : `${t.name} gedeblokkeerd.`)
  } catch (e) { fout.value = 'Blokkeren mislukt: ' + e.message }
}

// ---- Regels-editor ----------------------------------------------------
const wegingTotaal = computed(() => Object.values(regels.weging).reduce((a, v) => a + (Number(v) || 0), 0))
async function regelsOpslaan() {
  fout.value = ''
  // D=0 vast; drempels moeten oplopend zijn.
  const d = regels.drempels.map((v, i) => i === 0 ? 0 : Math.max(0, Number(v) || 0))
  for (let i = 1; i < d.length; i++) if (d[i] < d[i - 1]) { fout.value = `Drempel ${NIVEAU_LABELS[i]} moet ≥ ${NIVEAU_LABELS[i - 1]} zijn.`; return }
  try {
    const cfg = { drempels: d, weging: { ...regels.weging } }
    await bewaarCentral('regels', cfg)
    setNiveauDrempels(d)              // direct actief in deze sessie
    auth.regels = cfg                 // AM-score-weging meteen live
    await log(wie(), 'Regels gewijzigd (ABCD-drempels / AM-score-weging)')
    meld('✓ Regels opgeslagen — direct actief voor het hele netwerk.')
  } catch (e) { fout.value = 'Regels opslaan mislukt: ' + e.message }
}
function regelsReset() {
  regels.drempels = [...NIVEAU_DREMPELS_STANDAARD]
  regels.weging = { ...WEGING_STANDAARD }
}

// ---- AVG & back-up ----------------------------------------------------
function download(naam, obj) {
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = naam
  a.click()
  URL.revokeObjectURL(a.href)
}

async function avgExport(t) {
  download(`AVG_export_${(t.name || t.snelstart).replace(/\W+/g, '_')}.json`, t)
  await log(wie(), `AVG-export gemaakt: ${t.name}`)
  meld(`✓ AVG-export van ${t.name} gedownload.`)
}

async function avgAnon(t) {
  if (anon.value !== t) { anon.value = t; return }   // twee-staps: dit wist ALLES
  anon.value = null
  try {
    await st.bewaar(anonimiseer(t))
    await st.blokkade(t.snelstart, true)
    await log(wie(), `AVG-anonimisering uitgevoerd: ${t.snelstart}`)
    meld('✓ Winkel geanonimiseerd en geblokkeerd (AVG).')
  } catch (e) { fout.value = 'Anonimiseren mislukt: ' + e.message }
}

async function backupExport() {
  const dump = {
    _tp: 'portaal-backup', at: new Date().toISOString(),
    tappunten: st.items,
    accountmanagers: ams.value,
    instellingen: { flesMaten: inst.maten, margeFactor: inst.marge, shopUrl: inst.shopUrl, modules: { ...mod }, b2bApi: { url: inst.b2bUrl, actief: inst.b2bActief } }
  }
  download(`TapParfum_backup_${new Date().toISOString().slice(0, 10)}.json`, dump)
  await log(wie(), 'Back-up gedownload')
  meld('✓ Back-up gedownload. (Supabase maakt daarnaast zelf dagelijkse back-ups.)')
}

// Back-up herstellen (v71 backupHerstel): leest een back-up-JSON en zet de
// netwerk-instellingen terug. Winkel-/AM-data blijft bewust ongemoeid — die
// leeft in de database en Supabase heeft daar eigen dagback-ups voor; we
// herstellen alleen de central-configuratie (veilig + omkeerbaar).
const herstelBezig = ref(false)
async function backupHerstel(ev) {
  const file = ev.target.files && ev.target.files[0]
  ev.target.value = ''
  if (!file) return
  herstelBezig.value = true; fout.value = ''
  try {
    const dump = JSON.parse(await file.text())
    if (dump._tp !== 'portaal-backup' || !dump.instellingen) throw new Error('Geen geldig TapParfum-back-upbestand.')
    const i = dump.instellingen
    if (Array.isArray(i.flesMaten)) { await bewaarCentral('flesMaten', i.flesMaten); inst.maten = i.flesMaten.map(x => ({ ...x })) }
    if (i.margeFactor != null) { await bewaarCentral('margeFactor', Number(i.margeFactor) || 1); inst.marge = Number(i.margeFactor) || 1 }
    if (i.shopUrl != null) { await bewaarCentral('shopUrl', String(i.shopUrl)); inst.shopUrl = String(i.shopUrl) }
    if (i.modules) { await bewaarCentral('modules', i.modules); mod.game = i.modules.game !== false; mod.kassa = i.modules.kassa !== false; mod.producten = i.modules.producten !== false }
    if (i.b2bApi) { await bewaarCentral('b2bApi', i.b2bApi); inst.b2bUrl = String(i.b2bApi.url || ''); inst.b2bActief = !!i.b2bApi.actief }
    await log(wie(), 'Back-up hersteld (netwerk-instellingen)')
    meld('✓ Netwerk-instellingen hersteld uit de back-up.')
  } catch (e) { fout.value = 'Herstellen mislukt: ' + e.message }
  herstelBezig.value = false
}

// ---- Instellingen -----------------------------------------------------
async function instellingenOpslaan() {
  fout.value = ''
  try {
    await bewaarCentral('flesMaten', inst.maten.map(x => ({ m: x.m, p: Number(x.p) || 0 })))
    await bewaarCentral('margeFactor', Number(inst.marge) || 1)
    await bewaarCentral('shopUrl', inst.shopUrl.trim())
    await bewaarCentral('b2bApi', { url: inst.b2bUrl.trim(), actief: !!inst.b2bActief })
    await bewaarCentral('modules', { game: !!mod.game, kassa: !!mod.kassa, producten: !!mod.producten })
    await log(wie(), 'Netwerk-instellingen gewijzigd')
    meld('✓ Instellingen opgeslagen — direct actief voor het hele netwerk.')
  } catch (e) { fout.value = 'Instellingen opslaan mislukt: ' + e.message }
}

function tijd(x) { return x && x.at ? String(x.at).slice(0, 16).replace('T', ' ') : '—' }
</script>

<template>
  <div>
    <h1>Beheer</h1>
    <p class="sub">Het kantoorpaneel — mensen, winkels, instellingen, AVG en audit.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <p v-if="melding" class="ok" role="status">{{ melding }}</p>

    <div class="tabs" role="tablist">
      <button v-for="[k, lbl] in TABS" :key="k" type="button" role="tab"
              :class="{ aan: tab === k }" :aria-selected="tab === k"
              :data-test="'tab-' + k" @click="tab = k; wis = null; anon = null">{{ lbl }}</button>
    </div>

    <!-- ===== MENSEN ===== -->
    <template v-if="tab === 'mensen'">
      <div class="kaart">
        <h2>Accountmanagers</h2>
        <form class="rij vorm" @submit.prevent="toevoegen">
          <label>Naam<input v-model="nieuw.naam" required placeholder="bijv. Marian" data-test="am-naam" /></label>
          <label>E-mailadres<input v-model="nieuw.email" type="email" required placeholder="marian@tapparfum.nl" data-test="am-email" /></label>
          <button class="knop" type="submit" :disabled="bezig" data-test="am-toevoegen">+ Uitnodigen</button>
        </form>
        <p class="note">De accountmanager gaat zelf naar het portaal → <b>Eerste keer? Account aanmaken</b> → "Ik ben
          accountmanager" → registreert met precies dít e-mailadres. Koppeling is automatisch en server-bewaakt.</p>

        <div v-for="a in ams" :key="a.id" class="rij item" data-test="am-rij">
          <b>{{ a.naam }}</b>
          <span class="mo">{{ a.email || '—' }}</span>
          <span class="badge" :class="a.auth_user_id ? 'groen' : 'wacht'" data-test="am-status">
            {{ a.auth_user_id ? '✓ gekoppeld' : 'uitgenodigd' }}
          </span>
          <span class="mo">{{ AANTAL[a.id] || 0 }} winkel{{ (AANTAL[a.id] || 0) === 1 ? '' : 's' }}</span>
          <button class="weg" :class="{ zeker: wis === a }" type="button" data-test="am-verwijder"
                  aria-label="Accountmanager verwijderen" @click="weg(a)">{{ wis === a ? 'Zeker?' : '✕' }}</button>
        </div>
        <p v-if="!ams.length" class="stil">Nog geen accountmanagers uitgenodigd.</p>
      </div>
      <div class="kaart">
        <h2>Kantoor-collega's & rechten</h2>
        <p class="note">Extra kantoor-logins maak je (nog) in Supabase: Authentication → Add user → daarna App metadata
          <code>{"role":"staff"}</code>. Vraag je beheerder of gebruik het account-script.</p>
        <p class="note">Hieronder de <b>rechten-matrix</b> (v71): rol <b>beheer</b> ziet en mag alles; rol <b>kantoor</b>
          krijgt alleen de aangevinkte onderdelen in het menu. Een account zonder regel = volledige rechten.</p>

        <form class="rij vorm" @submit.prevent="rechtToevoegen">
          <label>E-mailadres kantoor-account<input v-model="rechtNieuw.email" type="email" required placeholder="collega@retail-brands.nl" data-test="recht-email" /></label>
          <label>Rol
            <select v-model="rechtNieuw.rol" data-test="recht-rol">
              <option value="beheer">beheer (alles)</option>
              <option value="kantoor">kantoor (matrix)</option>
            </select>
          </label>
          <button class="knop" type="submit" :disabled="bezig" data-test="recht-toevoegen">+ Vastleggen</button>
        </form>

        <div v-for="(r, mail) in rechten" :key="mail" class="rij item" data-test="recht-rij">
          <b>{{ mail }}</b>
          <span class="badge" :class="r.rol === 'beheer' ? 'groen' : 'wacht'">{{ r.rol }}</span>
          <template v-if="r.rol !== 'beheer'">
            <label v-for="k in RECHT_KEYS" :key="k" class="vink">
              <input type="checkbox" :checked="r[k] !== false" :data-test="'recht-' + k + '-' + mail"
                     @change="rechtZet(mail, k, $event.target.checked)" /> {{ k }}
            </label>
          </template>
          <span class="spacer"></span>
          <button class="weg" :class="{ zeker: wis === mail }" type="button" :data-test="'recht-weg-' + mail"
                  aria-label="Rechten-regel verwijderen" @click="rechtWeg(mail)">{{ wis === mail ? 'Zeker?' : '✕' }}</button>
        </div>
        <p v-if="!Object.keys(rechten).length" class="stil">Nog geen rechten-regels — elk staff-account heeft nu volledige rechten.</p>
      </div>
    </template>

    <!-- ===== WINKELS ===== -->
    <template v-else-if="tab === 'winkels'">
      <div class="kaart">
        <h2>Winkels — toewijzen & toegang</h2>
        <div v-for="t in st.items" :key="t.snelstart" class="rij item" data-test="winkel-rij">
          <b>{{ t.name }}</b>
          <span class="mo">{{ t.snelstart }} · {{ eur0(t.jaaromzet) }}</span>
          <span v-if="t.geblokkeerd" class="badge zwart" data-test="winkel-blok-badge">geblokkeerd</span>
          <span class="spacer"></span>
          <select class="amsel" :value="t.am_id || ''" :aria-label="'Accountmanager voor ' + t.name"
                  data-test="winkel-am" @change="wijsToe(t, $event)">
            <option value="">— geen AM —</option>
            <option v-for="a in ams" :key="a.id" :value="a.id">{{ a.naam }}</option>
          </select>
          <button class="klein" :class="{ rood: !t.geblokkeerd }" type="button" data-test="winkel-blok"
                  @click="blok(t)">{{ t.geblokkeerd ? 'deblokkeer' : 'blokkeer' }}</button>
        </div>
        <p v-if="!st.items.length" class="stil">Nog geen winkels.</p>
      </div>
    </template>

    <!-- ===== INSTELLINGEN ===== -->
    <template v-else-if="tab === 'instellingen'">
      <div class="kaart">
        <h2>Kassaprijzen</h2>
        <div class="rij vorm">
          <label v-for="(x, i) in inst.maten" :key="x.m">{{ x.m }}
            <input v-model="x.p" type="number" min="0" step="0.5" :data-test="'inst-prijs-' + i" />
          </label>
        </div>
      </div>
      <div class="kaart">
        <h2>Netwerk</h2>
        <div class="rij vorm">
          <label>Marge-factor (inkoop → winkelomzet)
            <input v-model="inst.marge" type="number" min="0.1" step="0.1" data-test="inst-marge" />
          </label>
          <label>Bestelportaal-URL
            <input v-model="inst.shopUrl" type="url" placeholder="https://bestel.tapparfum.nl…" data-test="inst-shopurl" />
          </label>
        </div>
      </div>
      <div class="kaart">
        <h2>B2B-koppeling</h2>
        <p class="note">De URL van het B2B-portaal voor de klant-/ordersynchronisatie. Zet 'm aan zodra de koppeling live is.</p>
        <div class="rij vorm">
          <label>B2B-API-URL
            <input v-model="inst.b2bUrl" type="url" placeholder="https://b2b.retail-brands.nl/api…" data-test="inst-b2b-url" />
          </label>
          <label class="schakel b2b"><input v-model="inst.b2bActief" type="checkbox" data-test="inst-b2b-actief" /> Koppeling actief</label>
        </div>
      </div>
      <div class="kaart">
        <h2>Modules aan/uit</h2>
        <p class="note">Uitzetten verbergt de module in het hele netwerk — data blijft bewaard.</p>
        <div class="rij">
          <label class="schakel"><input v-model="mod.kassa" type="checkbox" data-test="mod-kassa" /> 🧾 Kassa</label>
          <label class="schakel"><input v-model="mod.game" type="checkbox" data-test="mod-game" /> 🏆 Sales Game</label>
          <label class="schakel"><input v-model="mod.producten" type="checkbox" data-test="mod-producten" /> 🧴 Producten</label>
        </div>
      </div>
      <div class="rij">
        <button class="knop" type="button" data-test="inst-opslaan" @click="instellingenOpslaan">Instellingen opslaan</button>
      </div>
    </template>

    <!-- ===== REGELS ===== -->
    <template v-else-if="tab === 'regels'">
      <div class="kaart">
        <h2>ABCD-omzetdrempels</h2>
        <p class="note">De jaaromzet (× marge = winkelomzet) waarop een winkel een niveau bereikt. D is altijd 0; elk niveau moet ≥ het vorige zijn. Direct van invloed op status, beloningen en de cockpit.</p>
        <div class="rij vorm">
          <label v-for="(k, i) in NIVEAU_LABELS" :key="k">Niveau {{ k }}
            <input v-if="i === 0" type="number" value="0" disabled />
            <input v-else v-model="regels.drempels[i]" type="number" min="0" step="500" :data-test="'regel-drempel-' + k" />
          </label>
        </div>
      </div>
      <div class="kaart">
        <h2>AM-score-weging</h2>
        <p class="note">Hoe zwaar elk onderdeel meetelt in de accountmanager-score. Richtlijn: samen 100.
          <b :class="{ amber: wegingTotaal !== 100 }">nu {{ wegingTotaal }}</b>.</p>
        <div class="rij vorm">
          <label>Groei<input v-model="regels.weging.groei" type="number" min="0" data-test="regel-weging-groei" /></label>
          <label>Activaties<input v-model="regels.weging.activatie" type="number" min="0" data-test="regel-weging-activatie" /></label>
          <label>Retentie (bezoekritme)<input v-model="regels.weging.retentie" type="number" min="0" data-test="regel-weging-retentie" /></label>
          <label>Datakwaliteit<input v-model="regels.weging.data" type="number" min="0" data-test="regel-weging-data" /></label>
        </div>
      </div>
      <div class="rij">
        <button class="knop" type="button" data-test="regels-opslaan" @click="regelsOpslaan">Regels opslaan</button>
        <button class="knop ghost" type="button" data-test="regels-reset" @click="regelsReset">Terug naar standaard</button>
      </div>
    </template>

    <!-- ===== AVG & BACK-UP ===== -->
    <template v-else-if="tab === 'avg'">
      <div class="kaart">
        <h2>Back-up</h2>
        <p class="note">Downloadt alle winkels, accountmanagers en instellingen als JSON. Supabase maakt daarnaast zelf
          dagelijkse database-back-ups.</p>
        <div class="rij">
          <button class="knop" type="button" data-test="backup-export" @click="backupExport">⬇ Back-up downloaden</button>
          <label class="knop ghost" :class="{ bezig: herstelBezig }">
            {{ herstelBezig ? 'Bezig…' : '⬆ Back-up herstellen' }}
            <input type="file" accept="application/json,.json" data-test="backup-herstel" style="display:none" @change="backupHerstel" />
          </label>
        </div>
        <p class="note" style="margin-top:8px">Herstellen zet de <b>netwerk-instellingen</b> (kassaprijzen, marge, portaal-URL, modules, B2B) terug uit een back-upbestand. Winkel- en AM-gegevens blijven ongemoeid — die staan veilig in de database.</p>
      </div>
      <div class="kaart">
        <h2>AVG per winkel</h2>
        <p class="note"><b>Export</b> levert alle vastgelegde gegevens van één winkel (inzagerecht). <b>Wis</b> anonimiseert
          de winkel onomkeerbaar en blokkeert de toegang (recht op vergetelheid) — exact de v71-veldenlijst.</p>
        <div v-for="t in st.items" :key="t.snelstart" class="rij item" data-test="avg-rij">
          <b>{{ t.name }}</b>
          <span class="mo">{{ t.snelstart }}</span>
          <span class="spacer"></span>
          <button class="klein" type="button" data-test="avg-export" @click="avgExport(t)">⬇ AVG-export</button>
          <button class="klein rood" :class="{ zeker: anon === t }" type="button" data-test="avg-anon"
                  @click="avgAnon(t)">{{ anon === t ? 'Zeker? Dit wist alles' : 'wis (AVG)' }}</button>
        </div>
      </div>
    </template>

    <!-- ===== AUDIT ===== -->
    <template v-else>
      <div class="kaart">
        <h2>Audit-log <span class="mo">· laatste 25 beheeracties</span></h2>
        <div v-for="l in logboek" :key="l.id" class="rij item" data-test="audit-rij">
          <span class="mo tijd">{{ tijd(l) }}</span>
          <b class="mo">{{ l.wie || '—' }}</b>
          <span>{{ l.txt }}</span>
        </div>
        <p v-if="!logboek.length" class="stil">Nog geen beheeracties vastgelegd.</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 12px;font-size:16px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.tabs button{background:#fff;border:1.5px solid var(--line);border-radius:10px;padding:8px 14px;font-weight:800;font-size:13px;color:var(--grey);cursor:pointer}
.tabs button.aan{border-color:var(--coral);background:var(--soft);color:var(--coral-d)}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:14px}
.rij{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.vorm{align-items:flex-end;margin-bottom:8px}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:140px}
label.schakel{flex-direction:row;align-items:center;gap:8px;font-size:13.5px;color:var(--ink);min-width:150px}
label.schakel input{width:17px;height:17px;accent-color:var(--coral)}
input,select{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
input:focus,select:focus{border-color:var(--coral)}
.knop{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer}
.knop:hover{background:var(--coral-d)}
.knop:disabled{opacity:.6}
.note{font-size:12.5px;color:var(--grey);background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:0 0 10px}
.note code{background:#fff;border:1px solid var(--line);border-radius:4px;padding:1px 5px}
.item{padding:9px 0;border-bottom:1px solid var(--line);font-size:14px}
.item:last-of-type{border-bottom:0}
.mo{color:var(--grey);font-size:12.5px}
.tijd{min-width:118px;font-variant-numeric:tabular-nums}
.spacer{flex:1}
.badge{font-size:11.5px;font-weight:800;border-radius:6px;padding:2px 10px}
.badge.groen{background:var(--green-soft);color:#2c5a12}
.badge.wacht{background:var(--soft);color:var(--coral-d)}
.badge.zwart{background:#333;color:#fff}
.amsel{max-width:180px}
.klein{background:none;border:1.5px solid var(--line);border-radius:8px;padding:5px 11px;font-size:12px;font-weight:700;color:var(--grey);cursor:pointer}
.klein:hover{border-color:var(--coral);color:var(--coral-d)}
.klein.rood{color:#b3261e}
.klein.rood:hover,.klein.zeker{border-color:#b3261e;color:#b3261e;font-weight:800}
.weg{background:none;border:0;color:var(--grey);cursor:pointer;font-size:14px}
.weg:hover,.weg.zeker{color:#b3261e;font-weight:800}
.fout{color:#b3261e}
.ok{color:#2c5a12;background:#f4faf0;border-radius:8px;padding:8px 10px;font-size:13.5px}
.stil{color:var(--grey);font-size:13px}
.vink{display:flex;flex-direction:row;align-items:center;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);cursor:pointer;min-width:0;flex:none}
.vink input{width:15px;height:15px;accent-color:var(--coral)}
.knop.ghost{background:#fff;color:var(--ink);border:1.5px solid var(--line);display:inline-flex;align-items:center;gap:6px;cursor:pointer}
.knop.ghost:hover{border-color:var(--coral);color:var(--coral)}
.knop.ghost.bezig{opacity:.6}
</style>
