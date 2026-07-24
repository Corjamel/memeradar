// Omzet-historie (v71 joLog): een tijdlijn van gemeten jaaromzetten, zodat we
// een trend kunnen tonen. v71 hield het veld wel bij maar schreef het nooit —
// hier sluiten we het schrijfpad alsnog aan: elke keer dat de jaaromzet écht
// verandert, leggen we een meetpunt {at, v} vast (één per dag; dezelfde dag
// werken we bij i.p.v. dubbel te loggen).
export function registreerOmzetSnapshot(nieuw, oud, vandaag) {
  const v = Number(nieuw && nieuw.jaaromzet) || 0
  if (v <= 0) return nieuw                       // 0 of leeg = niets te loggen
  const vorige = oud ? (Number(oud.jaaromzet) || 0) : null
  if (vorige != null && vorige === v) return nieuw   // niets gewijzigd
  const dag = vandaag || new Date().toISOString().slice(0, 10)
  const basis = Array.isArray(nieuw.joLog) ? nieuw.joLog
    : (oud && Array.isArray(oud.joLog) ? oud.joLog : [])
  const log = basis.map(e => ({ ...e }))
  const laatste = log[log.length - 1]
  if (laatste && String(laatste.at).slice(0, 10) === dag) laatste.v = v
  else log.push({ at: dag, v })
  nieuw.joLog = log
  return nieuw
}

// De laatste ~8 meetpunten als getallen (voor de sparkline).
export function omzetTrend(t) {
  return (Array.isArray(t && t.joLog) ? t.joLog : []).slice(-8).map(e => Number(e.v) || 0)
}
