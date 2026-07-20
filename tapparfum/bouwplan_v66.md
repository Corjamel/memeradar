# TapParfum-portaal — Bouwplan (gebundeld uit 5 analyses)

## Kernoordeel

Dit portaal is grotendeels decor. De drie dingen die het als "af" verkoopt — rol-communicatie, de "AI-assistent" en de "API-koppeling" — bestaan niet echt: communicatie is één vrij-tekstveld dat zichzelf overschrijft, de AI is ~15 regexen met een robot-emoji, en "bestellen" is een knop die een externe website opent waarna je de order overtypt. Het énige stuk dat wél echt werkt — de cloud-sync — is meteen het gevaarlijkste: het pusht AM-PINs én de platte beheer-mastercode naar een tabel die elke ingelogde gebruiker mag lezen. Volgorde is daarmee dwingend: eerst het lek dichten, dan de nepfuncties eerlijk of echt maken, dan pas de echte backend bouwen — en niets van de order-kant kan starten zolang de gebruiker geen bestelplatform kiest.

---

## Alle bevindingen, gesorteerd op prioriteit

### NU (now)

| Area | Titel | Fix (kort) | Effort | Dependency |
|---|---|---|---|---|
| Security | central-tabel wereldleesbaar én bevat credentials | Sync nooit PINs/mastercode; splits central in staff-only vs publiek | M | supabase-auth |
| Security | Platte PINs + client-side rolgates over localStorage | Rol- en datatoegang volledig achter Supabase Auth + RLS | L | supabase-auth |
| Bestel | "Server bewaart de sleutel veilig" is vals — fetch zonder auth | B2B-calls achter Supabase Edge Function/proxy; misleidende toast weg | L | supabase-auth |
| Bestel | AM kan niet echt bestellen — enige actie is externe URL | Draft-order flow per tappunt; tot dan UI eerlijk labelen als redirect | L | externe-api |
| Bestel | Order-sync bestaat niet (alleen klantensync) | `syncBestellingenB2B()` → `importBestellingen(rows,'api')`, upsert op b2bId | M | externe-api |
| Bestel | Platformkeuze onbeslist — mapB2bKlant gokt het schema | Kies platform (Shopify B2B/Woo/Lightspeed/eigen) en map hun echte schema | S | externe-api |
| Comm | Bezoek-accept half — partner ziet geplande datum nergens | Banner "Volgend bezoek: DATUM" in partner-view + AM-afwijzen-met-reden | M | none |
| Comm | Geen thread — antwoorden overschrijven elkaar, verkeerde provenance | `antwoord:{}` → `antwoorden:[]`; render afzender uit `.door`; reageer-knop | M | none |
| AI | "Assistent" is broze regex-matcher, geen AI | Vervang tekstveld door zoekbaar commando-paneel op bestaande handlers | M | none |
| AI | Copy belooft "gewone taal" en "echte AI in Fase 1" | Hernoem naar "Snelacties"; schrap "gewone taal"/"echte AI"; toon klikbare commando's | S | none |
| Nav | "Cockpit" is geen cockpit maar de tappunten-lijst | Label → "Tappunten", icoon → map-pin; "Cockpit" reserveren voor kantoor | S | none |
| Nav | Dubbele kop op Cockpit (hero + vhead, gelijke subtitels) | Eén titeldrager; KPI-rij binnen eerste schermhoogte | S | none |

### NEXT

| Area | Titel | Fix (kort) | Effort | Dependency |
|---|---|---|---|---|
| Comm | Signalen op array-index geadresseerd + unshift → verkeerd-signaal-bug | Stabiel `id` per signaal; overal adresseren op id i.p.v. index | M | supabase-storage |
| Comm | Retour is puur vrije tekst — geen foto/structuur/status | Velden product/aantal/reden + foto naar storage (URL in signaal) + retourstatus | M | supabase-storage |
| Bestel | Materiaal-artikelnummers verzameld maar nooit verstuurd | Cart-prefill: `openBestelportaal(context)` stuurt artnr+aantal mee | M | externe-api |
| Bestel | Ordermodel te dun voor echte koppeling | Uitbreiden met extId/status/regels/tappuntB2bId; upsert op extId | M | externe-api |
| Nav | "Vandaag" opent als muur van gestapelde gekleurde banners | Statusstrip samenvoegen; game/producten onder "Nu"; max 2 accentkleuren boven de vouw | M | none |
| Nav | Accent-randkleuren zijn inflatie — niets valt op | Kleursemantiek vastleggen (rood=actie, amber=let op, groen=klaar, neutraal=info) | M | none |
| Nav | Labels <11px + filterteller #bbb op coral-d (~2.1:1) | Functionele labels ≥11-12px; `.fchip.on .fn` → rgba(255,255,255,.85) | S | none |
| AI | Assistent dupliceert knoppen die al bestaan | Command-palette (Ctrl-K) óf weghalen; geen tweede broze ingang | S | none |
| Security | RLS partner-update zonder kolombescherming; blokkeren niet server-afgedwongen | BEFORE UPDATE-trigger: am_id/snelstart/geblokkeerd/auth_user_id vastzetten | M | supabase-auth |
| Security | Partner-credentials (hash+salt+reset) liften mee naar cloud in `data` | Strip `t.auth` vóór push (veld-whitelist) óf migreer naar Supabase Auth | S | supabase-auth |

### LATER

| Area | Titel | Fix (kort) | Effort | Dependency |
|---|---|---|---|---|
| Comm | Documenten heen en weer bestaan niet | Documentenmodule met echte bestandsopslag (AM↔partner↔kantoor) | L | supabase-storage |
| Comm | AM/kantoor hebben geen nieuw/ongelezen-markering | `gezienDoorAM/K`-vlag; nav-teller toont ongelezen i.p.v. alle open | S | none |
| Bestel | Twee losse URL-velden (shopUrl vs b2bApi), api.url ongevalideerd | Eén config-object afgeleid van platform; https-only validatie | S | none |
| Nav | Kantoor-acties dubbel getoond (Cockpit-banner + Vandaag) | Eén thuis (Acties-scherm); Cockpit/Vandaag verwijzen door met identieke copy | S | none |
| Nav | Mobiele nav klapt om tot wrappende tab-brij | Hamburger/bottom-tab met alleen primaire "Werk"-items | M | none |
| AI | Echte Claude pas ná cloud, alleen Q&A | LLM alleen voor uitleg; mutaties blijven via deterministische handlers, sleutel op de server | L | externe-api |
| Security | Ghost Protocol: hostname-gate geeft rol-impersonatie | Ghost via build-flag uit productie-build strippen | S | none |
| Security | Publishable/anon-key in de bron | Laten staan; RLS-fixes borgen; service_role buiten client houden | S | none |

---

## Volgorde van bouwen

### BLOK A — Snelle wins nu (dependency: none)

Alles hieronder is pure client-side edit in dat ene HTML-bestand, nul backend, en verlaagt direct de verwarring en de support-last:

- **Maak de nepfuncties eerlijk (4a/4b).** Vervang het "AI"-tekstveld door een zoekbaar commando-paneel op de handlers die al bestaan; schrap "gewone taal" en "echte AI". Dit doodt de grootste frustratiebron (typen dat niet matcht) zonder één regel backend.
- **Fix de navigatie-identiteit (3a/3b).** Hernoem "Cockpit" → "Tappunten" met de map-pin; schrap de dubbele kop. Twee regels, en de AM weet eindelijk: Vandaag = wat moet ik nú, Tappunten = mijn portfolio.
- **Bouw de echte conversatie (1a/1b).** Zet `antwoord:{}` om naar `antwoorden:[]` met afzender, en render de bezoekdatum als banner in de partner-view. Let op: doe de overstap naar **stabiele id-adressering (1c) gelijktijdig met het aanzetten van multi-device**, anders krijg je de verkeerd-signaal-bug erbij.
- **Visuele opschoning (3c/3d/3f)** kan hier direct achteraan: kleursemantiek vastleggen, "Vandaag"-top comprimeren, labels leesbaar maken.

Waarom eerst: dit is het goedkoopste werk met het hoogste zichtbare rendement, en het maakt het product eerlijk voordat er iemand op afgaat.

### BLOK B — Op de cloud (dependency: supabase-auth / supabase-storage)

Dit kan niet veilig client-side in één HTML-bestand — het vereist server, RLS en echte bestandsopslag. **De security-fixes gaten de cloud-go-live**: multi-device aanzetten vóór 5a en 1c gedaan zijn, maakt het aantoonbaar slechter (lek + verkeerd-signaal-bug).

- **Auth-spoor:** stop credential-sync en splits central (5a) → PINs/rolgates naar Supabase Auth + RLS (5b) → B2B-sleutel achter Edge Function (2c) → partner-update kolom-whitelist (5c) → `t.auth` strippen vóór push (5d).
- **Storage-spoor:** stabiele signaal-id's voor multi-device (1c) → retourfoto's in storage (1d) → documentenmodule (1e).

Waarom hierop: elk van deze fixes leunt op een echte serverzijde die er nu niet is. De volgorde is niet vrijblijvend — het auth-spoor moet klaar zijn vóór je sync live zet.

### BLOK C — Externe integratie (dependency: externe-api)

**Wat er van de gebruiker nodig is: één besluit — welk bestelplatform (2d).** Shopify B2B, WooCommerce, Lightspeed of eigen backend. Dit is effort S maar blokkeert alle L-werk eronder: draft-order flow (2a), order-sync (2b), materiaal-cart-prefill (2e) en het uitgebreide ordermodel (2f) kunnen pas tegen een echt API-schema gebouwd worden. Zolang die keuze uitblijft, blijf je stubs en giswerk-mappings bouwen. De "echte AI" (4d) hoort ook hier: pas ná cloud, sleutel op de server, strikt voor vraag-en-antwoord.

**Actie:** vraag de gebruiker nu het platform te kiezen — dat is de goedkoopste beslissing met de grootste unblock.

---

## Security — wat nu dichten

Alleen de echte risico's, in volgorde van ernst:

1. **Actief credential-lek (5a).** `central` is `select ... using(true)` en bevat AM-PINs, kantoor-accounts + rechten én de platte beheer-mastercode. Elke ingelogde gebruiker doet `select * from central` en leest de mastercode → directe privilege-escalatie. Dit is geen theorie: de pushes gebeuren juist wanneer kantoor accounts beheert. **Stop credential-sync direct.**
2. **Geen echte grens in lokale modus (5b).** Alle PII en PINs staan plat in localStorage; rolgates zijn puur client-side. Via DevTools zet je `role='kantoor'` + volledige rechten en je bent binnen. Cosmetische beveiliging.
3. **B2B-fetch zonder auth (2c).** De `/klanten`-call gaat zonder Authorization rechtstreeks uit de browser; werkt alleen als het endpoint publiek-onbeveiligd is (= lek van het complete klantenbestand). De belofte "server bewaart de sleutel" is vals.
4. **Partner kan eigen rij vrij muteren (5c).** RLS-update zonder kolomrestrictie: partner kan zichzelf deblokkeren, `am_id` herschrijven, data overschrijven. Nu latent (cloudlogin partner nog niet bedraad), maar het schema-gat is er.
5. **Partner-hash+salt+reset-code in de cloud (5d).** Een live reset.code lezen = winkel-overname; enkelvoudige SHA-256 maakt brute-force van zwakke wachtwoorden haalbaar.

Géén prioriteit: de **anon-key in de bron (5f)** is by design publiek — verspil er geen tijd aan te "verbergen", borg in plaats daarvan de RLS. **Ghost (5e)** is laag (geen Supabase-sessie, dus geen cloud-toegang) maar hoort simpelweg via een build-flag uit de productie-build.

---

## De 3 dingen die het meeste verschil maken

1. **Dicht het credential-lek (5a + 5b).** Er staat nu een leesbare mastercode en alle PINs in een tabel die iedereen kan opvragen. Zolang dit open staat is al het andere cosmetica — dit is de enige bevinding die je vandaag níet mag laten liggen.
2. **Maak belofte en realiteit gelijk (4a/4b, 2c-toast, 2a-labeling).** De kloof tussen wat de UI belooft ("AI", "koppeling", "server bewaart de sleutel") en wat het doet, is de grootste bron van frustratie en support-vragen. Óf eerlijk labelen, óf echt bouwen — geen tussenweg.
3. **Forceer de twee besluiten die alles deblokkeren:** (a) de Supabase-backend écht inrichten met Auth + RLS, en (b) het bestelplatform kiezen. Zonder deze twee blijf je oneindig stubs bouwen — met deze twee valt vrijwel elke overige bevinding op zijn plek.
