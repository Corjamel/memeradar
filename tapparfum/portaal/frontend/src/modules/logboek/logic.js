// Logboek, bezoeken, afspraken & opvolgcadans — EXACT v71 (r.638, 1228-1272,
// 2669-2672, 2720-2722). Alles puur: functies krijgen een tappunt-kopie en
// geven een bijgewerkte kopie terug; de views slaan op via de store.
import { BASIS, BONUS_MANUAL } from '../punten/logic.js'
import { beDone } from '../rekenhart/logic.js'

// Kleuren 1-op-1 uit v71 (LOG_TYPES r.1232) zodat de badges gelijk ogen.
export const LOG_TYPES = {
  bezoek: { l: 'Bezoek', ic: '📍', bg: 'var(--mist)', fg: '#21343f' },
  telefoon: { l: 'Telefoon', ic: '📞', bg: '#C0DD97', fg: '#173404' },
  mail: { l: 'Mail', ic: '✉️', bg: '#dcd9e8', fg: '#3a2f5a' },
  notitie: { l: 'Notitie', ic: '📝', bg: 'var(--sand)', fg: 'var(--ink)' }
}

// Duur van een bezoek leesbaar maken (v71 fmtDuur r.1511).
export function fmtDuur(min) {
  if (min == null) return ''
  min = Math.max(0, Math.round(min))
  return min < 60 ? min + ' min' : Math.floor(min / 60) + ' u ' + String(min % 60).padStart(2, '0')
}

// v71-cadans: vaste opvolgmomenten vanaf de live-datum.
export const FU = [
  ['d7', 'Dag 7 · Belcheck', 7],
  ['d30', 'Dag 30 · Omzetreview', 30],
  ['d60', 'Dag 60 · Bijsturen', 60],
  ['d90', 'Dag 90 · Kwartaal + upsell', 90]
]

export const BEZOEK_RITME_DAGEN = 90     // v71-drempel: 90 dagen zonder bezoek

const vandaagISO = () => new Date().toISOString().slice(0, 10)
const uid = () => 'l' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7)

export function dagenTot(d) {
  const t0 = new Date(); t0.setHours(0, 0, 0, 0)
  return Math.round((new Date(d) - t0) / 86400000)
}

/* Logregel toevoegen. Bij type 'bezoek' gaat t.laatsteBezoek alleen vooruit en
   wordt een gepland bezoek op/vóór die datum afgeboekt (v71 r.1233-1239). */
export function logToevoegen(t, entry) {
  const txt = (entry.txt || '').trim()
  if (!txt) return null
  const e = {
    id: uid(), at: entry.at || vandaagISO(),
    type: LOG_TYPES[entry.type] ? entry.type : 'notitie',
    txt, nextDate: entry.nextDate || '', nextDone: false
  }
  // v71-compatibele extra's: mailrichting bij mail, bezoekduur bij bezoek.
  if (e.type === 'mail' && (entry.dir === 'in' || entry.dir === 'uit')) e.dir = entry.dir
  if (e.type === 'bezoek' && entry.duurMin !== '' && entry.duurMin != null) e.duurMin = Math.max(0, parseInt(entry.duurMin) || 0)
  // Stabiel sorteren op datum (nieuwste eerst): 0 teruggeven bij gelijke datum
  // houdt de zojuist toegevoegde regel bovenaan i.p.v. willekeurig te herschikken.
  const logboek = [e, ...(t.logboek || [])].sort((a, b) => (a.at < b.at ? 1 : (a.at > b.at ? -1 : 0)))
  const t2 = { ...t, logboek }
  if (e.type === 'bezoek') {
    if (!t2.laatsteBezoek || e.at > t2.laatsteBezoek) t2.laatsteBezoek = e.at
    if (t2.bezoekGepland && t2.bezoekGepland <= e.at) t2.bezoekGepland = ''
  }
  return { t2, e }
}

export function logNextDone(t, eid, v) {
  return { ...t, logboek: (t.logboek || []).map(e => e.id === eid ? { ...e, nextDone: !!v } : e) }
}

export function logVerwijder(t, eid) {
  return { ...t, logboek: (t.logboek || []).filter(e => e.id !== eid) }
}

/* Dagen sinds laatste bezoek (logboek of los laatsteBezoek-veld); null = nooit. */
export function dagenSindsBezoek(t) {
  let d = t.laatsteBezoek || null
  ;(t.logboek || []).forEach(e => { if (e.type === 'bezoek' && (!d || e.at > d)) d = e.at })
  return d ? -dagenTot(d) : null
}

export function bezoekStil(t) {
  const d = dagenSindsBezoek(t)
  return d == null || d > BEZOEK_RITME_DAGEN
}

/* Open opvolgingen uit het logboek, over alle zichtbare winkels. */
export function logOpenNext(items) {
  const uit = []
  items.forEach(t => (t.logboek || []).forEach(e => {
    if (e.nextDate && !e.nextDone) {
      const due = new Date(e.nextDate)
      if (!isNaN(due)) uit.push({ t, e, diff: dagenTot(due) })
    }
  }))
  return uit.sort((a, b) => a.diff - b.diff)
}

// ---- Afspraken (gemaakt bij een bezoek; partner ziet en vinkt ze ook) ----
export const afsprakenOpen = (t) => (t.afspraken || []).filter(a => !a.done)

export function afspraakToevoegen(t, blok) {
  const regels = String(blok || '').split(/\r?\n/).map(x => x.trim()).filter(Boolean)
  if (!regels.length) return null
  const today = vandaagISO()
  const nieuw = regels.map(txt => ({ id: uid(), at: today, txt, done: false }))
  return { ...t, afspraken: [...nieuw, ...(t.afspraken || [])] }
}

/* Afvinken; als de partner het doet komt er een notitie in het logboek (v71 r.1256-1257). */
export function afspraakDone(t, aid, v, by) {
  const a = (t.afspraken || []).find(x => x.id === aid)
  if (!a) return t
  let t2 = {
    ...t,
    afspraken: t.afspraken.map(x => x.id === aid
      ? { ...x, done: !!v, doneAt: v ? vandaagISO() : '', doneBy: v ? (by || 'am') : '' } : x)
  }
  if (v && by === 'partner') {
    const res = logToevoegen(t2, { type: 'notitie', txt: '✓ Afspraak afgerond door partner: ' + a.txt })
    if (res) t2 = res.t2
  }
  return t2
}

// ---- Bezoek plannen / registreren (v71 r.2670-2672) ----
export const planBezoek = (t, datum) => ({ ...t, bezoekGepland: datum || '' })
export const registreerBezoek = (t, txt) =>
  logToevoegen(t, { type: 'bezoek', txt: txt || 'Bezoek geregistreerd' })

// ---- Punten-controle bij bezoek (v71 r.2667-2669) ----
// Claims op afstand controleerbaar: link, hashtags, weekpost — de rest vergt een bezoek.
export const REMOTE_OK = ['link', 'hashtags', 'weekpost']
export const visitGated = (key) => !REMOTE_OK.includes(key)

export function visitOpenClaims(t) {
  const bp = t.bp || {}, bpClaim = t.bpClaim || {}, bonus = t.bonus || {}, bonusClaim = t.bonusClaim || {}
  let n = 0
  BASIS.forEach(x => { if (bpClaim[x[0]] && !bp[x[0]] && visitGated(x[0])) n++ })
  BONUS_MANUAL.forEach(x => { if (bonusClaim[x[0]] && !bonus[x[0]] && visitGated(x[0])) n++ })
  return n
}

// ---- Opvolgcadans vanaf de live-datum (v71 r.2721) ----
// Loopt dóór na break-even — alleen de flessen-targets vervallen dan.
export function followups(items) {
  const uit = []
  items.forEach(t => {
    if (!t.liveDate) return
    const basis = new Date(t.liveDate)
    if (isNaN(basis)) return
    const bd = beDone(t)
    FU.forEach(([k, lab, off]) => {
      const due = new Date(basis)
      due.setDate(due.getDate() + off)
      const diff = dagenTot(due)
      let tgt = ''
      if (!bd && t.be && t.be.days > 0) {
        if (off >= t.be.days) tgt = 'break-even zou nu bereikt moeten zijn'
        else if (off === 7) tgt = `target week 1 ≈ ${t.be.perWk} flessen`
        else tgt = `op schema ≈ ${Math.round(t.be.bottles * off / t.be.days)}/${t.be.bottles} flessen`
      }
      uit.push({ t, k, lab, diff, tgt, done: !!(t.fu && t.fu[k]) })
    })
  })
  return uit
}

export function markFU(t, k, v) {
  const fu = { ...(t.fu || {}) }
  if (v) fu[k] = vandaagISO(); else delete fu[k]
  return { ...t, fu }
}
