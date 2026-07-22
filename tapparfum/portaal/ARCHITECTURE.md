# TapParfum Portaal — Architectuur

> Dit document is de **bron van waarheid** voor hoe het nieuwe portaal in elkaar zit.
> Het is geschreven voor twee lezers: de eigenaar (niet-technisch) én de ontwikkelaar
> die het onderhoudt. Lees dit eerst voordat je iets bouwt of wijzigt.

---

## 1. Waarom dit portaal bestaat

Een B2B-portaal voor TapParfum met **±500 winkels (tappunten)** en drie rollen:

| Rol | Wie | Ziet |
|-----|-----|------|
| **kantoor** (staff) | TapParfum-kantoor | het hele netwerk |
| **accountmanager** (am) | AM's | alleen hun eigen winkels |
| **partner** | winkeleigenaren | alleen hun eigen winkel |

Doel op termijn: uitgroeien tot een **volwaardig CRM** (contacten, deals, pijplijn,
taken, e-mailtracking) — daarom is de architectuur bewust modulair.

## 2. De harde eisen (waar elke keuze aan getoetst is)

1. **Valt niet uit de lucht.** Er hangen 500 winkels aan; downtime is onacceptabel.
2. **Altijd doorontwikkelbaar.** Nieuwe functies erbij zonder de rest te breken.
3. **Onderhoudbaar door één dev.** Een mainstream stack die elke moderne dev oppakt.
4. **Server-afgedwongen veiligheid.** Geen data mag lekken; de browser wordt nooit vertrouwd.
5. **Betaalbaar draaien.** Geen dure servers die 24/7 beheer vragen.

## 3. De stack (en waarom)

**Frontend:** Vue 3 (Composition API) + Vite + Pinia (state) + Vue Router.
**Backend:** **Supabase** (beheerd) — PostgreSQL + Auth + Row Level Security + Storage + Edge Functions.
**Hosting:** statische frontend (Netlify/Vercel) + Supabase als beheerde backend.

### Waarom Supabase en niet een eigen Laravel-server?

Een eerder voorstel was Laravel op een eigen server. Technisch prima, maar het
faalt op **eis 1 en 5**: een eigen server moet je draaien, updaten, back-uppen en
's nachts fixen. Voor dit bedrijf (geen vaste infra-beheerder) is dat precies wat
"uit de lucht valt".

Supabase levert dezelfde bouwstenen (echte Postgres, echte auth, rechten in de
database) **als beheerde dienst**: zij houden de server draaiend, patchen en
back-uppen. Wij schrijven alleen ons schema en onze regels.

| Eis | Supabase-aanpak |
|-----|-----------------|
| Valt niet uit de lucht | Beheerde infra + automatische back-ups; geen eigen server |
| Veiligheid server-afgedwongen | **Postgres Row Level Security** in de database-kern — *fail-closed* |
| Doorontwikkelbaar | Modulaire frontend + één migratie per feature |
| Onderhoudbaar | Vue + Supabase = zeer gangbare, goed te bemensen stack |
| Betaalbaar | Geen VPS; schaalt tot ver voorbij 500 winkels |

### Beveiligingsprincipe (belangrijkste regel van dit project)

> **De frontend wordt NOOIT vertrouwd. Elke toegangsregel wordt door de database
> afgedwongen via Row Level Security (RLS), niet door de Vue-code.**

De Vue-code bepaalt alleen wat je *ziet* (UX). Wat je *mag* (data lezen/schrijven)
bepaalt Postgres, op basis van je ingelogde account (JWT). Ook met DevTools open
komt niemand bij data die niet van hem is. Dit is *fail-closed*: vergeet je een
filter in de frontend, dan lekt er nog niets, want de database weigert het.

## 4. Repo-structuur

```
tapparfum/portaal/
├── ARCHITECTURE.md          ← dit document
├── README.md                ← snelstart voor de dev
├── backend/
│   └── migrations/          ← de database, als genummerde SQL-bestanden
│       ├── 001_core.sql        (tappunten, central, accountmanagers, RLS)
│       ├── 002_am_isolatie.sql (AM ziet alleen eigen winkels)
│       ├── 003_storage.sql     (privé documenten per winkel)
│       └── 004_kolom_guard.sql (beschermde velden: alleen staff)
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.js          ← app-start, router, pinia
        ├── App.vue          ← schil (nav + router-view)
        ├── lib/
        │   └── supabase.js  ← de enige plek die de Supabase-client maakt
        ├── stores/
        │   └── auth.js       ← ingelogde gebruiker + rol + rechten (Pinia)
        ├── router/
        │   └── index.js      ← routes + guards (UX-niveau)
        └── modules/          ← ELKE FUNCTIE IS EEN MODULE
            ├── auth/         (login, wachtwoord vergeten)
            ├── tappunten/    (winkels: lijst, detail, bewerken)
            ├── berichten/
            ├── agenda/
            └── ...
```

**Kernidee: één functie = één module.** Een module bevat zijn eigen views,
componenten, store en API-laag. Modules kennen elkaar niet direct — ze praten via
de gedeelde stores en de Supabase-laag. Zo kun je een module toevoegen, wijzigen of
weggooien zonder de rest te raken (eis 2).

## 5. Hoe voeg je een nieuwe module toe? (het recept)

1. Maak `src/modules/<naam>/` met: `views/`, `components/`, `api.js`, (optioneel) `store.js`.
2. Nieuwe data nodig? Voeg een **migratie** toe in `backend/migrations/` (nooit een
   bestaand bestand wijzigen — altijd een nieuw genummerd bestand), **inclusief de
   RLS-regels** die bepalen wie het mag zien/schrijven.
3. Registreer de route(s) in `src/router/index.js` met de juiste rol-`meta`.
4. Schrijf een test (Playwright, met gemockte Supabase) die bewijst dat de rol-regels
   kloppen — dit is de acceptatievoorwaarde, niet een extraatje.

> **Gouden regel:** een module is pas "af" als er een RLS-regel én een test is die
> bewijst dat rol X wél en rol Y níet bij de data kan.

## 6. Data & migraties

- De database wordt beschreven door **genummerde SQL-bestanden** in `backend/migrations/`.
  Ze zijn **idempotent** (veilig opnieuw te draaien) en **gevalideerd op PostgreSQL 16**.
- Draaien: plak elk bestand op volgorde in de Supabase **SQL Editor** → Run.
  (Later automatiseerbaar met de Supabase CLI.)
- **Nooit** een oud migratiebestand aanpassen — voeg een nieuw genummerd bestand toe.
  Zo is de databasegeschiedenis altijd reproduceerbaar.

## 7. Draaien & deployen

**Lokaal ontwikkelen:**
```bash
cd tapparfum/portaal/frontend
npm install
npm run dev        # start Vite op http://localhost:5173
```
Zet de Supabase-URL + publishable key in `frontend/.env` (zie `.env.example`).
De publishable key is **publiek-veilig** (de beveiliging zit in RLS); de
`service_role`-key komt **nooit** in de frontend.

**Deployen:**
```bash
npm run build      # bouwt naar frontend/dist/
```
`dist/` is statisch → sleep naar Netlify of koppel de repo. Nul server.

## 8. Voor de onderhoudende ontwikkelaar (onboarding in 10 minuten)

1. Lees dit document + `README.md`.
2. `npm install && npm run dev` in `frontend/`.
3. Bekijk `src/modules/tappunten/` als voorbeeldmodule — elke andere module volgt
   hetzelfde patroon.
4. Beveiliging zit in `backend/migrations/` (RLS), **niet** in de Vue-code. Als je
   twijfelt of iets veilig is: controleer de RLS-policy, niet de frontend.
5. Nieuwe feature = nieuwe module + nieuwe migratie + test (zie §5).

## 9. Migratie van de huidige app (geen big-bang)

De huidige werkende app (`TapParfum_Portal_v71_cloud.html`) blijft **live** terwijl
dit portaal ernaast groeit ("strangler"-aanpak):

1. Bouw een module in het nieuwe portaal tot parity.
2. Test tegen dezelfde Supabase-data.
3. Schakel dat onderdeel over; de rest blijft voorlopig op de oude app.
4. Herhaal tot alles over is. Er is nooit een moment waarop niets werkt.

De data leeft al in Supabase — er is dus **geen risicovolle data-migratie**; beide
apps lezen dezelfde tabellen.

## 10. Roadmap naar volwaardig CRM

| Fase | Modules | Status |
|------|---------|--------|
| 0 | Fundering: auth + rollen + rechten (server-afgedwongen) | ✅ klaar |
| 1 | Tappunten (winkels): lijst, detail, bewerken, blokkeren | ✅ klaar |
| 2 | Berichten (kantoor↔AM), winkelvragen (partner→AM/kantoor), agenda (plannen + accepteren/afwijzen), documenten (privé Storage) | ✅ klaar |
| 3 | Dashboards per rol (kantoor-cockpit, AM-overzicht, partner-start), acties (central), beloningsladder (central, kantoor beheert) | ✅ klaar |
| 4 | CRM-uitbreiding: contactpersonen per winkel, deals-pijplijn (AM/kantoor), taken met kantoor-toewijzing | ✅ klaar |
| 5 | Koppelingen: WooCommerce (bestellingen), Microsoft 365 (mailtracking) — wacht op keys/app-registratie van de eigenaar | ⏳ volgende |

Elke fase = losse modules op dezelfde fundering. Niets hoeft in één keer af.
