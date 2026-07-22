# PARITY.md — volledige v71 → portaal vergelijking (bouwplan)

> Resultaat van een 3-agent-inventarisatie van `TapParfum_Portal_v71_cloud.html`
> (4367 regels), gecontroleerd op veldnaam-niveau. **Dit is de bron van waarheid
> voor wat er nog gebouwd moet worden.** Regelnummers verwijzen naar v71.
> Werkwijze: per onderdeel bouwen → testen → committen (zie ARCHITECTURE.md §5).

## Bouwvolgorde (prioriteit 1 eerst)

| # | Onderdeel | Prio | Status |
|---|-----------|------|--------|
| 1 | Kassa (t.verkopen + flesMaten-prijzen + brug naar flesLog) | 1 | ✅ klaar |
| 2 | Calculator (break-even + jaardoel → t.be / t.goal) | 1 | ✅ klaar |
| 3 | Opstartchecklist/setup (t.setup, 6 fases, 19 acties) | 1 | ✅ klaar (SETUPFORM-formulierkoppeling volgt bij #17) |
| 4 | Basispunten/bonuspunten (t.bp/t.bonus + claims) | 1 | ✅ klaar (bezoek-gating van claims volgt bij #11) |
| 5 | Beloningen-engine (REWARDS + eisen + uitkering + vangnet) | 1 | ✅ klaar (Academy-les-UI volgt bij #24; engine leest t.academy al) |
| 6 | Producten + prodBesteld (lanceringen, fases, adoptie) | 1 | ✅ klaar (productfoto-upload volgt bij #28 merk & assets) |
| 7 | Bestellingen-registratie (t.bestellingen + CSV + ritme) | 1 | ✅ klaar (zelfde importpoort als straks de B2B-API) |
| 8 | Retour/probleem mét bewijsfoto + antwoord-flow | 1 | ✅ klaar (foto privé in tp-docs, migratie 011) |
| 9 | Bestellen-scherm partner (pakketten + shopUrl) | 1 | ✅ klaar (pakketInhoud-bewerken door kantoor kan later) |
| 10 | AM-Vandaag (7-bronnen-werklijst) | 1 | ✅ klaar (werkdag/GPS-stempels volgen bij #19) |
| 11 | Logboek/bezoeken (t.logboek, types, afspraken, 90d-ritme) | 1 | ✅ klaar (afspraken-popup bij openen winkel kan later) |
| 12 | Beheer-uitbreiding: tabs, winkels blokkeren, AVG, back-up, modules aan/uit, audit-log, rechten-matrix kantoor-gebruikers | 1 | ✅ klaar (matrix filtert het menu, zoals v71; data-beveiliging = RLS) |
| 13 | Instellingen (flesMaten, margeFactor, shopUrl, dagType-keuze in kassa) | 1 | ✅ klaar |
| 14 | statusKey/levels/margeFactor/groei (rekenhart) | 1 | ✅ klaar (cockpit-groepering op status volgt bij #15/#22) |
| 15 | Partner-dashboard-fasering (onboarding→break-even→jaardoel) + nudges | 1 | ✅ klaar — **alle 16 prio-1-onderdelen af** |
| 16 | Actie-detail (deelname, feedback, punten, materialen) | 1 | ✅ klaar (bestelDeadline-veld kan later) |
| 17 | Formulieren (7 stuks, t.forms) | 2 | ontbreekt |
| 18 | Mail (compose + .eml-import) | 2 | ontbreekt |
| 19 | Ritten/werkdag (GPS-momentopnames) | 2 | ontbreekt |
| 20 | Vieringen + milestones (checkMilestones) | 2 | ontbreekt |
| 21 | Geurbibliotheek + refill-bestellen | 2 | ontbreekt |
| 22 | Kantoor-analyse/activiteit/team (kanalyse, kactFeed, kteam) | 2 | deels |
| 23 | Globale zoekfunctie | 2 | ontbreekt |
| 24 | Academy (6 cursussen, 28 lessen, t.academy) | 2 | ✅ klaar (gekoppeld aan de beloningen-engine) |
| 25 | Sales Game (klassementen, podium) | 2/3 | ontbreekt |
| 26 | Heractiveren (t.react) | 2 | ontbreekt |
| 27 | Community | 3 | ontbreekt |
| 28 | Welkom/rondleiding, SPOTLIGHT, merk & assets, teksten-editor, layout-regie | 3 | ontbreekt |

## Kritieke datacompatibiliteit (veldnamen — NOOIT wijzigen)

Op het tappunt-record (`tappunten.data` JSONB):
- `flesLog[{at,n,ti,src?}]` — `ti` = index in `SALE_TYPES` (std/excl × bottle/refill × 30/50/100, vaste volgorde); `src:'kassa'` markeert kassaregels
- `verkopen{ 'YYYY-MM-DD': { '15ml': n, … } }` — maatlabels als sleutel; prijzen leven los in config `flesMaten`
- `jaaromzet` (inkoop), `vorigJaar`, `doel`, `klanten`, `dagType`, `statusManual`, `liveDate`
- `be{inv,rev,perWk,days,bottles}` + `beDone`, `beDoneAt`
- `goal{doel,klanten,flWeek,flJaar,flDag,refills}`
- `bp{key:bool}` / `bpClaim` / `bonus` / `bonusClaim` — puntenchecklists (BASIS 16 items = 70 pt, BONUS_MANUAL 8 items = 35 pt)
- `setup{done:{'si-ai':bool}, skipped}` — 6 fases, 19 acties; formulier-gekoppeld via SETUPFORM
- `academy{cursusKey:{lesIndex:bool}}` — 6 cursussen, 28 lessen
- `beloond{rewardKey:datumISO}` — eenmalige uitkering
- `vieringen[{type:'level'|'doel'|'be'|'beloning',…,at}]`
- `signalen[{at,cat,text,done,door,foto?,antwoord?{at,text,door},nieuwVoorP?,wensDatum?,bezoekStatus?,bezoekDatum?}]` — één berichtlijn voor partnerberichten/bezoekflow/kantoor-opdrachten/mijlpalen
- `logboek[{id,at,type:'bezoek'|'telefoon'|'mail'|'notitie',txt,nextDate,nextDone,gps?,aank?,duurMin?,dir?,msgId?,subject?,body?}]`
- `afspraken[{id,at,txt,done,doneAt,doneBy}]`, `laatsteBezoek`, `bezoekGepland`, `fu{d7,d30,d60,d90}`
- `bestellingen[{id,at,ref,totaal,omschrijving,bron}]` — dedupe op `ref`
- `actieDeelname{aid:{done,at,by,res{werkte,tekst,at,by},punten}}`, `actiesGezienP[]`
- `prodBesteld{pid:{done,at,by}}`, `prodGezienP[]`
- `forms{formId:{veldKey:waarde}}` — 7 formulieren, exacte veldkeys in v71 r.700-736
- `react[{date,actie,opvolg,done}]`, `traject`, `trajectSinds`, `trajectDoor`, `welkomOk`

Centrale namespaces (central-tabel): `acties`, `producten`, `pakketInhoud`, `flesMaten`
(`[{m:'15ml',p:12.5},…]`), `margeFactor`, `shopUrl`, `modules{game,kassa,producten}`,
`layout`, `regels{drempels,weging,actDagen,rewards}`, `brand`, `teksten`, `salesgame
{actief,titel,prijs,waarde,eind,minPunten,minBasis,regels}`.
**Bewust NIET netwerk-leesbaar** (in het portaal eigen tabellen met RLS): berichten,
winkelvragen (voorheen signalen), gebruikers/rechten, beheerlog.

## Kernformules (exact overnemen)

- **Prijstabel** `OMZETPF` (r.672): std.bottle `[12.40,16.53,26.86]`, std.refill `[10.33,14.46,24.79]`, excl.bottle `[16.53,20.66,35.12]`, excl.refill `[14.46,18.60,33.06]`; `SIZEIDX={'30':0,'50':1,'100':2}`; pakketten `PKG` inv: 3950/4702,5/5332,5/6692,5/8370/9595.
- **Break-even**: `be = ceil(inv / omzetPerFles)`; `weeks = ceil(be/perWk)`; `days = weeks*7`; behaald bij `flessenVerkocht>=bottles` OF `omzetVerkocht>=inv` (nooit door tijdsverloop). Punten op tijd: ≤75% van plandagen → 8, ≤100% → 5.
- **Jaardoel**: `revKlant = bottleprijs + refills*refillprijs`; `klanten = ceil(doel/revKlant)`; `flTot = klanten*(1+refills)`; `flWeek = round(flTot/52*10)/10`. Default refills = 8.
- **Niveaus** (op `winkelOmzet = jaaromzet × margeFactor`): D 0 · C 3000 · B 10000 · A 20000 · A+ 50000 (5% korting 3 mnd) · A++ 100000 (10%).
- **Groei**: `((jaaromzet/maandenVerstreken) − (vorigJaar/12)) / (vorigJaar/12)`; punten ≥150%→10 · ≥100%→8 · ≥75%→6 · ≥50%→4 · ≥25%→2.
- **statusKey-volgorde**: statusManual → setup-incompleet='nieuw' → be-niet-klaar='nieuw' → omzet 0 ('stagneert' als vorigJaar>0, anders 'groeit') → groei<0='stagneert' → A+/A++='top' → 'groeit'.
- **totaalScore** = basisScore(≤70) + bonusHandmatig(≤35) + bonusAuto(groei + jaardoel 5 + be-op-tijd 8/5) + actiepunten. Officieel-drempel: 60 basispunten.
- **Game-score** = groei% + acties×5 + min(20, 20% van totaalScore); nieuwkomers (geen vorigJaar) eigen klassement op omzet.
- **Rewards** (eisen + academy als zwakste schakel): vials=basis70+onboarding · home=€5000+groei50+tapbar · kaarsen=€10000+groei50+funnel · bodymist=€15000+groei50+aanspreken · promodag=totaal105+alle-cursussen. `groei50` auto-OK als vorigJaar<5000. Vangnet: bij elke login alle winkels nalopen.
- **Bronhiërarchie winkelomzet**: flessenteller > kassa > schatting (inkoop×factor) — vervangen, nooit optellen.
- **Drempels**: bezoek 90 dgn · bestelling 60 dgn · kassa-actief 14 dgn · FU-cadans d7/d30/d60/d90.

## Detailrapporten

De volledige agent-rapporten (met alle regelnummers en UI-gedrag) staan in de
sessie-log en zijn per onderdeel opnieuw op te vragen; dit document bevat de
bouwkritische kern. Bij twijfel: v71 zelf raadplegen op de genoemde regels —
v71 ís de specificatie (bewaren tot deze tabel leeg is).
