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
