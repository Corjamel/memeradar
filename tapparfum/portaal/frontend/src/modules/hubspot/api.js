// HubSpot read-only koppeling — praat NOOIT rechtstreeks met HubSpot (token is
// geheim), maar met de Supabase Edge Function 'hubspot-read', die server-side
// het token bewaart en alleen het gematchte resultaat teruggeeft.
import { sb } from '../../lib/supabase.js'

export async function haalHubspot({ winkelnaam = '', email = '', snelstart = '' }) {
  // Test-hook (zelfde patroon als window.__MOCK.signin): in productie bestaat dit niet.
  if (typeof window !== 'undefined' && window.__MOCK && window.__MOCK.hubspot) {
    const m = window.__MOCK.hubspot
    if (m.error) throw new Error(m.error)
    return m
  }
  if (!sb || !sb.functions || !sb.functions.invoke) throw new Error('HubSpot-koppeling is nog niet gedeployed.')
  const { data, error } = await sb.functions.invoke('hubspot-read', { body: { winkelnaam, email, snelstart } })
  if (error) throw new Error(error.message || 'HubSpot-aanroep mislukt.')
  if (data && data.error) throw new Error(data.error)
  return data || { companies: [], contacts: [], deals: [] }
}
