// AM-score — EXACT het v71-model (r.2058-2096): vijf componenten, elk
// genormaliseerd naar 0-100 en daarna gewogen (weging telt samen 100). De oude
// portal-score vermenigvuldigde een KALE groeiratio met het gewicht (groei
// domineerde) en had een hardcoded data-component — dat is hiermee hersteld.
import { monthsElapsed } from '../punten/logic.js'
import { laatsteBestelling } from '../bestellingen/logic.js'

// Datakwaliteit: dezelfde velden als v71 GEG_VELDEN (r.3976).
export const GEG_VELDEN = ['contact', 'email', 'tel', 'adres', 'postcode', 'plaats', 'land', 'snelstart', 'type', 'display', 'bezoekmoment', 'web', 'jarig']
const gegIngevuld = (t) => GEG_VELDEN.filter(k => String(t[k] || '').trim()).length

// v71 WEGING_STD + de vijf onderdelen die kantoor in de Regels-tab kan wegen.
export const WEGING_STANDAARD = { groei: 35, act: 25, uitv: 20, stil: 10, data: 10 }
export const WEGING_LABELS = [
  ['groei', 'Groei'], ['act', 'Activaties'], ['uitv', 'Actie-uitvoering'],
  ['stil', 'Bestelstiltes (60d)'], ['data', 'Datakwaliteit']
]

const dagenGeleden = (d) => d ? (Date.now() - new Date(d)) / 864e5 : Infinity

// v71 echteActivatie (r.2058): binnen het activatievenster een afgeronde actie
// of een bestelling ná de trajectstart.
function echteActivatie(t, actDagen) {
  if (t.traject !== true || !t.trajectSinds) return false
  if (dagenGeleden(t.trajectSinds) > actDagen) return false
  const na = (d) => d && d >= t.trajectSinds
  const actieOk = Object.values(t.actieDeelname || {}).some(v => v && v.res && na(v.res.at))
  const bestelOk = (t.bestellingen || []).some(b => na(b.at))
  return actieOk || bestelOk
}

/* AM-score over een lijst winkels. opts: { weging, acties, actDagen }.
   Geeft { score, groeiPct, comp } — comp is de uitleg-strip per component. */
export function amScore(ts, { weging, acties = [], actDagen = 90 } = {}) {
  const w = { ...WEGING_STANDAARD, ...(weging || {}) }
  if (!ts.length) return { score: 0, groeiPct: null, comp: [] }
  // Groei: v71 aggregeert over de portefeuille (Σ maand-tempo vs Σ vorig jaar/12).
  let nu = 0, vj = 0
  ts.forEach(t => { nu += (+t.jaaromzet || 0) / Math.max(1, monthsElapsed(t)); vj += (+t.vorigJaar || 0) / 12 })
  const groeiPct = vj > 0 ? Math.round((nu - vj) / vj * 100) : null
  const act90 = ts.filter(t => t.traject === true && t.trajectSinds && dagenGeleden(t.trajectSinds) <= actDagen).length
  const actEcht = ts.filter(t => echteActivatie(t, actDagen)).length
  // Actie-uitvoering: deelname% + afgerond% over de niet-gearchiveerde acties.
  const open = (acties || []).filter(a => !a.archived)
  let deel = 0, res = 0, mog = 0
  open.forEach(a => ts.forEach(t => { mog++; const d = t.actieDeelname && t.actieDeelname[a.id]; if (d && d.done) { deel++; if (d.res) res++ } }))
  const deelPct = mog ? Math.round(deel / mog * 100) : 0
  const resPct = deel ? Math.round(res / deel * 100) : 0
  const stil = ts.filter(t => dagenGeleden(laatsteBestelling(t)) > 60).length
  const dataPct = Math.round(ts.reduce((a, t) => a + gegIngevuld(t), 0) / (ts.length * GEG_VELDEN.length) * 100)
  // Componenten -> 0-100 (v71 r.2090-2094).
  const sGroei = groeiPct == null ? 50 : Math.max(0, Math.min(100, 50 + groeiPct))
  const sAct = Math.min(100, actEcht * 25 + (act90 - actEcht) * 5)
  const sUit = Math.round((deelPct + resPct) / 2)
  const sStil = Math.max(0, 100 - Math.round(stil / ts.length * 100))
  const score = Math.round(sGroei * w.groei / 100 + sAct * w.act / 100 + sUit * w.uitv / 100 + sStil * w.stil / 100 + dataPct * w.data / 100)
  return {
    score, groeiPct,
    comp: [
      ['Groei', groeiPct == null ? '—' : (groeiPct >= 0 ? '+' : '') + groeiPct + '%'],
      ['Activaties', actEcht + ' echt / ' + act90],
      ['Uitvoering', deelPct + '% · ' + resPct + '% af'],
      ['Stiltes 60d+', stil],
      ['Data', dataPct + '%']
    ]
  }
}
