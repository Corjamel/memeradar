// API-laag Beloningen: de tredenladder (op jaaromzet) als netwerk-config in de
// central-tabel (ns 'beloningen'). Iedereen leest, alleen kantoor schrijft.
import { sb } from '../../lib/supabase.js'

export const STANDAARD_TREDEN = [
  { id: 'brons',   naam: 'Brons',   drempel: 2500,  tekst: 'Welkomstpakket display-materiaal' },
  { id: 'zilver',  naam: 'Zilver',  drempel: 5000,  tekst: 'Extra korting op de eerstvolgende bestelling' },
  { id: 'goud',    naam: 'Goud',    drempel: 10000, tekst: 'Gratis navul-actie voor de winkel' },
  { id: 'platina', naam: 'Platina', drempel: 20000, tekst: 'VIP: voorrang op nieuwe geuren + uitnodiging event' }
]

export async function haalTreden() {
  const { data, error } = await sb.from('central').select('ns,data').eq('ns', 'beloningen')
  if (error) throw new Error(error.message)
  const row = (data || [])[0]
  const arr = Array.isArray(row && row.data) ? row.data : []
  return arr.length ? arr : STANDAARD_TREDEN
}

// Alleen kantoor (server dwingt af).
export async function bewaarTreden(arr) {
  const { error } = await sb.from('central').upsert({ ns: 'beloningen', data: arr }, { onConflict: 'ns' })
  if (error) throw new Error(error.message)
}

// Bepaal huidige + volgende trede voor een omzet.
export function tredeVoor(omzet, treden) {
  const lijst = (treden && treden.length ? treden : STANDAARD_TREDEN)
    .slice().sort((a, b) => a.drempel - b.drempel)
  let huidig = null, volgende = null
  for (const tr of lijst) {
    if (omzet >= tr.drempel) huidig = tr
    else { volgende = tr; break }
  }
  const pct = volgende ? Math.min(100, Math.round((omzet / volgende.drempel) * 100)) : 100
  return { huidig, volgende, pct }
}
