// API-laag Deals (verkoopkansen). RLS: alleen kantoor en de AM van de winkel —
// partners zien deals bewust niet. Guard: winkel-koppeling ligt vast.
import { sb } from '../../lib/supabase.js'

export const FASEN = [
  ['lead', 'Lead'],
  ['voorstel', 'Voorstel'],
  ['onderhandeling', 'Onderhandeling'],
  ['gewonnen', 'Gewonnen'],
  ['verloren', 'Verloren']
]

// Win-kans per fase (voor de gewogen forecast). Afgeleid van de fase, dus geen
// extra kolom nodig — een standaard stage-weighted pijplijn. Kantoor kan dit
// later fijnregelen; deze waarden zijn een gangbaar uitgangspunt.
export const KANS = { lead: 0.10, voorstel: 0.30, onderhandeling: 0.60, gewonnen: 1, verloren: 0 }
export const OPEN_FASEN = ['lead', 'voorstel', 'onderhandeling']

export async function haalDeals() {
  const { data, error } = await sb.from('deals')
    .select('*').order('created_at', { ascending: false })
  if (error) throw new Error(error.message)
  return data || []
}

export async function nieuweDeal(d) {
  const { error } = await sb.from('deals').insert({
    tappunt_snelstart: d.tappunt_snelstart, titel: d.titel,
    waarde: Number(d.waarde) || 0, verwacht: d.verwacht || null, notitie: d.notitie || null
  })
  if (error) throw new Error(error.message)
}

export async function zetFase(id, fase) {
  const { error } = await sb.from('deals').update({ fase }).eq('id', id)
  if (error) throw new Error(error.message)
}

// Won/lost-reden vastleggen bij een afgesloten deal (kolom 'reden', migratie 016).
export async function zetReden(id, reden) {
  const { error } = await sb.from('deals').update({ reden: reden || null }).eq('id', id)
  if (error) throw new Error(error.message)
}
