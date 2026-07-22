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

// Audit-log (migratie 010, alleen staff). Loggen mag nooit een actie blokkeren.
export async function haalLog() {
  const { data, error } = await sb.from('beheerlog')
    .select('*').order('at', { ascending: false }).limit(25)
  if (error) throw new Error(error.message)
  return data || []
}

export async function log(wie, txt) {
  try { await sb.from('beheerlog').insert({ wie: wie || null, txt }) } catch (e) { /* stil */ }
}

// AVG: welke velden bij anonimiseren gewist worden — exact de v71-lijst (bhAnon).
export const AVG_WIS_VELDEN = ['contact', 'email', 'tel', 'adres', 'postcode', 'plaats', 'web', 'bezoekmoment', 'notes', 'display', 'jarig']
export const AVG_WIS_ARRAYS = ['logboek', 'afspraken', 'signalen', 'bestellingen', 'react', 'flesLog']
export const AVG_WIS_OBJECTEN = ['verkopen', 'fu', 'bp', 'bonus', 'forms', 'setup', 'goal', 'be', 'beloond']

export function anonimiseer(t) {
  const t2 = { ...t }
  for (const k of AVG_WIS_VELDEN) t2[k] = ''
  for (const k of AVG_WIS_ARRAYS) t2[k] = []
  for (const k of AVG_WIS_OBJECTEN) t2[k] = {}
  t2.jaaromzet = 0; t2.vorigJaar = 0; t2.doel = 0; t2.klanten = 0
  t2.name = 'Verwijderd tappunt'
  return t2
}
