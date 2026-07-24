// API-laag Ritten & locatie-archief (tabel am_locaties, migratie 014).
//
// Beveiliging = RLS (server-side): kantoor leest alles, een AM alleen zijn eigen
// stempels, een partner niets. De BEFORE INSERT-guard zet am_id op de ingelogde
// AM — de client bepaalt dat dus nooit. Verwijderen mag alleen kantoor.
import { sb } from '../../lib/supabase.js'

export async function haalLocaties() {
  const { data, error } = await sb.from('am_locaties')
    .select('id,am_id,type,tappunt_snelstart,lat,lng,acc,loc,at')
    .order('at', { ascending: false })
  if (error) throw new Error(error.message)
  return data || []
}

// Plaats een stempel. am_id wordt server-side gezet (guard). Zonder locatie
// (aan/uit-knop uit, of geolocatie geweigerd) sturen we bewust geen coördinaten.
export async function stempel({ type, tappunt_snelstart = null, gps = null }) {
  const rij = { type, tappunt_snelstart, at: new Date().toISOString() }
  if (gps && Number.isFinite(gps.lat) && Number.isFinite(gps.lng)) {
    rij.lat = gps.lat; rij.lng = gps.lng
    if (Number.isFinite(gps.acc)) rij.acc = Math.round(gps.acc)
  }
  const { error } = await sb.from('am_locaties').insert(rij)
  if (error) throw new Error(error.message)
}

// Verwijderen: RLS laat dit alleen voor kantoor slagen.
export async function verwijderLocatie(id) {
  const { error } = await sb.from('am_locaties').delete().eq('id', id)
  if (error) throw new Error(error.message)
}

// Eén losse locatiepeiling via de browser (v71 geoStamp): geen doorlopende
// tracking. Lost op met {lat,lng,acc} of met null (geweigerd/niet beschikbaar).
export function geoStamp() {
  return new Promise((resolve) => {
    try {
      if (typeof navigator === 'undefined' || !navigator.geolocation) return resolve(null)
      navigator.geolocation.getCurrentPosition(
        p => resolve({ lat: +p.coords.latitude.toFixed(6), lng: +p.coords.longitude.toFixed(6), acc: p.coords.accuracy || 0 }),
        () => resolve(null),
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
      )
    } catch (e) { resolve(null) }
  })
}
