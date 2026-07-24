// Rekenhart — EXACT de v71-logica (r.2604-2679, 3201-3211): niveaus (ABCD),
// winkelomzet met bronhiërarchie, en de status per winkel. Puur (geen API):
// de marge-factor en flesmaten komen als argument binnen, zodat elke view met
// dezelfde netwerk-config rekent (haalRekenConfig in modules/beloningen/api.js).
import { omzetPF } from '../calculator/logic.js'
import { vkPeriode } from '../kassa/api.js'
import { setupComplete } from '../setup/logic.js'
import { omzetGroei } from '../punten/logic.js'

/* Niveaus = omzet-STATUS met de vertrouwde drempels. De beloningen zitten NIET
   op de tussenliggende niveaus maar op concept-gedrag + Academy (zie REWARDS in
   modules/beloningen/logic.js) — alleen de top (A+/A++) heeft een omzetbeloning. */
export const LEVELS = [
  { k: 'D', min: 0, r: 'Startpunt — alles nog te winnen' },
  { k: 'C', min: 3000, r: 'Groeiend tappunt' },
  { k: 'B', min: 10000, r: 'Bovengemiddeld — top 33% van alle tappunten' },
  { k: 'A', min: 20000, r: 'Top 17% — A-klant, vaste waarde' },
  { k: 'A+', min: 50000, r: 'Top 4% — regiotopper', bel: '5% korting op je bestellingen — 3 maanden lang' },
  { k: 'A++', min: 100000, r: 'Top 1% — landelijke top, ambassadeur van TapParfum', bel: '10% korting op je bestellingen — 3 maanden lang' }
]
// De standaard-drempels, zodat de regels-editor kan resetten.
export const NIVEAU_DREMPELS_STANDAARD = LEVELS.map(l => l.min)

/* Regels-editor (v71 Regels-tab): kantoor kan de ABCD-omzetdrempels bijstellen.
   We patchen de bestaande LEVELS-drempels in-place (D=0 blijft), zodat álle
   afnemers van levelOf/statusKey meteen met de nieuwe drempels rekenen. Wordt
   éénmalig toegepast bij het laden van central 'regels' (auth.init). */
export function setNiveauDrempels(mins) {
  if (!Array.isArray(mins)) return
  LEVELS.forEach((l, i) => {
    if (i === 0) { l.min = 0; return }
    const v = Number(mins[i])
    if (Number.isFinite(v) && v >= 0) l.min = v
  })
}

// Vaste typevolgorde uit v71 (r.3201) — t.flesLog[].ti verwijst hierin op index.
export const SALE_TYPES = []
;['std', 'excl'].forEach(tp => ['bottle', 'refill'].forEach(md => ['30', '50', '100'].forEach(sz =>
  SALE_TYPES.push({ tp, md, sz, label: `${sz} ml ${tp === 'std' ? 'standaard' : 'Exclusive'} ${md === 'bottle' ? '+ flesje' : 'refill'}` }))))

export const jaaromzet = (t) => +t.jaaromzet || 0   // uitsluitend inkoop bij TapParfum
export const flessenVanLog = (entries) => (entries || []).reduce((a, e) => a + (+e.n || 0), 0)
export const omzetVanLog = (entries) => (entries || []).reduce((a, e) => {
  const ty = SALE_TYPES[e.ti]
  return a + (ty ? omzetPF(ty.tp, ty.md, ty.sz) * (+e.n || 0) : 0)
}, 0)
export const flessenVerkocht = (t) => flessenVanLog(t.flesLog)      // all-time (break-even)
export const omzetVerkocht = (t) => omzetVanLog(t.flesLog)
export const omzetVerkochtJaar = (t) => {
  const y = String(new Date().getFullYear())
  return omzetVanLog((t.flesLog || []).filter(e => String(e.at || '').slice(0, 4) === y))
}

/* Geregistreerde bedragen = INKOOP; de ABCD-grenzen zijn gekalibreerd op
   winkelVERKOOP — de marge-factor overbrugt (geschatte winkelomzet = inkoop × factor). */
export const winkelOmzet = (t, marge) => Math.round(jaaromzet(t) * (marge > 0 ? marge : 1))
export const kassaJaar = (t, maten) => Math.round(vkPeriode(t, new Date().getFullYear() + '-01-01', maten).tot)
export const tellerJaar = (t) => Math.round(omzetVerkochtJaar(t))

/* Eén waarheid voor 'winkelomzet dit jaar': flessenteller (incl. kassa-brug) >
   losse kassa > schatting (inkoop × factor). Bronnen vervangen elkaar — nooit optellen. */
export function winkelOmzetInfo(t, marge, maten) {
  const f = tellerJaar(t)
  if (f > 0) {
    const heeftKassa = (t.flesLog || []).some(e => e && e.src === 'kassa')
    return { bedrag: f, bron: heeftKassa ? 'kassa' : 'teller' }
  }
  const k = kassaJaar(t, maten)
  if (k > 0) return { bedrag: k, bron: 'kassa' }
  return { bedrag: winkelOmzet(t, marge), bron: 'schatting' }
}

export function levelOf(jo, marge) {
  jo = jo * (marge > 0 ? marge : 1)
  let i = 0
  for (let j = 0; j < LEVELS.length; j++) { if (jo >= LEVELS[j].min) i = j }
  const cur = LEVELS[i], nx = LEVELS[i + 1] || null
  return {
    k: cur.k, idx: i, min: cur.min, r: cur.r, bel: cur.bel || null,
    next: nx ? nx.k : null, nextMin: nx ? nx.min : null, nextR: nx ? nx.r : null,
    gap: nx ? Math.max(nx.min - jo, 0) : 0
  }
}

/* Break-even is ALLEEN bereikt op basis van daadwerkelijk verkochte flessen
   of terugverdiende omzet — nooit door tijdsverloop. */
export function beReached(t) {
  if (!t.be) return false
  const sold = flessenVerkocht(t)
  if (t.be.bottles > 0 && sold >= t.be.bottles) return true
  const inv = t.be.inv || 0
  if (inv > 0 && omzetVerkocht(t) >= inv) return true
  return false
}
export const beDone = (t) => !!(t.beDone || beReached(t))

export const STATUS = {
  nieuw: { l: 'Nieuw', bg: '#D8D5CC', fg: '#3a3a36' },
  groeit: { l: 'Groeit', bg: '#C0DD97', fg: '#173404' },
  top: { l: 'Top', bg: '#EE644D', fg: '#fff' },
  stagneert: { l: 'Stagneert', bg: '#FAC775', fg: '#412402' }
}

/* v71-volgorde: statusManual → setup-incompleet = nieuw → break-even niet klaar
   (tenzij checklist overgeslagen) = nieuw → omzet 0 → groei < 0 = stagneert →
   niveau A+/A++ = top → groeit. */
export function statusKey(t, marge) {
  if (t.statusManual) return t.statusManual
  if (!setupComplete(t)) return 'nieuw'
  const overgeslagen = t.setup && t.setup.skipped
  if (!overgeslagen && t.be && !beDone(t)) return 'nieuw'
  const jo = jaaromzet(t)
  if (!jo) return ((+t.vorigJaar || 0) > 0 || (+t.omzet2024 || 0) > 0) ? 'stagneert' : 'groeit'
  const g = omzetGroei(t)
  if (g != null && g < 0) return 'stagneert'
  const lv = levelOf(jo, marge).k
  if (lv === 'A+' || lv === 'A++') return 'top'
  return 'groeit'
}

export const groeiTxt = (g) => g == null ? '—' : (g >= 0 ? '+' : '') + Math.round(g * 100) + '%'
