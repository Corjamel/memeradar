// Sales Game — landelijk klassement via het server-aggregaat (migratie 019).
// RLS geeft een partner alleen de eigen winkel; dit RPC rekent server-side over
// ÁLLE traject-tappunten en geeft een geanonimiseerd klassement terug (andere
// winkels heten "Winkel #n"). Degradeert netjes: staat de functie nog niet live,
// dan valt de view terug op het lokale (RLS-gescoped) klassement.
import { sb } from '../../lib/supabase.js'

export async function haalGameBoard({ minPunten = 0, minBasis = 0 } = {}) {
  if (typeof sb.rpc !== 'function') return null
  const { data, error } = await sb.rpc('tp_salesgame_board', {
    p_min_punten: Math.max(0, parseInt(minPunten) || 0),
    p_min_basis: Math.max(0, parseInt(minBasis) || 0)
  })
  if (error) throw new Error(error.message)
  // Alleen een echte array = een (mogelijk leeg) landelijk klassement. Iets
  // anders (null) → functie niet beschikbaar → de view valt terug op lokaal.
  return Array.isArray(data) ? data : null
}
