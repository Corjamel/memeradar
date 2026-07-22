// API-laag Documenten: privé bestanden per winkel in de 'tp-docs'-bucket.
// Toegang wordt door Storage-RLS (migratie 003) afgedwongen: partner alleen de
// map van zijn winkel, AM die van zijn winkels, kantoor alles. Bestanden zijn
// nooit publiek — openen gaat via tijdelijke (signed) links.
import { sb } from '../../lib/supabase.js'

export async function lijstDocumenten(snelstart) {
  const { data, error } = await sb.storage.from('tp-docs')
    .list(snelstart, { limit: 100, sortBy: { column: 'name', order: 'desc' } })
  if (error) throw new Error(error.message)
  return data || []
}

export async function uploadDocument(snelstart, file) {
  const pad = `${snelstart}/${Date.now()}_${file.name}`
  const { error } = await sb.storage.from('tp-docs').upload(pad, file)
  if (error) throw new Error(error.message)
}

export async function openLink(snelstart, naam) {
  const { data, error } = await sb.storage.from('tp-docs')
    .createSignedUrl(`${snelstart}/${naam}`, 60)
  if (error) throw new Error(error.message)
  return data.signedUrl
}
