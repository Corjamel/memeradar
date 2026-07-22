// Verkoop-schema & week-invulhulpen — EXACT v71 (r.3224-3247, 3310-3319).
// Puur: functies geven een bijgewerkte tappunt-kopie of een berekend object
// terug; de component slaat op en draait checkMilestones.
import { flessenVanLog, flessenVerkocht, omzetVerkochtJaar, jaaromzet, beDone } from '../rekenhart/logic.js'

export function daysSinceLive(t) {
  if (!t.liveDate) return null
  const d = new Date(t.liveDate)
  if (isNaN(d)) return null
  d.setHours(0, 0, 0, 0)
  const td = new Date(); td.setHours(0, 0, 0, 0)
  return Math.floor((td - d) / 86400000)
}

// Flessen dit jaar: uit het log geteld, en anders BEREKEND uit de omzet
// (omzet ÷ omzet-per-fles) zodat schema-meten ook werkt zonder los log.
export function flessenDitJaar(t) {
  const y = String(new Date().getFullYear())
  const geteld = flessenVanLog((t.flesLog || []).filter(e => String(e.at || '').slice(0, 4) === y))
  if (geteld > 0) return { n: geteld, bron: 'log' }
  const rev = (t.goal && t.goal.doel > 0 && t.goal.flJaar > 0) ? (t.goal.doel / t.goal.flJaar) : ((t.be && t.be.rev) || 16.53)
  return { n: Math.round(jaaromzet(t) / rev), bron: 'omzet', rev }
}

/* Op schema? Verwacht aantal flessen t/m vandaag vs. werkelijk — in de
   break-even-fase op het terugverdienplan, daarna op het jaardoel-tempo. */
export function schemaStatus(t) {
  if (t.be && !beDone(t) && t.be.days > 0) {
    const ds = daysSinceLive(t)
    if (ds == null) return null
    const verwacht = Math.min(Math.round(t.be.bottles * ds / t.be.days), t.be.bottles)
    const w = flessenVerkocht(t)
    return { fase: 'break-even', verwacht, werkelijk: w, delta: w - verwacht, doel: t.be.bottles, bron: 'log' }
  }
  if (t.goal && t.goal.flJaar > 0) {
    const now = new Date()
    const start = new Date(now.getFullYear(), 0, 1)
    const eind = new Date(now.getFullYear(), 11, 31)
    const frac = Math.min((now - start) / (eind - start), 1)
    const verwacht = Math.round(t.goal.flJaar * frac)
    const fd = flessenDitJaar(t)
    return { fase: 'jaardoel', verwacht, werkelijk: fd.n, delta: fd.n - verwacht, doel: t.goal.flJaar, bron: fd.bron }
  }
  return null
}

// Flessen die op één datum in het log staan.
export const dagTotaal = (t, d) => flessenVanLog((t.flesLog || []).filter(e => e.at === d))

/* Dagverkoop per dag zetten (eerste-week-ritme): verhogen voegt regels toe met
   het standaard-dagtype; verlagen haalt de laatst gelogde regels van die dag
   weg. Puur — geeft de bijgewerkte kopie terug (v71 setDagVerkoop). */
export function zetDagVerkoop(t, d, n) {
  n = Math.max(parseInt(n) || 0, 0)
  const flesLog = [...(t.flesLog || [])]
  const cur = flessenVanLog(flesLog.filter(e => e.at === d))
  if (n > cur) {
    const ti = (t.dagType != null ? t.dagType : 1)
    flesLog.push({ at: d, n: n - cur, ti })
  } else if (n < cur) {
    let over = cur - n
    for (let i = flesLog.length - 1; i >= 0 && over > 0; i--) {
      const e = flesLog[i]
      if (e.at !== d) continue
      const m = Math.min(+e.n || 0, over)
      flesLog[i] = { ...e, n: (+e.n || 0) - m }
      over -= m
      if (flesLog[i].n <= 0) flesLog.splice(i, 1)
    }
  }
  flesLog.sort((a, b) => (a.at < b.at ? -1 : 1))
  return { ...t, flesLog }
}

// De laatste 7 dagen als {iso, wd, dm}-objecten (ma-zo labels, v71 DAGN).
export function laatste7Dagen() {
  const DAGN = ['zo', 'ma', 'di', 'wo', 'do', 'vr', 'za']
  const iso = d => { const p = n => String(n).padStart(2, '0'); return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) }
  return [0, 1, 2, 3, 4, 5, 6].map(i => {
    const dt = new Date(); dt.setDate(dt.getDate() - (6 - i))
    return { iso: iso(dt), wd: DAGN[dt.getDay()], dm: dt.getDate() + '/' + (dt.getMonth() + 1) }
  })
}

export { omzetVerkochtJaar }
