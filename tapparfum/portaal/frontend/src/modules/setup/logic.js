// Opstartchecklist — EXACT de v71-definitie (r.627-636).
// Datamodel op het tappunt: t.setup = { done: { '0-0': true, ... }, skipped: bool }
// (sleutel = faseIndex-actieIndex, identiek aan v71's SETUPFORM-notatie).

export const SETUP = [
  { nr: '1', titel: 'Order & voorbereiden', acties: ['Order binnen & bevestigd', 'Trainingsmoment gepland (wie is aanwezig)', 'Start-stappenplan & A4-missie gedeeld', 'Voorwaarden besproken & akkoord (tappunt / tapbar / winkel)'] },
  { nr: '2', titel: 'Levering & installatie', acties: ['Labelprinter geïnstalleerd', 'Tapflessen gevuld & op nummer gepresenteerd', 'Testers met juiste dopkleur (LA zilver / LE zwart / T goud) & stickers', 'Tablet bijgewerkt en klaar'] },
  { nr: '3', titel: 'Demodag plannen', acties: ['Demodag = trainingsdag gepland', 'Poster + social media ingezet', 'Promodag-voorwaarden gecontroleerd'] },
  { nr: '4', titel: 'Demodag & training', acties: ['Team leert verkopen volgens de lifestyle', "USP's & verkoopbenaderingen getoond", 'Open vragen gesteld + tips gegeven'] },
  { nr: '5', titel: 'Evalueren', acties: ['Demo-evaluatieformulier ingevuld', 'Resultaten & klantrespons genoteerd'] },
  { nr: '6', titel: 'Actieplan & live', acties: ['Omzet-actieplan & jaardoel besproken', 'Eerste jaaromzet ingevuld', 'Tappunt verkoopt zelfstandig — live'] }
]
export const SETUP_TOTAL = SETUP.reduce((a, s) => a + s.acties.length, 0)   // 19 (4+4+3+3+2+3, identiek aan v71's reduce)

export function setupDone(t, si, ai) {
  return !!(t.setup && t.setup.done && t.setup.done[`${si}-${ai}`])
}

export function setupCount(t) {
  let n = 0
  SETUP.forEach((s, si) => s.acties.forEach((_, ai) => { if (setupDone(t, si, ai)) n++ }))
  return n
}

export function setupComplete(t) {
  return !!(t.setup && t.setup.skipped) || setupCount(t) === SETUP_TOTAL
}

// v71-gating: fase 4 en 5 (index 3 en 4) gaan pas open als de demodag gepland
// is (fase 3, actie 1 = sleutel '2-0'). Fase 1-3 en 6 zijn altijd open.
export function faseOpen(t, si) {
  if (si <= 2 || si === 5) return true
  return setupDone(t, 2, 0)
}
