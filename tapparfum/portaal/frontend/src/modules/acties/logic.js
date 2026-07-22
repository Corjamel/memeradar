// Actie-deelname & resultaat — EXACT v71 (r.1552-1581, 3763).
// Datamodel op het tappunt:
//   t.actieDeelname = { aid: { done, at, by, res:{werkte,tekst,at,by}, punten } }
//   t.actiesGezienP = [aid, ...]   (gezien = melding weg)
// Puur: functies geven een bijgewerkte kopie terug; de views slaan op.
import { inTraject } from '../beloningen/logic.js'
import { logToevoegen } from '../logboek/logic.js'

const vandaagISO = () => new Date().toISOString().slice(0, 10)

export const doetMee = (t, aid) => !!(t.actieDeelname && t.actieDeelname[aid] && t.actieDeelname[aid].done)
export const heeftRes = (t, aid) => !!(t.actieDeelname && t.actieDeelname[aid] && t.actieDeelname[aid].res)

export function zetDeelname(t, aid, aan, by) {
  const d = { ...(t.actieDeelname || {}) }
  if (aan) d[aid] = { done: true, at: vandaagISO(), by: by || 'am' }
  else delete d[aid]
  return { ...t, actieDeelname: d }
}

/* Resultaat registreren = dé feedbackronde: werkte het (ja/deels/nee) + korte
   toelichting. Punten worden automatisch toegekend (alleen traject-winkels,
   alleen als de actie punten heeft) en tellen mee in de beloningen.
   Alleen mogelijk als er deelname was en er nog geen resultaat staat. */
export function actieResSave(t, actie, werkte, tekst, by) {
  if (!['ja', 'deels', 'nee'].includes(werkte)) return null
  const d = t.actieDeelname && t.actieDeelname[actie.id]
  if (!d || !d.done || d.res) return null
  const res = { werkte, tekst: String(tekst || '').trim(), at: vandaagISO(), by: by || 'am' }
  let punten = 0
  if (actie && +actie.punten > 0 && inTraject(t)) punten = +actie.punten
  const deelname = { ...t.actieDeelname, [actie.id]: { ...d, res, ...(punten ? { punten } : {}) } }
  let t2 = { ...t, actieDeelname: deelname }
  const woord = werkte === 'ja' ? 'werkte goed' : (werkte === 'deels' ? 'werkte deels' : 'werkte niet')
  const log = logToevoegen(t2, {
    type: 'notitie',
    txt: '📊 Actie afgerond: ' + (actie.titel || '') + ' — ' + woord +
      (res.tekst ? ' · ' + res.tekst : '') + (punten ? ' · +' + punten + ' punten toegekend' : '')
  })
  if (log) t2 = log.t2
  return { t2, punten }
}

/* Resultaat-overzicht over een lijst winkels (kantoor/AM-analyse, v71 r.1577). */
export function actieResStats(items, aid) {
  const st = { afgerond: 0, ja: 0, deels: 0, nee: 0, punten: 0, fb: [] }
  items.forEach(t => {
    const d = t.actieDeelname && t.actieDeelname[aid]
    if (d && d.res) {
      st.afgerond++
      st[d.res.werkte] = (st[d.res.werkte] || 0) + 1
      st.punten += (+d.punten || 0)
      st.fb.push({ tn: t.name, werkte: d.res.werkte, tekst: d.res.tekst || '', at: d.res.at, by: d.res.by })
    }
  })
  return st
}

/* Video-embed (v71 r.1554): YouTube/Vimeo als privacyvriendelijke embed-URL,
   al het andere alleen als veilige losse link. */
export function videoEmbedUrl(u) {
  u = String(u || '').trim()
  if (!u) return null
  let m = u.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/|embed\/)|youtu\.be\/)([\w-]{6,})/)
  if (m) return { embed: 'https://www.youtube-nocookie.com/embed/' + m[1] }
  m = u.match(/vimeo\.com\/(\d+)/)
  if (m) return { embed: 'https://player.vimeo.com/video/' + m[1] }
  return /^https?:\/\//i.test(u) ? { link: u } : null
}
