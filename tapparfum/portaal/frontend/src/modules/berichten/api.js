// API-laag van de Berichten-module (kantoor ↔ accountmanager).
// RLS bepaalt server-side wie wat ziet; de kolom-guard in migratie 005 zorgt
// dat een AM alleen status/antwoord kan wijzigen, nooit de vraag zelf.
import { sb } from '../../lib/supabase.js'

export async function haalBerichten() {
  const { data, error } = await sb.from('berichten')
    .select('*').order('created_at', { ascending: false })
  if (error) throw new Error(error.message)
  return data || []
}

export async function haalAccountmanagers() {
  const { data, error } = await sb.from('accountmanagers').select('id,naam')
  if (error) throw new Error(error.message)
  return data || []
}

// Kantoor: vraag of taak versturen aan een AM.
export async function stuurBericht({ aan_am, type, txt, van }) {
  const { error } = await sb.from('berichten')
    .insert({ aan_am, type, txt, van: van || 'kantoor' })
  if (error) throw new Error(error.message)
}

// AM: bericht beantwoorden (alleen status/antwoord — meer staat de server niet toe).
export async function beantwoord(id, antwoord) {
  const { error } = await sb.from('berichten')
    .update({ status: 'klaar', antwoord, antwoord_at: new Date().toISOString() })
    .eq('id', id)
  if (error) throw new Error(error.message)
}
