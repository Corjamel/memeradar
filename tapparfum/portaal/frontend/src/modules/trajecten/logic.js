// Heractiveren & trajecten — EXACT v71 (r.2979-3016). Datamodel:
// t.react = [{date, actie, opvolg, done}] (nieuwste eerst), t.traject (false =
// klant zonder begeleiding), t.trajectSinds, t.trajectDoor.
// De vier trajecten volgen de statusKey — de labels leven in STATUS (rekenhart).
import { dagenTot } from '../logboek/logic.js'

export const REACT_ACTIES = [
  'Gebeld / langsgegaan — situatie besproken',
  'Voorraad & presentatie samen gecheckt',
  'Geuravond / proefactie ingepland',
  'Bestseller-tips gegeven & schap opnieuw ingericht',
  'Social-post of lokale actie afgesproken',
  'Bijbestelling / aanvulling geregeld',
  'Doel & dag-target opnieuw afgesproken'
]

export const TRAJ = [
  { k: 'nieuw', foc: 'Inwerktraject — eerst terugverdienen', desc: 'Net gestart. De partner doorloopt de opstart en verdient daarna de investering terug. Nog geen omzetdoelen — jij begeleidt.', col: '#8a8578', acties: null },
  { k: 'groeit', foc: 'Groeien naar doel en volgend niveau', desc: 'Draait zelfstandig en groeit. Stuur op het jaardoel met positieve acties: geuravond, spaaractie, social media, assortiment uitbreiden.', col: 'var(--green)', acties: ['Geuravond / vriendinnenavond plannen', 'Spaaractie 6 refills + 7e gratis starten', 'Social-post of lokale actie afgesproken', 'Bijbestelling / assortiment uitbreiden', 'Doel & dag-target opnieuw afgesproken'] },
  { k: 'stagneert', foc: 'Heractiveren — uitzoeken wat misging', desc: 'Omzet daalt — hier ligt je prioriteit. Bel eerst, check voorraad & presentatie, zet dan een actie in en plan de opvolging.', col: 'var(--amber)', acties: REACT_ACTIES },
  { k: 'top', foc: 'Belonen & opschalen', desc: 'Je sterkste groeiers. Bedank en beloon ze, en verkoop uitbreiding: meer geuren, de Exclusive-lijn of extra modules.', col: 'var(--coral-d)', acties: ['Bedankt + succesverhaal gedeeld', 'Upsell: meer geuren / Exclusive', 'Upgrade naar groter pakket besproken', 'Ambassadeur / review gevraagd', 'Extra promodag ingepland'] }
]

const vandaagISO = () => new Date().toISOString().slice(0, 10)

// Actie vastleggen (v71 addReact) — puur.
export function reactToevoegen(t, actie, opvolg) {
  if (!actie) return null
  return { ...t, react: [{ date: vandaagISO(), actie, opvolg: opvolg || '', done: false }, ...(t.react || [])] }
}

export function reactDone(t, idx, v) {
  const react = (t.react || []).map((r, i) => i === idx ? { ...r, done: !!v } : r)
  return { ...t, react }
}

/* Open heractivatie-opvolgingen over alle zichtbare winkels (v71 reactOpen) —
   stroomt de agenda/Vandaag-lijst in. */
export function reactOpenLijst(items) {
  const uit = []
  items.forEach(t => (t.react || []).forEach((r, idx) => {
    if (r.done || !r.opvolg) return
    const due = new Date(r.opvolg)
    if (isNaN(due)) return
    uit.push({ t, r, idx, diff: dagenTot(due), goalW: (t.goal && t.goal.doel > 0) ? t.goal.flWeek : null })
  }))
  return uit.sort((a, b) => a.diff - b.diff)
}
