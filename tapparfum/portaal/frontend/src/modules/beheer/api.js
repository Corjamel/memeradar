// API-laag Beheer (alleen kantoor — RLS am_staff_all + staff-update bewaken dit).
import { sb } from '../../lib/supabase.js'

export async function haalAms() {
  const { data, error } = await sb.from('accountmanagers')
    .select('id,naam,email,auth_user_id').order('naam', { ascending: true })
  if (error) throw new Error(error.message)
  return data || []
}

export async function voegAmToe(naam, email) {
  const { error } = await sb.from('accountmanagers')
    .insert({ naam, email: String(email).toLowerCase() })
  if (error) throw new Error(error.message)
}

export async function verwijderAm(id) {
  const { error } = await sb.from('accountmanagers').delete().eq('id', id)
  if (error) throw new Error(error.message)
}

// Winkel aan een AM hangen (of loskoppelen met null) — alleen staff mag dit.
export async function zetWinkelAm(snelstart, am_id) {
  const { error } = await sb.from('tappunten')
    .update({ am_id: am_id || null }).eq('snelstart', snelstart)
  if (error) throw new Error(error.message)
}

// Netwerk-instellingen in de central-tabel (RLS: iedereen leest, staff schrijft).
export async function haalCentral(ns) {
  const { data, error } = await sb.from('central').select('ns,data').eq('ns', ns)
  if (error) throw new Error(error.message)
  const row = (data || [])[0]
  return row ? row.data : null
}

export async function bewaarCentral(ns, data) {
  const { error } = await sb.from('central').upsert({ ns, data }, { onConflict: 'ns' })
  if (error) throw new Error(error.message)
}
