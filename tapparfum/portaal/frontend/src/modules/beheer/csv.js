// Tappunten-CSV — klantenbestand in één keer binnenhalen (v71 parseTappuntCSV).
// Puur parsen; het wegschrijven doet BeheerView via bewaarTappunt (RLS bewaakt
// dat alleen kantoor mag schrijven). Kolom "naam" (of tappunt/winkel/name) is
// verplicht; de rest is optioneel. Scheidingsteken ; of , wordt geraden.

function normDatumOpt(d) {
  d = String(d || '').trim()
  if (!d) return ''
  // dd-mm-jjjj of dd/mm/jjjj -> jjjj-mm-dd; ISO laten we staan.
  const m = d.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})$/)
  if (m) {
    const jaar = m[3].length === 2 ? '20' + m[3] : m[3]
    return `${jaar}-${String(m[2]).padStart(2, '0')}-${String(m[1]).padStart(2, '0')}`
  }
  return /^\d{4}-\d{2}-\d{2}/.test(d) ? d.slice(0, 10) : ''
}

// ---- Kolomkoppeling (interactieve import) --------------------------------
// De import toont eerst het bestand met een koppelscherm: elke doelkolom
// krijgt een dropdown met de CSV-kolommen, voorgeraden met de heuristiek
// hieronder. Zo werkt élk klantenbestand, ongeacht de kolomnamen.

export const CSV_DOELVELDEN = [
  ['name', 'Winkelnaam', true],
  ['snelstart', 'Code / klantnummer', false],
  ['contact', 'Contactpersoon', false],
  ['email', 'E-mailadres', false],
  ['tel', 'Telefoon', false],
  ['adres', 'Adres', false],
  ['postcode', 'Postcode', false],
  ['plaats', 'Plaats', false],
  ['land', 'Land', false],
  ['type', 'Type / segment', false],
  ['laatsteBezoek', 'Laatste bezoek', false],
  ['jaaromzet', 'Jaaromzet (dit jaar)', false],
  ['vorigJaar', 'Omzet vorig jaar', false],
  ['am', 'Accountmanager (naam)', false]
]

const VELD_HINTS = {
  name: ['naam', 'tappunt', 'winkel', 'name', 'klant'],
  snelstart: ['snelstart', 'code', 'klantnr', 'nummer'],
  contact: ['contact', 'eigenaar'],
  email: ['mail'],
  tel: ['tel', 'phone'],
  adres: ['adres', 'straat'],
  postcode: ['postcode', 'zip'],
  plaats: ['plaats', 'stad', 'city'],
  land: ['land', 'country'],
  type: ['type', 'segment'],
  laatsteBezoek: ['laatste bezoek', 'laatstebezoek', 'bezoek'],
  jaaromzet: ['jaaromzet', 'omzet dit jaar', 'omzet 20'],
  vorigJaar: ['vorig jaar', 'vorigjaar', 'omzet vorig'],
  am: ['accountmanager', 'account manager', 'vertegenwoordiger']
}

// Ruwe CSV: kopregel + rijen, scheidingsteken ; of , (meest voorkomende wint).
export function parseRuwCSV(text) {
  const lines = String(text || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean)
  if (lines.length < 2) return null
  const sep = (lines[0].split(';').length >= lines[0].split(',').length) ? ';' : ','
  const headers = lines[0].split(sep).map(h => h.trim())
  const rows = lines.slice(1).map(l => l.split(sep).map(c => c.trim()))
  return { headers, rows, sep }
}

// Raad per doelveld de best passende kolom (-1 = niet koppelen). Een kolom
// wordt maar één keer uitgedeeld — 'naam' wint van 'accountmanager' bij 'am'.
export function raadKoppeling(headers) {
  const H = headers.map(h => String(h).toLowerCase())
  const map = {}
  const bezet = new Set()
  CSV_DOELVELDEN.forEach(([veld]) => {
    // 'am' alleen als exacte kolomnaam — anders zou elke *naam*-kolom matchen.
    const i = H.findIndex((h, ix) => !bezet.has(ix) &&
      ((VELD_HINTS[veld] || []).some(n => h.indexOf(n) >= 0) || (veld === 'am' && h === 'am')))
    map[veld] = i
    if (i >= 0) bezet.add(i)
  })
  return map
}

// Bouwt uit een gekoppelde rij hetzelfde object als parseTappuntCSV.
export function rijViaKoppeling(cellen, map) {
  const g = veld => (map[veld] >= 0 ? (cellen[map[veld]] || '').trim() : '')
  const num = s => { const n = Number(String(s).replace(/[^\d,.-]/g, '').replace(',', '.')); return isFinite(n) && n > 0 ? Math.round(n) : 0 }
  return {
    name: g('name'), snelstart: g('snelstart'), tel: g('tel'), land: g('land'),
    laatsteBezoek: normDatumOpt(g('laatsteBezoek')),
    contact: g('contact'), email: g('email'), adres: g('adres'),
    postcode: g('postcode'), plaats: g('plaats'), type: g('type'),
    jaaromzet: num(g('jaaromzet')), vorigJaar: num(g('vorigJaar')), amNaam: g('am')
  }
}

export function parseTappuntCSV(text) {
  const lines = String(text || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean)
  if (lines.length < 2) return []
  const sep = (lines[0].split(';').length >= lines[0].split(',').length) ? ';' : ','
  const H = lines[0].toLowerCase().split(sep).map(h => h.trim())
  const idx = ns => H.findIndex(h => ns.some(n => h.indexOf(n) >= 0))
  const iN = idx(['naam', 'tappunt', 'winkel', 'name'])
  const iS = idx(['snelstart', 'code', 'klantnr'])
  const iT = idx(['tel', 'phone'])
  const iL = idx(['land', 'country'])
  const iB = idx(['laatste bezoek', 'laatstebezoek', 'bezoek'])
  const iC = idx(['contact', 'eigenaar'])
  const iE = idx(['mail'])
  const iA = idx(['adres', 'straat'])
  const iP = idx(['postcode'])
  const iPl = idx(['plaats', 'stad', 'city'])
  const iTy = idx(['type', 'segment'])
  if (iN < 0) return []
  return lines.slice(1).map(l => {
    const c = l.split(sep)
    const g = i => i >= 0 ? (c[i] || '').trim() : ''
    return {
      name: g(iN), snelstart: g(iS), tel: g(iT), land: g(iL),
      laatsteBezoek: iB >= 0 ? normDatumOpt(c[iB]) : '',
      contact: g(iC), email: g(iE), adres: g(iA), postcode: g(iP), plaats: g(iPl), type: g(iTy)
    }
  }).filter(r => r.name)
}

// Bouwt uit een CSV-rij een compleet tappunt-object (zelfde veldopbouw als een
// handmatig toegevoegde winkel; opstart overgeslagen want de winkel draait al).
export function rijNaarNieuwTappunt(r, vandaag) {
  const dag = vandaag || new Date().toISOString().slice(0, 10)
  return {
    snelstart: r.snelstart || ('csv-' + Math.random().toString(36).slice(2, 8)),
    name: r.name, tel: r.tel || '', land: r.land || 'NL', liveDate: dag, traject: false,
    email: r.email || '', adres: r.adres || '', postcode: r.postcode || '', plaats: r.plaats || '',
    type: r.type || '', display: '', bezoekmoment: '', web: '', jarig: '', contact: r.contact || '',
    notes: '', setup: { done: {}, skipped: true }, forms: {}, fu: {}, jaaromzet: 0, joLog: [],
    klanten: 0, bp: {}, bonus: {}, vorigJaar: 0, react: [], pakket: '', statusManual: '', doel: 0,
    open: false, laatsteBezoek: r.laatsteBezoek || '', bron: 'csv'
  }
}

// Variant voor de kolomkoppeling: neemt ook omzetvelden mee als die gekoppeld zijn.
export function rijNaarTappuntGekoppeld(r, vandaag) {
  const t = rijNaarNieuwTappunt(r, vandaag)
  if (r.jaaromzet) t.jaaromzet = r.jaaromzet
  if (r.vorigJaar) t.vorigJaar = r.vorigJaar
  return t
}
