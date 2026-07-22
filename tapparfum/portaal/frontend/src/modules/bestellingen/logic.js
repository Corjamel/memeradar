// Bestellingen-logica — EXACT v71 (r.1275-1313). Datamodel op het tappunt:
// t.bestellingen = [{id, at, ref, totaal (excl. btw), omschrijving,
// bron:'handmatig'|'csv'|'api'}] — nieuwste eerst, dedupe op ref.
// LET OP het onderscheid: jaaromzet = wat het tappunt aan consumenten verkoopt
// (flesLog); bestellingen = wat het tappunt bij TapParfum inkoopt.

export const bestellingenVan = (t) => t.bestellingen || []

export function inkoopJaar(t) {
  const y = String(new Date().getFullYear())
  return bestellingenVan(t).filter(b => String(b.at || '').slice(0, 4) === y)
    .reduce((a, b) => a + (+b.totaal || 0), 0)
}

export function laatsteBestelling(t) {
  const b = bestellingenVan(t)
  return b.length ? b[0].at : null
}

export function dagenSindsBestelling(t) {
  const d = laatsteBestelling(t)
  if (!d) return null
  const dt = new Date(d)
  if (isNaN(dt)) return null
  return Math.round((Date.now() - dt) / 864e5)
}

// v71-drempel: 60 dagen zonder bestelling = stil.
export const BESTEL_STIL_DAGEN = 60
export function bestelStil(t) {
  const d = dagenSindsBestelling(t)
  return d != null && d > BESTEL_STIL_DAGEN
}

// Europese bedragen: "€ 1.234,56", "1234,56" en "1.234" allemaal goed lezen.
export function euBedrag(v) {
  let x = String(v == null ? '' : v).replace(/[€\s]/g, '')
  if (!x) return 0
  if (x.indexOf('.') >= 0 && x.indexOf(',') >= 0) { x = x.replace(/\./g, '').replace(',', '.') }
  else if (x.indexOf(',') >= 0) { x = x.replace(',', '.') }
  else if (/^\d{1,3}(\.\d{3})+$/.test(x)) { x = x.replace(/\./g, '') }
  const n = parseFloat(x)
  return isNaN(n) ? 0 : n
}

export function normDatum(d) {
  d = String(d || '').trim()
  const m = d.match(/^(\d{2})[-/](\d{2})[-/](\d{4})$/)
  if (m) return m[3] + '-' + m[2] + '-' + m[1]
  return d || new Date().toISOString().slice(0, 10)
}

const uid = () => 'b' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7)

/* Bestelling toevoegen — puur: geeft de bijgewerkte kopie terug, of null bij
   een dubbel ordernummer (dedupe op ref, zoals v71). */
export function voegBestellingToe(t, o) {
  const lijst = [...bestellingenVan(t)]
  const ref = (o.ref || '').trim()
  if (ref && lijst.some(b => b.ref === ref)) return null
  lijst.unshift({
    id: uid(), at: normDatum(o.at), ref,
    totaal: Math.max(+o.totaal || 0, 0),
    omschrijving: (o.omschrijving || '').trim(),
    bron: o.bron || 'handmatig'
  })
  lijst.sort((a, b) => (a.at < b.at ? 1 : -1))
  return { ...t, bestellingen: lijst }
}

/* CSV: herkent ; of , en de kolommen datum · tappunt/klant/snelstart ·
   ordernr/ref · totaal/bedrag · omschrijving (exact de v71-herkenning). */
export function parseBestelCSV(text) {
  const lines = String(text || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean)
  if (lines.length < 2) return []
  const sep = (lines[0].split(';').length >= lines[0].split(',').length) ? ';' : ','
  const H = lines[0].toLowerCase().split(sep).map(h => h.trim())
  const idx = names => H.findIndex(h => names.some(n => h.indexOf(n) >= 0))
  const iD = idx(['datum', 'date']), iT = idx(['tappunt', 'klant', 'snelstart', 'winkel'])
  const iR = idx(['ordernr', 'order', 'ref', 'factuur']), iTot = idx(['totaal', 'bedrag', 'amount'])
  const iO = idx(['omschrijving', 'opmerking', 'descr'])
  if (iT < 0 || iTot < 0) return []
  return lines.slice(1).map(l => {
    const cells = l.split(sep)
    return {
      at: iD >= 0 ? (cells[iD] || '').trim() : '',
      tappunt: (cells[iT] || '').trim(),
      ref: iR >= 0 ? (cells[iR] || '').trim() : '',
      totaal: euBedrag(cells[iTot]),
      omschrijving: iO >= 0 ? (cells[iO] || '').trim() : ''
    }
  }).filter(r => r.tappunt && r.totaal > 0)
}

/* Bulk-import — de ENE poort voor CSV én straks de B2B-API. Match op
   snelstartcode (voorkeur) of winkelnaam; dedupe op ordernr. Puur: geeft de
   telling + de gewijzigde tappunt-kopieën terug (de view slaat ze op). */
export function importBestellingen(items, rows, bron) {
  let ok = 0, dup = 0
  const miss = []
  const gewijzigd = new Map()   // snelstart -> bijgewerkte kopie
  rows.forEach(r => {
    const q = String(r.tappunt || '').trim().toLowerCase()
    if (!q) return
    const basis = items.find(x => String(x.snelstart || '').toLowerCase() === q)
      || items.find(x => String(x.name || '').toLowerCase() === q)
    if (!basis) { if (!miss.includes(r.tappunt)) miss.push(r.tappunt); return }
    const t = gewijzigd.get(basis.snelstart) || basis
    const t2 = voegBestellingToe(t, { ...r, bron: bron || 'csv' })
    if (!t2) { dup++; return }
    gewijzigd.set(basis.snelstart, t2)
    ok++
  })
  return { ok, dup, miss, updates: [...gewijzigd.values()] }
}
