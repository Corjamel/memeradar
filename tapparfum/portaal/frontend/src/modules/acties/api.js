// API-laag Acties: netwerkbrede campagnes in de central-tabel (ns 'acties').
// RLS (migratie 001): iedereen die is ingelogd mag lezen, alleen kantoor
// (staff) mag schrijven — precies wat een campagne nodig heeft.
import { sb } from '../../lib/supabase.js'

export async function haalActies() {
  const { data, error } = await sb.from('central').select('ns,data').eq('ns', 'acties')
  if (error) throw new Error(error.message)
  const row = (data || [])[0]
  return Array.isArray(row && row.data) ? row.data : []
}

// Alleen kantoor (server dwingt af via central_staff_write).
export async function bewaarActies(arr) {
  const { error } = await sb.from('central').upsert({ ns: 'acties', data: arr }, { onConflict: 'ns' })
  if (error) throw new Error(error.message)
}

export function isActief(a, vandaag) {
  const d = vandaag || new Date().toISOString().slice(0, 10)
  return !a.archived && (!a.eind || a.eind >= d)
}
