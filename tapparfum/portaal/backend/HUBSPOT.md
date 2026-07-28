# HubSpot-koppeling (read-only) — deploy-stappenplan

Het portaal toont per winkel de gematchte **HubSpot-bedrijven, contactpersonen
en deals** (alleen kantoor/AM, read-only). De koppeling loopt via een Supabase
**Edge Function** (`hubspot-read`) die het HubSpot-token server-side bewaart —
het token staat **nooit** in de frontend.

## Wat matcht op wat
| Portaal (tappunt) | HubSpot |
|---|---|
| Winkelnaam | Company `name` (bevat-match) |
| E-mailadres | Contact `email` (exact) |
| Snelstartcode | Company-property (alleen als `HUBSPOT_SNELSTART_PROP` is gezet) |

> In jullie HubSpot bestaat (nog) geen snelstart-property op bedrijven. Matchen
> werkt dus op winkelnaam + e-mail. Wil je ook op snelstart matchen? Maak in
> HubSpot een company-property aan met de snelstartcode en zet de interne naam
> in de secret `HUBSPOT_SNELSTART_PROP`.

## Stap 1 — HubSpot Private App + token
1. HubSpot → **Settings → Integrations → Private Apps → Create a private app**.
2. Naam bv. `TapParfum Portaal (read-only)`.
3. Tabblad **Scopes** → alleen lezen aanzetten:
   - `crm.objects.companies.read`
   - `crm.objects.contacts.read`
   - `crm.objects.deals.read`
4. **Create app** → kopieer het **Access token** (begint met `pat-...`).

## Stap 2 — Secrets in Supabase
Zet het token als Edge-Function-secret (nooit in de repo/frontend):

```bash
supabase secrets set HUBSPOT_TOKEN=pat-xxxxxxxx
# optioneel, alleen als je een snelstart-property in HubSpot hebt:
supabase secrets set HUBSPOT_SNELSTART_PROP=jouw_interne_propertynaam
```
`SUPABASE_URL` en `SUPABASE_ANON_KEY` staan er standaard al.

## Stap 3 — Functie deployen
De functiecode staat in `backend/functions/hubspot-read/index.ts`. Supabase
verwacht functies onder `supabase/functions/` — kopieer de map daarheen (of
maak 'm daar aan) en deploy:

```bash
# vanuit je supabase-projectmap
mkdir -p supabase/functions/hubspot-read
cp <repo>/tapparfum/portaal/backend/functions/hubspot-read/index.ts supabase/functions/hubspot-read/
supabase functions deploy hubspot-read
```

Klaar. De frontend roept de functie automatisch aan via
`supabase.functions.invoke('hubspot-read', …)`; er is niets extra's nodig aan de
Vue-kant. Tot de functie live staat toont het paneel netjes *"HubSpot-koppeling
is nog niet gedeployed."* — geen foutscherm.

## Veiligheid
- **Read-only**: de private app heeft alleen `*.read`-scopes; het portaal kan
  niets in HubSpot wijzigen.
- **Alleen kantoor/AM**: de functie weigert (403) iedereen die geen staf is en
  niet in `accountmanagers` staat — partners zien niets.
- **Token blijft geheim**: het staat als Supabase-secret, nooit in client-code.
