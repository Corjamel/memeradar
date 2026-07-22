// Kleine API-laag voor het dashboard (eigen laag, zodat modules los blijven).
import { sb } from '../../lib/supabase.js'

export async function haalAms() {
  const { data, error } = await sb.from('accountmanagers').select('id,naam')
  if (error) throw new Error(error.message)
  return data || []
}
