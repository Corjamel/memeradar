// API-laag Contacten (contactpersonen bij een winkel). RLS: winkel zelf, de AM
// van de winkel en kantoor; verwijderen alleen AM/kantoor. De guard (migratie
// 008) voorkomt dat een contact naar een andere winkel verplaatst wordt.
import { sb } from '../../lib/supabase.js'

export async function haalContacten(snelstart) {
  const { data, error } = await sb.from('contacten')
    .select('*').eq('tappunt_snelstart', snelstart).order('naam', { ascending: true })
  if (error) throw new Error(error.message)
  return data || []
}

export async function voegContactToe(c) {
  const { error } = await sb.from('contacten').insert({
    tappunt_snelstart: c.tappunt_snelstart, naam: c.naam,
    functie: c.functie || null, tel: c.tel || null, email: c.email || null
  })
  if (error) throw new Error(error.message)
}

export async function verwijderContact(id) {
  const { error } = await sb.from('contacten').delete().eq('id', id)
  if (error) throw new Error(error.message)
}
