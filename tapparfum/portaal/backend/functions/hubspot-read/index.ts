// ============================================================================
// TapParfum Portaal — HubSpot read-only koppeling (Supabase Edge Function)
// ----------------------------------------------------------------------------
// WAAROM SERVER-SIDE: het HubSpot private-app-token is een geheim. Het mag nooit
// in de (publieke) Vue-app staan. Deze functie bewaart het als Supabase-secret,
// leest HubSpot en geeft alleen het gematchte resultaat terug aan een INGELOGDE
// staf-/AM-gebruiker. Partners krijgen niets (403).
//
// MATCHT een tappunt op HubSpot via, in deze volgorde:
//   1. snelstartcode  — alleen als HUBSPOT_SNELSTART_PROP is gezet (company-prop)
//   2. winkelnaam     — company.name (bevat-match)
//   3. e-mailadres    — contact.email (exacte match) + diens bedrijf
//
// SECRETS (Supabase → Project Settings → Edge Functions → Secrets):
//   HUBSPOT_TOKEN            (verplicht)  private-app-token, scope: crm.objects.*.read
//   HUBSPOT_SNELSTART_PROP   (optioneel)  interne naam van de snelstart-property op company
//   SUPABASE_URL / SUPABASE_ANON_KEY      (staan er standaard al)
// ============================================================================
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const HS = 'https://api.hubapi.com'
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS'
}
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, 'Content-Type': 'application/json' } })

async function hs(token: string, path: string, init: RequestInit = {}) {
  const r = await fetch(HS + path, {
    ...init,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', ...(init.headers || {}) }
  })
  if (!r.ok) throw new Error(`HubSpot ${r.status} op ${path}: ${(await r.text()).slice(0, 200)}`)
  return r.json()
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS })
  if (req.method !== 'POST') return json({ error: 'Alleen POST' }, 405)

  const token = Deno.env.get('HUBSPOT_TOKEN')
  if (!token) return json({ error: 'HUBSPOT_TOKEN ontbreekt — zet het als Edge-Function-secret.' }, 500)

  // --- 1. Authenticatie: alleen een ingelogde staf-/AM-gebruiker mag lezen ---
  const authHeader = req.headers.get('Authorization') || ''
  const supa = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_ANON_KEY')!,
    { global: { headers: { Authorization: authHeader } } }
  )
  const { data: { user } } = await supa.auth.getUser()
  if (!user) return json({ error: 'Niet ingelogd' }, 401)
  const isStaff = (user.app_metadata as Record<string, unknown>)?.role === 'staff'
  let isAm = false
  if (!isStaff) {
    const { data } = await supa.from('accountmanagers').select('id').eq('auth_user_id', user.id).limit(1)
    isAm = !!(data && data.length)
  }
  if (!isStaff && !isAm) return json({ error: 'Geen toegang tot HubSpot (alleen kantoor/AM).' }, 403)

  // --- 2. Invoer: de identificatie van het tappunt ---
  const { winkelnaam = '', email = '', snelstart = '' } = await req.json().catch(() => ({}))
  const snelProp = Deno.env.get('HUBSPOT_SNELSTART_PROP') || ''

  try {
    // --- 3a. Bedrijven zoeken (op snelstart-prop indien geconfigureerd, anders naam) ---
    const bedrijfGroepen: unknown[] = []
    if (snelProp && snelstart) bedrijfGroepen.push({ filters: [{ propertyName: snelProp, operator: 'EQ', value: snelstart }] })
    if (winkelnaam) bedrijfGroepen.push({ filters: [{ propertyName: 'name', operator: 'CONTAINS_TOKEN', value: winkelnaam }] })
    let companies: Record<string, unknown>[] = []
    if (bedrijfGroepen.length) {
      const cRes = await hs(token, '/crm/v3/objects/companies/search', {
        method: 'POST',
        body: JSON.stringify({
          filterGroups: bedrijfGroepen,
          properties: ['name', 'city', 'domain', 'phone', 'hs_lead_status'],
          limit: 5
        })
      })
      companies = (cRes.results || []).map((c: Record<string, unknown>) => ({ id: c.id, ...(c.properties as object) }))
    }

    // --- 3b. Contacten zoeken op e-mail ---
    let contacts: Record<string, unknown>[] = []
    if (email) {
      const kRes = await hs(token, '/crm/v3/objects/contacts/search', {
        method: 'POST',
        body: JSON.stringify({
          filterGroups: [{ filters: [{ propertyName: 'email', operator: 'EQ', value: email }] }],
          properties: ['firstname', 'lastname', 'email', 'phone', 'jobtitle'],
          limit: 5
        })
      })
      contacts = (kRes.results || []).map((c: Record<string, unknown>) => ({ id: c.id, ...(c.properties as object) }))
    }

    // --- 3c. Deals gekoppeld aan het best-matchende bedrijf ---
    let deals: Record<string, unknown>[] = []
    const bedrijfId = companies[0]?.id
    if (bedrijfId) {
      const assoc = await hs(token, `/crm/v4/objects/companies/${bedrijfId}/associations/deals?limit=25`)
      const ids = (assoc.results || []).map((a: Record<string, unknown>) => a.toObjectId).filter(Boolean)
      if (ids.length) {
        const dRes = await hs(token, '/crm/v3/objects/deals/batch/read', {
          method: 'POST',
          body: JSON.stringify({
            properties: ['dealname', 'amount', 'deal_currency_code', 'dealstage', 'pipeline', 'closedate'],
            inputs: ids.slice(0, 25).map((id: unknown) => ({ id }))
          })
        })
        deals = (dRes.results || []).map((d: Record<string, unknown>) => ({ id: d.id, ...(d.properties as object) }))
      }
    }

    return json({ companies, contacts, deals, matchedCompanyId: bedrijfId || null })
  } catch (e) {
    return json({ error: String((e as Error).message || e) }, 502)
  }
})
