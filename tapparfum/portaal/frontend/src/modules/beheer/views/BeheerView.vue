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

const auth = useAuth()
const st = useTappunten()
const tab = ref('mensen')
const TABS = [
  ['mensen', '🚗 Mensen'],
  ['winkels', '🏬 Winkels'],
  ['instellingen', '⚙️ Instellingen'],
  ['avg', '🔐 AVG & back-up'],
  ['audit', '📜 Audit']
]

const ams = ref([])
const logboek = ref([])
const fout = ref('')
const melding = ref('')
const bezig = ref(false)
const nieuw = reactive({ naam: '', email: '' })
const wis = ref(null)            // twee-staps: AM verwijderen
const anon = ref(null)           // twee-staps: winkel anonimiseren
const inst = reactive({ maten: [], marge: 1, shopUrl: '' })
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
    const mo = await haalCentral('modules') || {}
    mod.game = mo.game !== false; mod.kassa = mo.kassa !== false; mod.producten = mo.producten !== false
    rechten.value = (await haalCentral('kantoorRechten')) || {}
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
    instellingen: { flesMaten: inst.maten, margeFactor: inst.marge, shopUrl: inst.shopUrl, modules: { ...mod } }
  }
  download(`TapParfum_backup_${new Date().toISOString().slice(0, 10)}.json`, dump)
  await log(wie(), 'Back-up gedownload')
  meld('✓ Back-up gedownload. (Supabase maakt daarnaast zelf dagelijkse back-ups.)')
}

// ---- Instellingen -----------------------------------------------------
async function instellingenOpslaan() {
  fout.value = ''
  try {
    await bewaarCentral('flesMaten', inst.maten.map(x => ({ m: x.m, p: Number(x.p) || 0 })))
    await bewaarCentral('margeFactor', Number(inst.marge) || 1)
    await bewaarCentral('shopUrl', inst.shopUrl.trim())
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

    <!-- ===== AVG & BACK-UP ===== -->
    <template v-else-if="tab === 'avg'">
      <div class="kaart">
        <h2>Back-up</h2>
        <p class="note">Downloadt alle winkels, accountmanagers en instellingen als JSON. Supabase maakt daarnaast zelf
          dagelijkse database-back-ups.</p>
        <button class="knop" type="button" data-test="backup-export" @click="backupExport">⬇ Back-up downloaden</button>
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
</style>
