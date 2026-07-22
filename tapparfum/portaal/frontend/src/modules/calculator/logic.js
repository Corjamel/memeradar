// Rekenlogica calculator — EXACT overgenomen uit v71 (r.671-673, 3098-3102).
// Deze getallen zijn de commerciële waarheid van TapParfum; nooit afronden of
// "verbeteren" zonder besluit van kantoor.

export const PKG = [
  { n: 'Pakket 80 geuren', inv: 3950 },
  { n: 'Pakket 100 geuren (incl. 15 Exclusive)', inv: 4702.5 },
  { n: 'Pakket 120 geuren (incl. 15 Exclusive)', inv: 5332.5 },
  { n: 'Pakket 160 geuren (incl. 20 Exclusive)', inv: 6692.5 },
  { n: 'Pakket 200 geuren (incl. 30 Exclusive)', inv: 8370 },
  { n: 'Pakket 240 geuren — WINKEL', inv: 9595 }
]

export const OMZETPF = {
  std: { bottle: [12.40, 16.53, 26.86], refill: [10.33, 14.46, 24.79] },
  excl: { bottle: [16.53, 20.66, 35.12], refill: [14.46, 18.60, 33.06] }
}
export const SIZEIDX = { 30: 0, 50: 1, 100: 2 }

export function omzetPF(type, mode, size) {
  return OMZETPF[type][mode][SIZEIDX[String(size)]]
}

// Break-even: hoeveel flessen om de pakket-investering terug te verdienen?
export function beModel({ pkg, type, mode, size, rate }) {
  const inv = PKG[pkg].inv
  const rev = omzetPF(type, mode, size)
  const bottles = Math.ceil(inv / rev)
  const perWk = Math.max(1, +rate || 1)
  const weeks = Math.ceil(bottles / perWk)
  return { inv, rev, perWk, days: weeks * 7, bottles }
}

// Jaardoel: hoeveel vaste klanten en flessen voor het omzetdoel?
export function goalModel({ doel, refills, type, size }) {
  const bottle = omzetPF(type, 'bottle', size)
  const refill = omzetPF(type, 'refill', size)
  const revKlant = bottle + refills * refill
  const klanten = Math.ceil(doel / revKlant)
  const flTot = klanten * (1 + refills)
  return {
    doel, klanten, revKlant,
    flJaar: flTot,
    flWeek: Math.round(flTot / 52 * 10) / 10,
    flDag: Math.round(flTot / 365 * 10) / 10,
    refills
  }
}
