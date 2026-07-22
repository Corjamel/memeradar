// Puntensysteem — EXACT de v71-definities (r.641-668, 2653-2827).
// Data op het tappunt: t.bp / t.bpClaim / t.bonus / t.bonusClaim = { key: bool }.

export const BASIS = [
  ['geuren', 'Min. 80 verschillende tap-geuren in de kast (dames LA · heren LE · unisex/niche TN-TF)', 6],
  ['prijzen', 'Adviesprijzen aanhouden + verkopen op geurnoten (min. 2 noten benoemen)', 5],
  ['link', 'www.tapparfum.nl gelinkt in je social-bio of op je website', 1],
  ['amcontact', 'Vaste accountmanager-afspraak per kwartaal', 1],
  ['kwaliteit', 'Testers + tapflessen elke 3 mnd vervangen/controleren op oxidatie', 5],
  ['geurnotenboek', 'Geurnotenboek + tablet zichtbaar en in gebruik', 5],
  ['home', 'Home collectie aanwezig: geurkaars, homespray én reed diffuser', 5],
  ['exclusief', 'Exclusieve lijn: minimaal 10 geuren', 5],
  ['bodymist', 'Bodymist in het assortiment', 3],
  ['zichtbaar', 'TapParfum zichtbaar binnen (display) én buiten (raam/stoep)', 5],
  ['presentatie', 'Strakke presentatie: flessen op rij, schenktuiten gelijk, transparante stickers, teststrips, koffiebonen, ledlicht', 10],
  ['hoek', 'Eigen parfumhoek/-bar met toonbank en zitplek', 5],
  ['hashtags', 'Vaste hashtags onder elke TapParfum-post (#tapparfum #hervulbaar)', 3],
  ['promopakket', 'Promotiepakketten volledig als actie inzetten (niet in vast assortiment)', 3],
  ['certificaat', 'Personeel getraind + TapParfum-certificaat behaald', 5],
  ['voorraad', 'Altijd voorraad: lege flesjes, vials en verse testers', 3]
]
export const BASIS_MAX = BASIS.reduce((a, x) => a + x[2], 0)          // 70
export const OFFICIEEL = 60

export const BONUS_MANUAL = [
  ['geuravond', 'Min. 2 geuravonden/vriendinnen-avonden dit jaar gehouden (+ getagd)', 5],
  ['weekpost', 'Elke week een TapParfum-post op social (volgens richtlijnen, + @tag)', 5],
  ['eigenacties', '2 eigen acties bedacht én uitgevoerd (naast TapParfum-acties)', 5],
  ['gnbdagelijks', 'Geurnotenboek dagelijks gebruikt bij de verkoop', 2],
  ['dagtarget', 'Dag-target uit het dashboard gehaald', 5],
  ['wederverkoper', 'Nieuwe wederverkoper aangebracht (afgeronde sale)', 5],
  ['nieuwmodule', 'Nieuw product/module toegevoegd (Niventi · Candle · Home)', 5],
  ['excluit', 'Exclusieve lijn uitgebreid', 3]
]
export const BONUS_MAX = BONUS_MANUAL.reduce((a, x) => a + x[2], 0)   // 35

export const basisScore = (t) => BASIS.reduce((a, [k, , p]) => a + ((t.bp || {})[k] ? p : 0), 0)
export const bonusHandmatig = (t) => BONUS_MANUAL.reduce((a, [k, , p]) => a + ((t.bonus || {})[k] ? p : 0), 0)
export const officieel = (t) => basisScore(t) >= OFFICIEEL

// ---- automatische bonus (v71 r.2639-2664, 2819-2825) ----------------------
export function monthsElapsed(t) {
  const now = new Date()
  if (t.liveDate && String(t.liveDate).slice(0, 4) === String(now.getFullYear())) {
    const startM = +String(t.liveDate).slice(5, 7) - 1
    return Math.max(now.getMonth() - startM + 1, 1)
  }
  return now.getMonth() + 1
}

export function omzetGroei(t) {
  const m = monthsElapsed(t)
  const vj = +t.vorigJaar || 0
  if (m < 2 || vj <= 0) return null
  const nu = (+t.jaaromzet || 0) / m
  const ref = vj / 12
  return (nu - ref) / ref
}

export function omzetGroeiPunten(t) {
  const g = omzetGroei(t)
  if (g == null) return 0
  if (g >= 1.5) return 10
  if (g >= 1.0) return 8
  if (g >= 0.75) return 6
  if (g >= 0.5) return 4
  if (g >= 0.25) return 2
  return 0
}

export const effDoel = (t) => (t.goal && +t.goal.doel) || +t.doel || 0
export const jaardoelPunten = (t) => (effDoel(t) > 0 && (+t.jaaromzet || 0) >= effDoel(t)) ? 5 : 0

// Break-even op tijd: ≤75% van de geplande dagen -> 8, ≤100% -> 5, anders 0.
export function beOnTimePunten(t) {
  if (!t.be || !t.beDoneAt || !t.liveDate) return 0
  const dagen = Math.round((new Date(t.beDoneAt) - new Date(t.liveDate)) / 864e5)
  if (dagen <= t.be.days * 0.75) return 8
  if (dagen <= t.be.days) return 5
  return 0
}

export const bonusAuto = (t) => omzetGroeiPunten(t) + jaardoelPunten(t) + beOnTimePunten(t)
export const actiePunten = (t) => Object.values(t.actieDeelname || {}).reduce((a, d) => a + (+d.punten || 0), 0)
export const totaalScore = (t) => basisScore(t) + bonusHandmatig(t) + bonusAuto(t) + actiePunten(t)
