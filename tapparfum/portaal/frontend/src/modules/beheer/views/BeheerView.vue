<script setup>
// Beheer — het kantoorpaneel, opgezet zoals v71: tabbladen per taakgebied.
// Mensen | Winkels | Instellingen | AVG & back-up | Audit
import Icoon from '../../../components/Icoon.vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useToast } from '../../../stores/toast.js'
import { useTappunten } from '../../tappunten/store.js'
import {
  haalAms, voegAmToe, verwijderAm, zetWinkelAm,
  haalCentral, bewaarCentral, haalLog, log, anonimiseer
} from '../api.js'
import { STANDAARD_MATEN } from '../../kassa/api.js'
import { parseRuwCSV, raadKoppeling, rijViaKoppeling, rijNaarTappuntGekoppeld, CSV_DOELVELDEN } from '../csv.js'
import { BRAND_STD, applyBrand } from '../../../lib/brand.js'
import { eur0 } from '../../../lib/format.js'
import { LEVELS, NIVEAU_DREMPELS_STANDAARD, setNiveauDrempels, winkelOmzet, jaaromzet } from '../../rekenhart/logic.js'

const auth = useAuth()
const toast = useToast()
const st = useTappunten()
const tab = ref('mensen')
// Tabs 1-op-1 in v71-lijn: Instellingen is opgesplitst in Merk & design,
// Modules, Regie en Systeem (i.p.v. één gebundelde Instellingen-tab).
const TABS = [
  ['mensen', 'Mensen', 'users'],
  ['winkels', 'Winkels', 'tappunten'],
  ['merk', 'Merk & design', 'merk'],
  ['modules', 'Modules', 'gear'],
  ['regie', 'Regie', 'doc'],
  ['systeem', 'Systeem', 'gear'],
  ['regels', 'Regels', 'proces'],
  ['teksten', 'Teksten', 'pen'],
  ['avg', 'AVG & back-up', 'slot'],
  ['audit', 'Audit', 'kennis']
]
// Schermtitels die kantoor mag herbenoemen (v71 title.<route>).
const TEKST_SCHERMEN = [
  ['home', 'Mijn winkels'], ['vandaag', 'Vandaag'], ['winkels', 'Winkels'], ['agenda', 'Agenda'],
  ['bezoeken', 'Bezoeken'], ['berichten', 'Berichten'], ['acties', 'Acties'], ['beloningen', 'Beloningen'],
  ['game', 'Sales Game'], ['producten', 'Producten'], ['geuren', 'Geurbibliotheek'], ['community', 'Community'],
  ['academy', 'Academy'], ['kennisbank', 'Kennisbank'], ['analyse', 'Analyse'], ['team', 'Accountmanagers']
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
// Huisstijl (central 'brand'): logotekst + de vier merkkleuren.
const brand = reactive({ logoTekst: '', coral: BRAND_STD.coral, corald: BRAND_STD.corald, green: BRAND_STD.green, amber: BRAND_STD.amber })
function brandReset() {
  brand.logoTekst = ''
  brand.coral = BRAND_STD.coral; brand.corald = BRAND_STD.corald
  brand.green = BRAND_STD.green; brand.amber = BRAND_STD.amber
}
// Schermtitels (central 'teksten'): per route een override (leeg = standaard).
const tekst = reactive(Object.fromEntries(TEKST_SCHERMEN.map(([r]) => [r, ''])))
// Layout/regie (central 'layout'): content-uitlijning per rol (v71 bhAlign).
const ZONES = [['am', '🚗 Accountmanager'], ['partner', '🏪 Partner'], ['kantoor', '🏢 Kantoor']]
const align = reactive({ am: '', partner: '', kantoor: '' })
// Blokvolgorde partner-dashboard (v71 bhOrde): fase/week/trofee herschikken.
const BLOK_STD = ['fase', 'week', 'trofee']
const BLOK_LABEL = { fase: '📈 Fasekaart', week: '📅 Deze week', trofee: '🏆 Spaarcadeaus' }
const blokVolgorde = ref([...BLOK_STD])
function blokVerplaats(i, dir) {
  const j = i + dir
  if (j < 0 || j >= blokVolgorde.value.length) return
  const kopie = blokVolgorde.value.slice()
  ;[kopie[i], kopie[j]] = [kopie[j], kopie[i]]
  blokVolgorde.value = kopie
}
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
    const br = (await haalCentral('brand')) || {}
    brand.logoTekst = String(br.logoTekst || '')
    brand.coral = br.coral || BRAND_STD.coral; brand.corald = br.corald || BRAND_STD.corald
    brand.green = br.green || BRAND_STD.green; brand.amber = br.amber || BRAND_STD.amber
    const tk = (await haalCentral('teksten')) || {}
    TEKST_SCHERMEN.forEach(([r]) => { tekst[r] = String(tk['title.' + r] || '') })
    const la = (await haalCentral('layout')) || {}
    const al = la.align || {}
    align.am = al.am === 'midden' ? 'midden' : ''
    align.partner = al.partner === 'midden' ? 'midden' : ''
    align.kantoor = al.kantoor === 'midden' ? 'midden' : ''
    const vp = la.volgorde && la.volgorde.partner
    blokVolgorde.value = (Array.isArray(vp) && vp.length === BLOK_STD.length && BLOK_STD.every(k => vp.includes(k)))
      ? vp.slice() : [...BLOK_STD]
    logboek.value = await haalLog()
  } catch (e) { fout.value = 'Kon beheer niet laden: ' + e.message }
}
onMounted(laad)

function meld(m) { melding.value = m; fout.value = ''; toast.ok(m.replace(/^✓\s*/, '')) }

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

// ---- CSV-import van winkels: bestand kiezen -> kolommen koppelen -> import
const csvBezig = ref(false)
const csvMelding = ref('')
const csvFout = ref('')
const csvData = ref(null)              // { headers, rows } na het kiezen
const csvNaam = ref('')                // bestandsnaam (voor het koppelscherm)
const csvMap = reactive({})            // doelveld -> kolomindex (-1 = niet)
const csvVasteAm = ref('')             // fallback: alles naar deze AM

async function csvKies(ev) {
  csvMelding.value = ''; csvFout.value = ''
  const f = ev.target && ev.target.files && ev.target.files[0]
  if (!f) return
  try {
    const ruw = parseRuwCSV(await f.text())
    if (!ruw) { csvFout.value = 'Geen bruikbare regels — het bestand heeft een kopregel en minstens één rij nodig.'; return }
    csvData.value = ruw
    csvNaam.value = f.name
    const geraden = raadKoppeling(ruw.headers)
    Object.keys(geraden).forEach(k => { csvMap[k] = geraden[k] })
    csvVasteAm.value = ''
  } catch (e) {
    csvFout.value = 'Bestand lezen mislukt: ' + e.message
  } finally {
    if (ev.target) ev.target.value = ''    // zelfde bestand nogmaals kunnen kiezen
  }
}
function csvAnnuleer() { csvData.value = null; csvNaam.value = '' }
const csvPreview = computed(() => csvData.value ? csvData.value.rows.slice(0, 3) : [])
// AM op naam vinden (case-insensitief, ook als de CSV alleen de voornaam heeft).
function vindAm(naam) {
  const n = String(naam || '').trim().toLowerCase()
  if (!n) return null
  return ams.value.find(a => String(a.naam).toLowerCase() === n)
    || ams.value.find(a => String(a.naam).toLowerCase().indexOf(n) >= 0 || n.indexOf(String(a.naam).toLowerCase()) >= 0)
    || null
}

async function csvVoerUit() {
  if (!csvData.value || csvBezig.value) return
  if (csvMap.name < 0) { csvFout.value = 'Koppel eerst de kolom voor de winkelnaam — die is verplicht.'; return }
  csvBezig.value = true; csvMelding.value = ''; csvFout.value = ''
  try {
    // Dubbele winkels overslaan op code of naam (case-insensitief).
    const codes = new Set(st.items.map(t => String(t.snelstart || '').toLowerCase()))
    const namen = new Set(st.items.map(t => String(t.name || '').toLowerCase()))
    let ok = 0, dup = 0, metAm = 0
    for (const cellen of csvData.value.rows) {
      const r = rijViaKoppeling(cellen, csvMap)
      if (!r.name) continue
      const code = String(r.snelstart || '').toLowerCase()
      const naam = String(r.name || '').toLowerCase()
      if ((code && codes.has(code)) || namen.has(naam)) { dup++; continue }
      const t = rijNaarTappuntGekoppeld(r)
      await st.bewaar(t)                   // RLS: alleen kantoor mag schrijven
      // AM-koppeling: kolom uit het bestand wint; anders de vaste keuze.
      const am = vindAm(r.amNaam) || (csvVasteAm.value ? ams.value.find(a => a.id === csvVasteAm.value) : null)
      if (am) { await zetWinkelAm(t.snelstart, am.id); metAm++ }
      codes.add(String(t.snelstart).toLowerCase()); namen.add(naam)
      ok++
    }
    await st.laad()
    if (ok) await log(wie(), `CSV-import: ${ok} winkels toegevoegd${metAm ? `, ${metAm} aan een AM gekoppeld` : ''}${dup ? `, ${dup} overgeslagen` : ''}`)
    csvMelding.value = `✓ ${ok} winkel${ok === 1 ? '' : 's'} geïmporteerd${metAm ? ` · ${metAm} gekoppeld aan een accountmanager` : ''}${dup ? ` · ${dup} bestond al (overgeslagen)` : ''}.`
    if (ok) toast.ok(`${ok} winkel${ok === 1 ? '' : 's'} geïmporteerd`)
    csvAnnuleer()
  } catch (e) {
    csvFout.value = 'Import mislukt: ' + e.message
  } finally {
    csvBezig.value = false
  }
}

// ---- Export: klantenbestand als CSV ------------------------------------
function exporteerWinkels() {
  const kol = ['naam', 'code', 'contact', 'email', 'tel', 'adres', 'postcode', 'plaats', 'land', 'type', 'accountmanager', 'jaaromzet', 'vorig jaar', 'laatste bezoek', 'geblokkeerd']
  const naamVan = Object.fromEntries(ams.value.map(a => [a.id, a.naam]))
  const esc = v => { const s = String(v == null ? '' : v); return /[;"\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s }
  const regels = st.items.map(t => [
    t.name, t.snelstart, t.contact || '', t.email || '', t.tel || '', t.adres || '', t.postcode || '',
    t.plaats || '', t.land || '', t.type || '', naamVan[t.am_id] || '', t.jaaromzet || 0, t.vorigJaar || 0,
    t.laatsteBezoek || '', t.geblokkeerd ? 'ja' : ''
  ].map(esc).join(';'))
  const blob = new Blob(['﻿' + kol.join(';') + '\n' + regels.join('\n')], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'tapparfum-winkels-' + new Date().toISOString().slice(0, 10) + '.csv'
  a.click()
  URL.revokeObjectURL(a.href)
  log(wie(), `Klantenbestand geëxporteerd (${st.items.length} winkels)`).catch(() => {})
}

// ---- KPI-kop: het beheer in één oogopslag -------------------------------
const kpis = computed(() => {
  const zonderAm = st.items.filter(t => !t.am_id).length
  const blokN = st.items.filter(t => t.geblokkeerd).length
  const omzet = st.items.reduce((a, t) => a + (Number(t.jaaromzet) || 0), 0)
  const gekoppeld = ams.value.filter(a => a.auth_user_id).length
  return [
    ['winkels', st.items.length],
    ['jaaromzet (inkoop)', eur0(omzet)],
    ['accountmanagers', `${ams.value.length}` + (ams.value.length ? ` (${gekoppeld} actief)` : '')],
    ['zonder AM', zonderAm],
    ['geblokkeerd', blokN]
  ]
})

// ---- Regels-editor ----------------------------------------------------
const wegingTotaal = computed(() => Object.values(regels.weging).reduce((a, v) => a + (Number(v) || 0), 0))
// v71 (bhRegelsImpact): live veiligheidsnet — hoeveel winkels wisselen van niveau
// bij de nu ingevoerde drempels t.o.v. de actieve? Rekent op WINKELOMZET
// (inkoop × marge), net als levelOf, zodat kantoor niet blind drempels instelt
// die netwerkbreed direct doorwerken.
const niveauWissel = computed(() => {
  const oud = LEVELS.map(l => l.min)
  const nieuw = regels.drempels.map((v, i) => i === 0 ? 0 : Math.max(0, Number(v) || 0))
  if (oud.every((v, i) => v === nieuw[i])) return { veranderd: false, n: 0, vb: [] }
  const idx = (wo, mins) => { let i = 0; for (let j = 0; j < mins.length; j++) if (wo >= mins[j]) i = j; return i }
  const vb = []
  let n = 0
  st.items.forEach(t => {
    const wo = winkelOmzet(t, inst.marge)
    const a = idx(wo, oud), b = idx(wo, nieuw)
    if (a !== b) { n++; if (vb.length < 6) vb.push(`${t.name || t.snelstart} (${LEVELS[a].k}→${LEVELS[b].k})`) }
  })
  return { veranderd: true, n, vb }
})
async function regelsOpslaan() {
  fout.value = ''
  // D=0 vast; drempels moeten oplopend zijn.
  const d = regels.drempels.map((v, i) => i === 0 ? 0 : Math.max(0, Number(v) || 0))
  for (let i = 1; i < d.length; i++) if (d[i] < d[i - 1]) { fout.value = `Drempel ${NIVEAU_LABELS[i]} moet ≥ ${NIVEAU_LABELS[i - 1]} zijn.`; return }
  // v71 (bhRegelsSave): de AM-score-weging moet samen 100 zijn, anders draait de
  // ranking op een niet-genormaliseerde weging.
  if (wegingTotaal.value !== 100) { fout.value = `De AM-score-weging moet samen 100 zijn (nu ${wegingTotaal.value}).`; return }
  try {
    const weging = { ...regels.weging }
    // Merge i.p.v. overschrijven: central 'regels' kan (uit v71-migratie) óók
    // rewards-/actDagen-overrides bevatten — die mogen niet gewist worden door
    // het opslaan van drempels/weging.
    const bestaand = (await haalCentral('regels')) || {}
    const cfg = { ...bestaand, drempels: d, weging }
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
  // v71 (kSetMarge): de marge-factor moet groter dan 0 zijn — een 0/negatieve
  // waarde zou een corrupte config wegschrijven (niveaus vallen stil terug op ×1).
  const m = Number(inst.marge)
  if (!(m > 0)) { fout.value = 'Marge-factor moet groter dan 0 zijn (bijv. 2).'; return }
  try {
    await bewaarCentral('flesMaten', inst.maten.map(x => ({ m: x.m, p: Number(x.p) || 0 })))
    await bewaarCentral('margeFactor', m)
    await bewaarCentral('shopUrl', inst.shopUrl.trim())
    await bewaarCentral('b2bApi', { url: inst.b2bUrl.trim(), actief: !!inst.b2bActief })
    await bewaarCentral('modules', { game: !!mod.game, kassa: !!mod.kassa, producten: !!mod.producten })
    // Huisstijl: alleen afwijkingen van de standaard bewaren (leeg = standaard).
    const br = {}
    if (brand.logoTekst.trim()) br.logoTekst = brand.logoTekst.trim()
    ;['coral', 'corald', 'green', 'amber'].forEach(k => {
      if (String(brand[k]).toLowerCase() !== String(BRAND_STD[k]).toLowerCase()) br[k] = brand[k]
    })
    await bewaarCentral('brand', br)
    applyBrand(br)                       // kleuren meteen live
    // Layout/regie: gecentreerde zones + afwijkende partner-blokvolgorde bewaren.
    const alignObj = {}
    ZONES.forEach(([z]) => { if (align[z] === 'midden') alignObj[z] = 'midden' })
    const layoutObj = {}
    if (Object.keys(alignObj).length) layoutObj.align = alignObj
    if (blokVolgorde.value.join(',') !== BLOK_STD.join(',')) layoutObj.volgorde = { partner: blokVolgorde.value.slice() }
    await bewaarCentral('layout', layoutObj)
    try { window.dispatchEvent(new CustomEvent('tp-brand')) } catch (e) { /* logo/layout volgt bij herladen */ }
    await log(wie(), 'Netwerk-instellingen gewijzigd')
    meld('✓ Instellingen opgeslagen — direct actief voor het hele netwerk.')
  } catch (e) { fout.value = 'Instellingen opslaan mislukt: ' + e.message }
}

async function tekstenOpslaan() {
  fout.value = ''
  try {
    const obj = {}
    TEKST_SCHERMEN.forEach(([r, std]) => {
      const v = String(tekst[r] || '').trim()
      if (v && v !== std) obj['title.' + r] = v      // alleen echte afwijkingen bewaren
    })
    await bewaarCentral('teksten', obj)
    try { window.dispatchEvent(new CustomEvent('tp-brand')) } catch (e) { /* volgt bij herladen */ }
    await log(wie(), 'Schermteksten aangepast')
    meld('✓ Schermteksten opgeslagen — direct actief voor het hele netwerk.')
  } catch (e) { fout.value = 'Teksten opslaan mislukt: ' + e.message }
}
function tekstenReset() { TEKST_SCHERMEN.forEach(([r]) => { tekst[r] = '' }) }

function tijd(x) { return x && x.at ? String(x.at).slice(0, 16).replace('T', ' ') : '—' }
</script>

<template>
  <div>
    <header class="vheld"><div>
      <p class="eyebrow">Kantoorpaneel</p>
      <h1>Beheer</h1>
      <p class="sub">Het kantoorpaneel — mensen, winkels, instellingen, AVG en audit.</p>
    </div></header>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
    <p v-if="melding" class="ok" role="status">{{ melding }}</p>

    <!-- KPI-kop: het netwerk in één oogopslag -->
    <div class="kpis" data-test="beheer-kpis">
      <div v-for="[lbl, val] in kpis" :key="lbl" class="kpi">
        <b>{{ val }}</b><span>{{ lbl }}</span>
      </div>
    </div>

    <!-- Beveiligingsstatus — eerlijk overzicht (v71). Anders dan v71 (dat een
         schermslot op het apparaat was) is de beveiliging hier écht: Supabase
         Row Level Security dwingt op de server af wie welke rij ziet/wijzigt. -->
    <div class="veiligblok" data-test="beheer-veilig">
      <div class="vh"><Icoon naam="slot" /> Beveiligingsstatus — eerlijk overzicht</div>
      <p><b>Echt beveiligd (server, niet weg te klikken):</b> Postgres Row Level Security bepaalt per rij wie leest en schrijft — een AM ziet alleen zijn eigen winkels, een partner alleen zijn eigen winkel, kantoor alles. Wachtwoorden staan versleuteld bij Supabase Auth; wachtwoord-reset loopt via e-mail. Beschermde velden (geblokkeerd · snelstart · am_id · auth_user_id) zijn voor niet-staff nooit te wijzigen.</p>
      <p class="mo"><b>Dit paneel is de bediening, niet de grens:</b> wat je hier ziet stuurt de UX; de echte grens ligt bij RLS. Deel nooit de service-role-sleutel — die omzeilt RLS. Zet het Supabase-project op <b>je eigen account</b>, dan raak je dit nooit kwijt.</p>
    </div>

    <div class="tabs" role="tablist">
      <button v-for="[k, lbl, ic] in TABS" :key="k" type="button" role="tab"
              :class="{ aan: tab === k }" :aria-selected="tab === k"
              :data-test="'tab-' + k" @click="tab = k; wis = null; anon = null"><Icoon :naam="ic" /> {{ lbl }}</button>
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

      <!-- CSV-import met kolomkoppeling: bestand kiezen -> koppelen -> import -->
      <div class="kaart">
        <h2><Icoon naam="importeer" /> Winkels importeren (CSV)</h2>
        <template v-if="!csvData">
          <p class="note">Kies je klantenbestand (Excel: opslaan als CSV). Daarna koppel je zelf de kolommen aan de juiste velden — het maakt dus niet uit hoe de kolommen in jouw bestand heten. Bestaande winkels (zelfde code of naam) worden overgeslagen, nooit gedupliceerd.</p>
          <label class="csvknop" :class="{ bezig: csvBezig }">
            📄 Kies een CSV-bestand
            <input type="file" accept=".csv,text/csv" data-test="csv-input" :disabled="csvBezig" @change="csvKies" />
          </label>
        </template>

        <template v-else>
          <p class="note" data-test="csv-koppel"><b>{{ csvNaam }}</b> · {{ csvData.rows.length }} rijen gevonden.
            Koppel hieronder de kolommen — ik heb ze alvast zo goed mogelijk herkend. Alleen de <b>winkelnaam</b> is verplicht.</p>
          <div class="koppels">
            <label v-for="[veld, lbl, verplicht] in CSV_DOELVELDEN" :key="veld" class="koppel">
              <span>{{ lbl }}<b v-if="verplicht" class="ster">*</b></span>
              <select v-model.number="csvMap[veld]" :data-test="'csv-map-' + veld">
                <option :value="-1">— niet importeren —</option>
                <option v-for="(h, i) in csvData.headers" :key="i" :value="i">{{ h || ('kolom ' + (i + 1)) }}</option>
              </select>
            </label>
          </div>
          <label class="koppel vast">
            <span>Geen AM-kolom? Wijs alles toe aan</span>
            <select v-model="csvVasteAm" data-test="csv-vaste-am">
              <option value="">— geen accountmanager —</option>
              <option v-for="a in ams" :key="a.id" :value="a.id">{{ a.naam }}</option>
            </select>
          </label>
          <div class="tabelwrap">
            <table class="preview">
              <thead><tr><th v-for="(h, i) in csvData.headers" :key="i">{{ h || 'kolom ' + (i + 1) }}</th></tr></thead>
              <tbody><tr v-for="(r, ri) in csvPreview" :key="ri"><td v-for="(c, ci) in r" :key="ci">{{ c }}</td></tr></tbody>
            </table>
          </div>
          <div class="knoppenrij">
            <button class="knop" type="button" :disabled="csvBezig" data-test="csv-import-uitvoeren" @click="csvVoerUit">
              {{ csvBezig ? 'Bezig met importeren…' : `✓ Importeer ${csvData.rows.length} rijen` }}
            </button>
            <button class="klein" type="button" :disabled="csvBezig" data-test="csv-annuleer" @click="csvAnnuleer">Annuleren</button>
          </div>
        </template>
        <p v-if="csvMelding" class="ok" role="status" data-test="csv-melding">{{ csvMelding }}</p>
        <p v-if="csvFout" class="fout" role="alert" data-test="csv-fout">{{ csvFout }}</p>
      </div>

      <!-- Export: het hele klantenbestand als CSV (back-up of Excel-analyse) -->
      <div class="kaart">
        <h2><Icoon naam="exporteer" /> Winkels exporteren (CSV)</h2>
        <p class="note">Alle winkels met contactgegevens, accountmanager en omzet — voor een back-up of om in Excel verder te werken.</p>
        <button class="knop" type="button" data-test="csv-export" @click="exporteerWinkels">⬇ Download klantenbestand ({{ st.items.length }})</button>
      </div>
    </template>

    <!-- ===== MERK & DESIGN (v71-tab) — huisstijl: merkkleuren + logotekst ===== -->
    <template v-else-if="tab === 'merk'">
      <div class="kaart">
        <h2>🎨 Huisstijl</h2>
        <p class="note">Merkkleuren en logotekst voor het hele netwerk. Contrastbewaking maakt een te lichte tekstkleur automatisch leesbaar. Leeg = standaard TapParfum-huisstijl.</p>
        <div class="rij vorm">
          <label>Logotekst<input v-model="brand.logoTekst" maxlength="20" placeholder="TAPPARFUM" data-test="brand-logo" /></label>
          <label>Accent (koraal)<input v-model="brand.coral" type="color" data-test="brand-coral" /></label>
          <label>Accent donker (tekst)<input v-model="brand.corald" type="color" data-test="brand-corald" /></label>
          <label>Groen (succes)<input v-model="brand.green" type="color" data-test="brand-green" /></label>
          <label>Amber (aandacht)<input v-model="brand.amber" type="color" data-test="brand-amber" /></label>
        </div>
        <div class="rij">
          <span class="brandvoor" :style="{ background: brand.coral, color: '#fff' }" data-test="brand-preview">Voorbeeld-accent</span>
          <button class="knop ghost" type="button" data-test="brand-reset" @click="brandReset">Terug naar standaard</button>
        </div>
      </div>
      <div class="rij">
        <button class="knop" type="button" data-test="inst-opslaan" @click="instellingenOpslaan">Instellingen opslaan</button>
      </div>
    </template>

    <!-- ===== MODULES (v71-tab) — netwerkbreed aan/uit ===== -->
    <template v-else-if="tab === 'modules'">
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

    <!-- ===== REGIE (v71-tab) — volgorde & uitlijning ===== -->
    <template v-else-if="tab === 'regie'">
      <div class="kaart">
        <h2>📐 Layout</h2>
        <p class="note">Standaard staat de inhoud links (breed werkscherm). Gecentreerd geeft een smallere, gecentreerde kolom — rustiger voor lees-schermen. Per rol in te stellen.</p>
        <div class="rij vorm">
          <label v-for="[z, lbl] in ZONES" :key="z">{{ lbl }}
            <select v-model="align[z]" :data-test="'align-' + z">
              <option value="">Links (standaard)</option>
              <option value="midden">Gecentreerd</option>
            </select>
          </label>
        </div>
        <h3 class="subkop">Blokvolgorde partner-dashboard</h3>
        <p class="note">De volgorde van de drie hoofdblokken op het partner-dashboard. Bovenaan verschijnt bovenaan.</p>
        <ol class="blokorder">
          <li v-for="(k, i) in blokVolgorde" :key="k" :data-test="'blok-' + k">
            <span class="bl">{{ BLOK_LABEL[k] }}</span>
            <span class="pijlen">
              <button type="button" class="mini" :disabled="i === 0" :data-test="'blok-op-' + k" aria-label="Omhoog" @click="blokVerplaats(i, -1)">▲</button>
              <button type="button" class="mini" :disabled="i === blokVolgorde.length - 1" :data-test="'blok-neer-' + k" aria-label="Omlaag" @click="blokVerplaats(i, 1)">▼</button>
            </span>
          </li>
        </ol>
      </div>
      <div class="rij">
        <button class="knop" type="button" data-test="inst-opslaan" @click="instellingenOpslaan">Instellingen opslaan</button>
      </div>
    </template>

    <!-- ===== SYSTEEM (v71-tab) — prijzen, netwerk & koppelingen ===== -->
    <template v-else-if="tab === 'systeem'">
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
        <!-- Live impact-preview (v71 bhRegelsImpact): hoeveel winkels wisselen van
             niveau bij deze drempels, vóór opslaan (dat direct netwerkbreed live gaat). -->
        <p v-if="niveauWissel.veranderd" class="impact" data-test="regel-impact">
          <template v-if="niveauWissel.n === 0">Geen enkele winkel wisselt van niveau bij deze drempels.</template>
          <template v-else><b>{{ niveauWissel.n }}</b> winkel{{ niveauWissel.n === 1 ? '' : 's' }} wisselt van niveau — o.a. {{ niveauWissel.vb.join(' · ') }}{{ niveauWissel.n > niveauWissel.vb.length ? ' …' : '' }}</template>
        </p>
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

    <!-- ===== TEKSTEN ===== -->
    <template v-else-if="tab === 'teksten'">
      <div class="kaart">
        <h2>✏️ Schermtitels</h2>
        <p class="note">Herbenoem de schermen in het menu en de topbalk voor het hele netwerk. Leeg = de standaardnaam. Handig om het portaal op jullie eigen woorden af te stemmen.</p>
        <div class="tekstlijst">
          <label v-for="[r, std] in TEKST_SCHERMEN" :key="r" class="tekstrij">
            <span class="tstd">{{ std }}</span>
            <input v-model="tekst[r]" :placeholder="std" :data-test="'tekst-' + r" maxlength="40" />
          </label>
        </div>
        <div class="rij">
          <button class="knop" type="button" data-test="teksten-opslaan" @click="tekstenOpslaan">Teksten opslaan</button>
          <button class="knop ghost" type="button" data-test="teksten-reset" @click="tekstenReset">Terug naar standaard</button>
        </div>
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
.impact{font-size:12.5px;color:var(--coral-d);background:var(--soft);border:1px solid var(--peach);border-radius:10px;padding:9px 12px;margin:10px 0 0}
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
/* KPI-kop */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:14px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 14px}
.kpi b{display:block;font-size:17px}
.kpi span{color:var(--grey);font-size:11.5px}
/* Beveiligingsstatus — eerlijk overzicht (v71), amber-accent links */
.veiligblok{background:#fff;border:1px solid var(--line);border-left:4px solid var(--amber);border-radius:12px;padding:12px 16px;margin-bottom:14px}
.veiligblok .vh{display:flex;align-items:center;gap:8px;font-weight:800;font-size:13px;color:var(--amber);margin-bottom:6px}
.veiligblok .vh :deep(svg){width:16px;height:16px}
.veiligblok p{margin:0 0 6px;font-size:12.5px;line-height:1.55;color:var(--ink)}
.veiligblok p:last-child{margin-bottom:0}
.veiligblok p.mo{color:var(--grey)}
.veiligblok b{color:var(--ink)}
/* CSV-koppelscherm */
.koppels{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px 14px;margin:10px 0}
.koppel{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:12.5px;font-weight:700;color:var(--grey)}
.koppel select{flex-shrink:0;max-width:150px;padding:6px 8px;border:1.5px solid var(--line);border-radius:8px;font-size:12.5px;font-family:inherit}
.koppel.vast{background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin-bottom:10px;max-width:440px}
.ster{color:var(--coral-d)}
.tabelwrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin-bottom:10px}
.preview{border-collapse:collapse;font-size:12px;min-width:100%}
.preview th{background:var(--cream);text-align:left;padding:6px 10px;white-space:nowrap;font-size:11px;text-transform:uppercase;letter-spacing:.04em}
.preview td{padding:5px 10px;border-top:1px solid var(--line);white-space:nowrap}
.knoppenrij{display:flex;align-items:center;gap:10px}
.csvknop{display:inline-block;background:var(--coral);color:#fff;font-weight:800;font-size:13px;border-radius:10px;padding:10px 16px;cursor:pointer}
.csvknop:hover{background:var(--coral-d)}
.csvknop.bezig{opacity:.6;pointer-events:none}
.csvknop input{display:none}
.brandvoor{display:inline-flex;align-items:center;font-size:12px;font-weight:800;border-radius:8px;padding:8px 14px}
.subkop{font-size:13px;font-weight:800;margin:14px 0 2px}
.blokorder{list-style:none;margin:6px 0 0;padding:0;display:flex;flex-direction:column;gap:6px;max-width:360px}
.blokorder li{display:flex;align-items:center;gap:10px;background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:8px 12px}
.blokorder .bl{font-weight:700;font-size:13.5px}
.blokorder .pijlen{margin-left:auto;display:flex;gap:4px}
.blokorder .mini{width:28px;height:28px;border:1.5px solid var(--line);background:#fff;border-radius:7px;cursor:pointer;font-size:11px;color:var(--ink)}
.blokorder .mini:disabled{opacity:.35;cursor:default}
.blokorder .mini:not(:disabled):hover{border-color:var(--coral);color:var(--coral)}
.tekstlijst{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px;margin-bottom:12px}
.tekstrij{display:flex;flex-direction:column;gap:3px;font-size:11px;color:var(--grey)}
.tekstrij .tstd{text-transform:uppercase;letter-spacing:.4px;font-weight:800}
.tekstrij input{font-size:13.5px;padding:8px 10px;border:1.5px solid var(--line);border-radius:8px;color:var(--ink)}
input[type=color]{width:52px;height:34px;padding:2px;border:1.5px solid var(--line);border-radius:8px;background:#fff;cursor:pointer}
.vink{display:flex;flex-direction:row;align-items:center;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);cursor:pointer;min-width:0;flex:none}
.vink input{width:15px;height:15px;accent-color:var(--coral)}
.knop.ghost{background:#fff;color:var(--ink);border:1.5px solid var(--line);display:inline-flex;align-items:center;gap:6px;cursor:pointer}
.knop.ghost:hover{border-color:var(--coral);color:var(--coral)}
.knop.ghost.bezig{opacity:.6}
</style>
