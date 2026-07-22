// API-laag van de Community-module — de besloten tijdlijn per AM-portefeuille.
// RLS (migratie 013) bepaalt server-side wie welke posts ziet; de insert-guard
// zet am_id/author/role aan de bron, dus de client hoeft (en kan) niets forceren.
// Een partner geeft alleen de tekst mee — de rest bepaalt de database.
import { sb } from '../../lib/supabase.js'

export async function haalPosts() {
  const { data, error } = await sb.from('community')
    .select('*').order('created_at', { ascending: false })
  if (error) throw new Error(error.message)
  return data || []
}

// Plaatsen: alleen de tekst reist mee. De guard leidt portefeuille + auteur +
// rol af uit wie je bent (partner -> winkelnaam, AM -> AM-naam, kantoor -> HQ).
// Kantoor moet wél een doel-portefeuille meegeven (amId) voor een HQ-mededeling.
export async function plaats(txt, opts = {}) {
  const rij = { txt }
  if (opts.amId) rij.am_id = opts.amId
  if (opts.role) rij.role = opts.role
  if (opts.author) rij.author = opts.author
  const { error } = await sb.from('community').insert(rij)
  if (error) throw new Error(error.message)
}

// Modereren (alleen kantoor; RLS weigert het voor de rest).
export async function verwijder(id) {
  const { error } = await sb.from('community').delete().eq('id', id)
  if (error) throw new Error(error.message)
}
