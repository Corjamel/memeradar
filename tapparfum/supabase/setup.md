# TapParfum Portal → Supabase (Fase 1) — opzet

Doel: echte database, gedeeld tussen apparaten en winkels, met echte accounts en
**automatische wachtwoord-reset per e-mail**. De snelstartcode blijft de leidende
sleutel per winkel.

Dit is een samenwerking: **stap 1 en 2 doe jij** (alleen jij kunt een project
aanmaken), daarna wire ik de app en testen we samen.

---

## Stap 1 — Supabase-project aanmaken (jij, ~5 min)

1. Ga naar https://supabase.com → **Start your project** → log in (GitHub of e-mail).
2. **New project**:
   - Name: `tapparfum-portal`
   - Database Password: kies een sterk wachtwoord en **bewaar het**.
   - Region: **West EU (Amsterdam / Frankfurt)** — dichtbij, AVG-vriendelijk.
3. Wacht tot het project klaar is (~2 min).

> Belangrijk: maak het project op **jouw eigen account** — dan raak je het nooit
> kwijt (dit is exact wat in het portaal onder "Beveiliging" staat aangeraden).

## Stap 2 — Schema installeren + e-mail aanzetten (jij, ~3 min)

1. In je project: linkermenu → **SQL Editor** → **New query**.
2. Open `schema.sql` (in deze map), kopieer **alles**, plak in de editor → **Run**.
   Je hoort "Success. No rows returned" te zien.
3. Linkermenu → **Authentication → Providers → Email**: zet **Confirm email** aan
   en sla op. (Zo werken de verificatie- en reset-mails.)
4. Linkermenu → **Project Settings → API**. Noteer twee dingen en stuur ze me:
   - **Project URL** (bijv. `https://abcd1234.supabase.co`)
   - **anon public** key (de lange `eyJ...`-sleutel onder "Project API keys")

> De **anon key** is veilig om in de app te zetten — die mag publiek. De
> `service_role`-key deel je **nooit** en zet je nergens in de app.

## Stap 3 — Eerste kantoor-account = 'staff' (jij, ~2 min)

Kantoor/AM moeten het hele netwerk kunnen zien; partners alleen hun eigen winkel.

1. **Authentication → Users → Add user**: maak jouw kantoor-account
   (e-mail + wachtwoord).
2. Klik de aangemaakte gebruiker aan → bij **App metadata** → voeg toe:
   ```json
   { "role": "staff" }
   ```
   Bewaar. (Partners krijgen automatisch de standaardrol; alleen kantoor/AM
   zetten we op `staff`.)

---

## Stap 4 — App koppelen (ik, zodra ik URL + anon key heb)

Ik bouw dan in het portaal:
- Een **Supabase-verbinding** (jouw URL + anon key), met de huidige lokale opslag
  als terugval zolang er geen internet is.
- **Eerste login partner:** snelstartcode → account aanmaken (e-mail + wachtwoord
  via Supabase Auth) → gekoppeld aan de winkel via de meegeleverde `claim_tappunt`.
- **Daarna:** inloggen met e-mail + wachtwoord.
- **Wachtwoord vergeten:** echte reset-mail van Supabase (werkt nu wél automatisch).
- **Kantoor/AM:** inloggen met hun staff-account; zien het hele netwerk.
- Data (winkels + centrale config) leeft in de database en is op elk apparaat gelijk.

## Stap 5 — Migreren van je huidige gegevens (samen)

Heb je nu al winkels in een lokaal bestand? Dan:
1. In dat bestand: **Back-up** (download-knop in het portaal) → levert een JSON.
2. Ik lever een klein importscript dat die back-up in de database zet, met de
   snelstartcodes als sleutel — niets gaat verloren.

---

## Waarom dit het probleem definitief oplost
- Geen losse bestanden meer met wisselende, wisbare opslag → één database.
- Elk apparaat (jij, je AM's, elke winkel) ziet dezelfde, actuele gegevens.
- Wachtwoorden staan veilig op de server; reset-mail gaat automatisch.
- De server dwingt af wie wat mag zien (Row Level Security) — geen datalek meer
  tussen winkels, ook niet via de browserconsole.

## Wat je aan mij doorgeeft om verder te gaan
1. **Project URL**
2. **anon public key**
(Deze twee zijn genoeg. De service_role-key en je database-wachtwoord houd je voor
jezelf.)
