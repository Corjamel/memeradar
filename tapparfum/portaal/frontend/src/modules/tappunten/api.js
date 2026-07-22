// API-laag van de Tappunten-module. Praat als enige met de 'tappunten'-tabel.
//
// Beveiliging: RLS bepaalt server-side welke rijen je krijgt (kantoor alles,
// AM eigen winkels, partner eigen winkel) en de kolom-guard (migratie 004)
// beschermt geblokkeerd/snelstart/am_id. Wij sturen die velden bij een gewone
// save sowieso nooit mee — defensie in de diepte.
import { sb } from '../../lib/supabase.js'

export function rijNaarTappunt(row) {
  const t = (row.data && typeof row.data === 'object') ? { ...row.data } : {}
  t.snelstart = t.snelstart || row.snelstart
  t.name = t.name || row.name
  if (row.email && !t.email) t.email = row.email
  t.geblokkeerd = !!row.geblokkeerd
  if (row.am_id) t.am_id = row.am_id
  return t
}

export async function haalTappunten() {
  const { data, error } = await sb.from('tappunten')
    .select('snelstart,name,email,geblokkeerd,am_id,data')
  if (error) throw new Error(error.message)
  return (data || []).map(rijNaarTappunt)
}

export async function bewaarTappunt(t) {
  const d = { ...t }
  delete d.auth               // lokale inloggegevens horen nooit in de cloud
  const row = {
    snelstart: t.snelstart,
    name: t.name || t.snelstart,
    email: t.email || null,
    data: d
    // bewust NIET: geblokkeerd / am_id / auth_user_id (alleen-kantoor-velden)
  }
  const { error } = await sb.from('tappunten').upsert(row, { onConflict: 'snelstart' })
  if (error) throw new Error(error.message)
}

// Alleen kantoor (RLS + kolom-guard dwingen dat af): blokkeren/deblokkeren.
export async function zetBlokkade(snelstart, geblokkeerd) {
  const { error } = await sb.from('tappunten')
    .update({ geblokkeerd }).eq('snelstart', snelstart)
  if (error) throw new Error(error.message)
}
