// Beloningen-engine — EXACT de v71-definities (r.3248-3299, 3371-3378):
// vijf spaarcadeaus (REWARDS) met harde eisen + verplichte Academy-training,
// en de eenmalige uitkering in t.beloond { rewardKey: 'YYYY-MM-DD' }.
// Drempels bewust niet makkelijk; bijstellen kan hier (besluit kantoor).
import { BASIS_MAX, basisScore, totaalScore, omzetGroei, effDoel } from '../punten/logic.js'
import { LEVELS, jaaromzet, winkelOmzet, levelOf, flessenVerkocht, groeiTxt } from '../rekenhart/logic.js'
import { eur0 } from '../../lib/format.js'

// ---- Academy-koppeling (cursusdata uit v71; de lesinhoud volgt bij PARITY #24) ----
export const COURSES = [
  ['onboarding', 'Onboarding', 'Welkom bij TapParfum', 'Missie, het refill-concept en waarom parfum niet duur hoeft.', ['Wat is TapParfum', 'Het refill-concept', 'Onze missie & visie', 'De productlijnen', 'Het Geurnotenboek', 'Jouw eerste week']],
  ['geurnoten', 'Verkoop', 'Geurnoten uitleggen aan klanten', 'Top-, hart- en basisnoten zo vertellen dat klanten kopen.', ['Top-, hart- en basisnoten', 'Geurfamilies', 'In één zin uitleggen', 'Veelgestelde klantvragen']],
  ['funnel', 'Verkoop', 'De TapParfum sales funnel', 'Geur → formaat → upsell → refill → afronden.', ['De 5 stappen', 'Geur kiezen via het Geurnotenboek', 'Upsell & refill uitleggen', 'De verkoop afronden', 'Oefencases']],
  ['aanspreken', 'Verkoop', 'Klanten aanspreken & pitchen', 'Eerste indruk, pitch van 20 sec, omgaan met bezwaren.', ['De eerste indruk', 'Je pitch van 20 seconden', 'Omgaan met bezwaren', 'Live oefenen', 'Afsluiten & motivatie']],
  ['geurnotenboek', 'Tool', 'Het Geurnotenboek & de quiz', 'Laat klanten op geurbeleving zoeken — de app toont de match.', ['De tablet & de quiz', 'Op geurbeleving zoeken', 'Meerdere matches verkopen']],
  ['tapbar', 'Beleving', 'De perfecte Tapbar-demo', 'Tap, ruik, ontdek — de winkelbeleving die blijft hangen.', ['De Tapbar opzetten', 'De demo geven', 'Beleving & sfeer', 'Hygiëne & onderhoud', 'Veelgemaakte fouten']]
]

export function academyDone(t, key) {
  if (key === 'alle') return COURSES.every(c => academyDone(t, c[0]))
  const c = COURSES.find(x => x[0] === key)
  if (!c) return false
  const d = (t.academy || {})[key] || {}
  return c[4].every((_, i) => d[i])
}

export function academyPct(t, key) {
  if (key === 'alle') {
    let d = 0, tot = 0
    COURSES.forEach(c => {
      const a = (t.academy || {})[c[0]] || {}
      tot += c[4].length
      d += c[4].filter((_, i) => a[i]).length
    })
    return tot ? Math.round(d / tot * 100) : 0
  }
  const c = COURSES.find(x => x[0] === key)
  if (!c) return 0
  const a = (t.academy || {})[key] || {}
  return Math.round(c[4].filter((_, i) => a[i]).length / c[4].length * 100)
}

export function cursusNaam(key) {
  if (key === 'alle') return 'volledige Academy (certificaat)'
  const c = COURSES.find(x => x[0] === key)
  return c ? c[2] : key
}

// ---- Eisen-bouwstenen: elke eis heeft ok(t), pct(t) 0-100 en rest(t) ----
export const EIS = {
  basis: min => ({
    txt: min + '/' + BASIS_MAX + ' basispunten',
    ok: t => basisScore(t) >= min,
    pct: t => Math.min(basisScore(t) / min * 100, 100),
    rest: t => 'nog ' + Math.max(min - basisScore(t), 0) + ' punten'
  }),
  totaal: min => ({
    txt: min + ' totaalpunten (basis + bonus)',
    ok: t => totaalScore(t) >= min,
    pct: t => Math.min(totaalScore(t) / min * 100, 100),
    rest: t => 'nog ' + Math.max(min - totaalScore(t), 0) + ' punten'
  }),
  /* Realistische groei: +50% telt alleen vanaf een serieuze basis (≥ €5.000 vorig
     jaar). Kleinere/nieuwe winkels hoeven geen groei-% te bewijzen: de omzetdrempel
     is dan het bewijs. */
  groei50: () => ({
    txt: 'Omzetgroei ≥ +50% (vanaf ≥ €5.000 basis vorig jaar)',
    ok: t => { const vj = +t.vorigJaar || 0; if (vj < 5000) return true; const g = omzetGroei(t); return g != null && g >= 0.50 },
    pct: t => { const vj = +t.vorigJaar || 0; if (vj < 5000) return 100; const g = omzetGroei(t); return g == null ? 0 : Math.max(0, Math.min(g / 0.50 * 100, 100)) },
    rest: t => { const g = omzetGroei(t); return g == null ? 'omzet vorig jaar invullen' : 'nu ' + groeiTxt(g) + ' — doel +50%' }
  }),
  omzetMin: min => ({
    txt: 'Minimaal ' + eur0(min) + ' omzet dit jaar',
    ok: t => jaaromzet(t) >= min,
    pct: t => Math.min(jaaromzet(t) / min * 100, 100),
    rest: t => 'nog ' + eur0(Math.max(min - jaaromzet(t), 0))
  })
}

export const REWARDS = [
  { key: 'vials', r: 'Gratis promopakket: 200 vials + 2 topgeuren', ic: '🧪', chip: '70 basispunten', sub: 'Álle basispunten binnen — de perfecte winkel.', eisen: [EIS.basis(BASIS_MAX)], cursus: 'onboarding' },
  { key: 'home', r: 'Gratis promopakket homegeuren', ic: '🏠', chip: '€5.000 + groei', sub: 'Je eerste grote mijlpaal — verkoop de beleving en laat de omzet het bewijzen.', eisen: [EIS.omzetMin(5000), EIS.groei50()], cursus: 'tapbar' },
  { key: 'kaarsen', r: 'Gratis promopakket kaarsen', ic: '🕯️', chip: '€10.000 + groei', sub: 'Bovengemiddeld draaien én blijven groeien.', eisen: [EIS.omzetMin(10000), EIS.groei50()], cursus: 'funnel' },
  { key: 'bodymist', r: 'Gratis promopakket bodymist', ic: '💨', chip: '€15.000 + groei', sub: 'Voor de winkels die het concept écht laten werken.', eisen: [EIS.omzetMin(15000), EIS.groei50()], cursus: 'aanspreken' },
  { key: 'promodag', r: 'Gratis promotiedag (t.w.v. €500)', ic: '📣', chip: '105 totaalpunten', sub: 'Voor de meest actieve tappunten.', eisen: [EIS.totaal(105)], cursus: 'alle' }
]

export const inTraject = (t) => !t || t.traject !== false

/* Vrijgespeeld = álle eisen gehaald ÉN de vereiste training afgerond.
   Voortgang = de zwakste schakel. */
export const rewUnlocked = (t, rw) => rw.eisen.every(e => e.ok(t)) && (!rw.cursus || academyDone(t, rw.cursus))
export function rewPct(t, rw) {
  let m = 100
  rw.eisen.forEach(e => { m = Math.min(m, e.pct(t)) })
  if (rw.cursus) m = Math.min(m, academyPct(t, rw.cursus))
  return Math.round(m)
}

/* Controleert of er beloningen zijn vrijgespeeld — punten-beloningen (REWARDS)
   én groeibeloningen (LEVELS met bel). Eén keer uitkeren per beloning; puur:
   geeft de bijgewerkte kopie + wat er nieuw is terug (of null als er niets is).
   Let op: v71 vergeleek de niveau-beloningen per abuis met de kale inkoop; hier
   rekenen we — net als de niveau-badge zelf — met de winkelomzet (inkoop × marge). */
export function checkBeloningen(t, marge) {
  if (!inTraject(t)) return null
  const today = new Date().toISOString().slice(0, 10)
  const beloond = { ...(t.beloond || {}) }
  const vieringen = [...(t.vieringen || [])]
  const nieuw = []
  const uitkeren = (key, r, bron) => {
    beloond[key] = today
    vieringen.push({ type: 'beloning', r, at: today })
    nieuw.push({ key, r, bron })
  }
  REWARDS.forEach(rw => {
    if (!beloond[rw.key] && rewUnlocked(t, rw)) uitkeren(rw.key, rw.r, rw.chip + (rw.cursus ? ' + training' : ''))
  })
  const wo = winkelOmzet(t, marge)
  LEVELS.forEach(L => {
    if (L.bel && wo >= L.min && !beloond['lvl-' + L.k]) uitkeren('lvl-' + L.k, L.bel, 'niveau ' + L.k + ' bereikt')
  })
  if (!nieuw.length) return null
  return { t2: { ...t, beloond, vieringen }, nieuw }
}

/* Mijlpaal-detectie op één plek (v71 r.3301-3309) — aanroepen vanuit elke
   mutatie die omzet of flessen raakt. Vergelijkt de situatie vóór (joVoor)
   met nu en viert niveau-, doel- en break-even-mijlpalen. Puur: geeft de
   bijgewerkte kopie + meldteksten terug; sluit af met de beloningen-check. */
export function checkMilestones(t, joVoor, marge) {
  const today = new Date().toISOString().slice(0, 10)
  const vieringen = [...(t.vieringen || [])]
  const meldingen = []
  let t2 = { ...t, vieringen }
  const mijlpaal = (v, txt) => { vieringen.push({ ...v, at: today }); meldingen.push(txt) }

  const joNa = jaaromzet(t2)
  const lvNa = levelOf(joNa, marge)
  if (lvNa.idx > levelOf(joVoor, marge).idx) {
    mijlpaal({ type: 'level', k: lvNa.k, r: lvNa.r },
      'Niveau ' + lvNa.k + ' bereikt (' + eur0(joNa) + ') — geef het tappunt een compliment')
  }
  const doel = effDoel(t2)
  if (doel > 0 && joVoor < doel && joNa >= doel) {
    mijlpaal({ type: 'doel', doel }, 'Jaardoel van ' + eur0(doel) + ' behaald — bespreek een nieuw doel')
  }
  if (t2.be && !t2.beDone && flessenVerkocht(t2) >= t2.be.bottles) {
    t2 = { ...t2, beDone: true, beDoneAt: today }
    mijlpaal({ type: 'be' }, 'Investering terugverdiend — break-even gehaald! Plan het jaardoel-gesprek.')
  }
  const bel = checkBeloningen(t2, marge)
  if (bel) { t2 = bel.t2; bel.nieuw.forEach(n => meldingen.push('Beloning vrijgespeeld (' + n.bron + '): ' + n.r + ' — regel de uitkering.')) }
  if (!meldingen.length) return null
  return { t2, meldingen }
}
