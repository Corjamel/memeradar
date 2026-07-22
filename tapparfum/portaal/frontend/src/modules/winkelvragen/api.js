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

// Partner: vraag/probleem/retour melden vanuit zijn winkel — optioneel met
// bewijsfoto. De foto gaat privé de tp-docs-bucket in (map van de winkel,
// Storage-RLS van migratie 003 dekt hem af); de melding krijgt alleen het pad.
export async function stuurWinkelvraag({ tappunt_snelstart, type, txt, foto }) {
  let foto_pad = null
  if (foto) {
    foto_pad = `${tappunt_snelstart}/melding_${Date.now()}_${foto.name}`
    const { error: fe } = await sb.storage.from('tp-docs').upload(foto_pad, foto)
    if (fe) throw new Error('Foto uploaden mislukt: ' + fe.message)
  }
  const { error } = await sb.from('winkelvragen')
    .insert({ tappunt_snelstart, type: type || 'vraag', txt, ...(foto_pad ? { foto_pad } : {}) })
  if (error) throw new Error(error.message)
}

// Tijdelijke (signed) link naar de bewijsfoto van een melding.
export async function fotoLink(foto_pad) {
  const { data, error } = await sb.storage.from('tp-docs').createSignedUrl(foto_pad, 60)
  if (error) throw new Error(error.message)
  return data.signedUrl
}

// AM/kantoor: beantwoorden.
export async function beantwoordWinkelvraag(id, antwoord, door) {
  const { error } = await sb.from('winkelvragen')
    .update({ status: 'beantwoord', antwoord, antwoord_door: door || null, antwoord_at: new Date().toISOString() })
    .eq('id', id)
  if (error) throw new Error(error.message)
}
