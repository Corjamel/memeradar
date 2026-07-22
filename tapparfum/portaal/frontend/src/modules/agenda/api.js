// API-laag Agenda. RLS: kantoor alles, AM eigen bezoeken, partner alleen die
// van zijn winkel. De kolom-guard (migratie 006) laat een partner uitsluitend
// accepteren/afwijzen — datum/winkel/AM kan hij niet aanraken.
import { sb } from '../../lib/supabase.js'

export async function haalAgenda() {
  const { data, error } = await sb.from('agenda')
    .select('*').order('datum', { ascending: true })
  if (error) throw new Error(error.message)
  return data || []
}

// AM/kantoor: bezoek voorstellen.
export async function planBezoek({ tappunt_snelstart, am_id, datum, tijd, type, notitie }) {
  const { error } = await sb.from('agenda')
    .insert({ tappunt_snelstart, am_id: am_id || null, datum, tijd: tijd || null, type: type || 'bezoek', notitie: notitie || null })
  if (error) throw new Error(error.message)
}

// Status zetten: partner -> geaccepteerd/afgewezen; AM -> afgerond (server bewaakt).
export async function zetStatus(id, status) {
  const { error } = await sb.from('agenda').update({ status }).eq('id', id)
  if (error) throw new Error(error.message)
}
