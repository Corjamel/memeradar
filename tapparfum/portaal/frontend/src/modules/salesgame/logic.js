// Sales Game — de jaarwedstrijd (v71 r.1587-1623). GROEI wint, niet grootte;
// nieuwkomers zonder vergelijkingsjaar strijden in een eigen klassement;
// kwalificatie-eisen zijn een wortel ("nog X punten!"), nooit een muur.
// Alleen traject-deelnemers doen mee. Puur: functies krijgen de zichtbare
// winkels binnen (RLS-gescoped), dus de uitsnede klopt per rol.
import { omzetGroei, totaalScore } from '../punten/logic.js'
import { jaaromzet } from '../rekenhart/logic.js'
import { inTraject } from '../beloningen/logic.js'

export function gameScoreVan(t) {
  const g = omzetGroei(t)
  const groeiPct = g == null ? null : Math.round(g * 100)
  const acties = Object.values(t.actieDeelname || {}).filter(v => v && v.res).length
  const bonus = Math.min(20, Math.round(totaalScore(t) * 0.2))
  return { groeiPct, acties, bonus, score: (groeiPct == null ? 0 : groeiPct) + acties * 5 + bonus }
}

/* Klassement over de zichtbare winkels: groei-klassement, nieuwkomers en
   niet-gekwalificeerd (te weinig punten of te kleine basis). */
export function gameKlassement(sg, items) {
  if (!sg || !sg.actief) return null
  const minB = +sg.minBasis || 0, minP = +sg.minPunten || 0
  const groei = [], nieuw = [], nietQ = []
  items.forEach(t => {
    if (!inTraject(t)) return
    const sc = gameScoreVan(t)
    const pts = totaalScore(t)
    if (pts < minP) { nietQ.push({ t, reden: 'punten', tekort: minP - pts, sc }); return }
    if (sc.groeiPct == null) { nieuw.push({ t, jo: jaaromzet(t), sc }); return }
    if ((+t.vorigJaar || 0) < minB) { nietQ.push({ t, reden: 'basis', sc }); return }
    groei.push({ t, sc })
  })
  groei.sort((a, b) => b.sc.score - a.sc.score)
  nieuw.sort((a, b) => b.jo - a.jo)
  return { sg, groei, nieuw, nietQ }
}

export function gamePositie(k, snelstart) {
  if (!k) return null
  let i = k.groei.findIndex(x => x.t.snelstart === snelstart)
  if (i >= 0) return { kl: 'groei', pos: i + 1, van: k.groei.length, sc: k.groei[i].sc }
  i = k.nieuw.findIndex(x => x.t.snelstart === snelstart)
  if (i >= 0) return { kl: 'nieuw', pos: i + 1, van: k.nieuw.length, sc: k.nieuw[i].sc }
  const nq = k.nietQ.find(x => x.t.snelstart === snelstart)
  if (nq) return { kl: 'nietq', reden: nq.reden, tekort: nq.tekort || 0, sc: nq.sc }
  return null
}

export function gameDagen(sg) {
  if (!sg || !sg.eind) return null
  const d = Math.ceil((new Date(sg.eind) - new Date()) / 864e5)
  return d >= 0 ? d : 0
}
