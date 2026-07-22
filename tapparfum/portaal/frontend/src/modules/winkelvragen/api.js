// API-laag Winkelvragen (partner -> AM/kantoor). RLS: partner alleen eigen
// winkel, AM zijn winkels, kantoor alles. De kolom-guard (migratie 007) zorgt
// dat een antwoorder de oorspronkelijke vraag nooit kan herschrijven.
import { sb } from '../../lib/supabase.js'

export async function haalWinkelvragen() {
  const { data, error } = await sb.from('winkelvragen')
    .select('*').order('created_at', { ascending: false })
  if (error) throw new Error(error.message)
  return data || []
}

// Partner: vraag/probleem/retour melden vanuit zijn winkel.
export async function stuurWinkelvraag({ tappunt_snelstart, type, txt }) {
  const { error } = await sb.from('winkelvragen')
    .insert({ tappunt_snelstart, type: type || 'vraag', txt })
  if (error) throw new Error(error.message)
}

// AM/kantoor: beantwoorden.
export async function beantwoordWinkelvraag(id, antwoord, door) {
  const { error } = await sb.from('winkelvragen')
    .update({ status: 'beantwoord', antwoord, antwoord_door: door || null, antwoord_at: new Date().toISOString() })
    .eq('id', id)
  if (error) throw new Error(error.message)
}
