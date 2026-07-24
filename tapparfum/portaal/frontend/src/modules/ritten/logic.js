// Ritten-logica (puur): dagen groeperen en de km-keten schatten. De km-som is
// hemelsbreed (haversine) — bewust een INDICATIE, geen rittenadministratie.
export const TYPE_LABEL = { start: '🟢 Start werkdag', stop: '⏹ Stop werkdag', bezoek: '📍 Bezoek' }

export function haversineKm(a, b) {
  if (!a || !b || !Number.isFinite(a.lat) || !Number.isFinite(b.lat)) return 0
  const R = 6371, rad = d => d * Math.PI / 180
  const dLat = rad(b.lat - a.lat), dLng = rad(b.lng - a.lng)
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(s)))
}

const dagVan = (r) => String(r.at || '').slice(0, 10)
const tijdVan = (r) => { const s = String(r.at || ''); const m = s.match(/T(\d{2}:\d{2})/); return m ? m[1] : '' }

// Groepeer stempels per dag (nieuwste dag eerst), chronologisch binnen de dag,
// met een km-keten over de opeenvolgende punten die een coördinaat hebben.
export function groepeerPerDag(rows) {
  const perDag = new Map()
  ;(rows || []).forEach(r => {
    const d = dagVan(r); if (!d) return
    if (!perDag.has(d)) perDag.set(d, [])
    perDag.get(d).push({ ...r, tijd: tijdVan(r) })
  })
  const uit = []
  for (const [dag, lijst] of perDag) {
    lijst.sort((a, b) => String(a.at).localeCompare(String(b.at)))
    let km = 0, vorig = null
    lijst.forEach(s => {
      if (Number.isFinite(s.lat) && Number.isFinite(s.lng)) {
        if (vorig) km += haversineKm(vorig, s)
        vorig = s
      }
    })
    const nBezoek = lijst.filter(s => s.type === 'bezoek').length
    uit.push({ dag, stempels: lijst, km: Math.round(km * 10) / 10, nBezoek, open: !!lijst.find(s => s.type === 'start' && !lijst.find(x => x.type === 'stop')) })
  }
  return uit.sort((a, b) => (a.dag < b.dag ? 1 : -1))
}

export const mapsLink = (s) => (Number.isFinite(s.lat) && Number.isFinite(s.lng))
  ? `https://maps.google.com/?q=${s.lat},${s.lng}` : null
