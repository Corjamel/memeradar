# TapParfum Portaal — installeren & online zetten (voor de eigenaar)

Drie stappen, ±10 minuten. De oude app (v71) blijft gewoon draaien — dit
portaal komt er als **aparte testsite** naast (strangler-aanpak, zie
ARCHITECTURE.md §9). Beide gebruiken dezelfde Supabase-database.

---

## Stap 1 — Database bijwerken (Supabase, ~2 min)

1. Ga naar https://supabase.com → log in → open je project **tapparfum-portal**.
2. Linkermenu → **SQL Editor** → **New query**.
3. Open het bestand **`tapparfum_portaal_database.sql`** (alles-in-één),
   kopieer ALLES, plak in de editor → **Run**.
4. Je hoort "Success" te zien. Klaar.

> Veilig om opnieuw te draaien: het script is idempotent — bestaande tabellen
> en data blijven onaangetast. Het bevat migraties 001 t/m 008 (winkels, AM-
> isolatie, documenten-opslag, kolom-bescherming, berichten, agenda,
> winkelvragen en het CRM: contacten/deals/taken).

## Stap 2 — Portaal online zetten (Netlify, ~3 min)

1. Ga naar https://app.netlify.com → log in.
2. Kies **Add new site → Deploy manually** (de "drag & drop"-pagina).
3. Sleep het bestand **`tapparfum_portaal_site.zip`** in het vak.
4. Netlify pakt het uit en geeft je een link (bijv. `https://iets.netlify.app`).
   Hernoem de site gerust naar `tapparfum-portaal-test`
   (Site settings → Change site name).

> Belangrijk: maak een NIEUWE site — overschrijf niet de site waar v71 op
> draait. De oude app blijft de hoofdapp tot het portaal alles kan.

## Stap 3 — Inloggen en testen

1. Open de Netlify-link in je browser.
2. Log in met je **kantoor-account** (het e-mailadres + wachtwoord dat je in
   Supabase → Authentication hebt aangemaakt met rol `staff`).
3. Je landt in de **Kantoor-cockpit**. Loop de tabs door: Winkels, Agenda,
   Berichten, Acties, Beloningen, Deals, Taken.
4. Een accountmanager logt in met zijn AM-e-mail; een winkel met zijn eigen
   account — iedereen ziet automatisch alleen wat hij mag zien (dat dwingt de
   database af, niet de browser).

## Zelf opnieuw bouwen (voor de ontwikkelaar)

```bash
cd tapparfum/portaal/frontend
cp .env.example .env        # vul VITE_SUPABASE_URL en VITE_SUPABASE_KEY in
npm install
npm run build               # -> dist/ ; zip de INHOUD van dist en sleep naar Netlify
```

## Als er iets niet werkt

| Zie je… | Dan… |
|---|---|
| "Onjuiste inloggegevens" | Check e-mail/wachtwoord in Supabase → Authentication → Users. |
| Lege lijsten bij Berichten/Agenda/Deals | Stap 1 (database-script) nog niet gedraaid. |
| Pagina laadt niet na verversen op een subpagina | De `_redirects`-file ontbreekt — gebruik de meegeleverde zip. |
| Documenten-upload werkt niet | Controleer of het script ook het Storage-deel heeft gedraaid (bucket `tp-docs` onder Storage). |
