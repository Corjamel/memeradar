// API-laag Taken. RLS: kantoor alles, een AM alleen zijn eigen taken. Guard:
// een AM kan een taak niet aan een ander overdragen.
import { sb } from '../../lib/supabase.js'

export async function haalTaken() {
  const { data, error } = await sb.from('taken')
    .select('*').order('deadline', { ascending: true })
  if (error) throw new Error(error.message)
  return data || []
}

export async function nieuweTaak(t) {
  const { error } = await sb.from('taken').insert({
    titel: t.titel, am_id: t.am_id || null,
    tappunt_snelstart: t.tappunt_snelstart || null, deadline: t.deadline || null
  })
  if (error) throw new Error(error.message)
}

export async function zetKlaar(id, klaar) {
  const { error } = await sb.from('taken').update({ klaar }).eq('id', id)
  if (error) throw new Error(error.message)
}

export async function haalAms() {
  const { data, error } = await sb.from('accountmanagers').select('id,naam')
  if (error) throw new Error(error.message)
  return data || []
}
