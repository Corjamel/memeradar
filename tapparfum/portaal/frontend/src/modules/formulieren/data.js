// Formulieren — EXACT uit v71 (r.700-736): 7 akkoord-/checklistformulieren
// met yes/no-secties, keuzevragen (opts) en vrije velden. Opgeslagen onder
// t.forms = { formId: { veldKey: waarde } }. SETUPFORM koppelt checklist-
// stappen aan een formulier (sleutel 'fase-actie').
export const FORMS=[
 {id:"vw_tappunt",naam:"Voorw. Tappunt (80)",titel:"Voorwaarden officieel TapParfum Tappunt",desc:"Basis-tappunt vanaf 80 geuren. Loop elke voorwaarde samen met de ondernemer door en bevestig akkoord. Een 'Nee' bespreek en los je op vóór de start.",secties:[
   {t:"Gegevens",velden:[["date","vtdatum","Datum"],["text","vtbedrijf","Bedrijfsnaam / KvK-nummer"]]},
   {t:"Voorwaarden — besproken & akkoord",yesno:[["vt1","Het tappunt is ingeschreven bij de KvK en heeft een fysiek verkooppunt."],["vt2","Het tappunt voert minimaal 80 verschillende geuren in het assortiment."],["vt3","Het tappunt volgt de verkoop- en promotierichtlijnen én de adviesverkoopprijzen van TapParfum Nederland."],["vt4","Producten worden uitsluitend verkocht op basis van parfumstijl en geurnoten; andere marketingvormen zijn niet toegestaan."],["vt5","Er wordt geen korting gegeven, tenzij via een door TapParfum gecommuniceerde actie (eigen promoties zoals een gratis leeg flesje of tester zijn wél toegestaan)."],["vt6","Het tappunt zorgt zelf voor de juiste opslag van de parfums (bescherming tegen lucht, UV-licht en temperatuurschommelingen)."],["vt7","Het tappunt biedt geen andere op dezelfde wijze getapte parfums aan."],["vt8","Er wordt uitsluitend gewerkt met het officiële geurnotenbook (geen interne lijsten)."],["vt9","Eerste promotie-orders worden vooraf betaald; nabestellingen binnen 7 dagen na factuurdatum."],["vt10","Geopende parfumproducten kunnen niet worden geretourneerd."],["vt11","Beëindiging, verhuizing of overdracht gebeurt altijd in overleg met TapParfum Nederland."],["vt12","De ondernemer accepteert deze voorwaarden en de algemene voorwaarden van RB bv."]]},
   {t:"Opmerkingen",velden:[["textarea","vtopm","Opmerkingen / afspraken"]]}]},
 {id:"vw_tapbar",naam:"Voorw. Tapbar (160)",titel:"Voorwaarden officieel TapParfum Tapbar",desc:"Tapbar vanaf 160 geuren — geldt bovenop de tappunt-voorwaarden. Komt in aanmerking voor alleenrecht, met vaste begeleiding van een accountmanager.",secties:[
   {t:"Gegevens",velden:[["date","vbdatum","Datum"],["text","vbbedrijf","Bedrijfsnaam / KvK-nummer"]]},
   {t:"Extra voorwaarden Tapbar — besproken & akkoord",yesno:[["vb1","De Tapbar voert minimaal 160 verschillende geuren in het assortiment."],["vb2","De Tapbar voldoet aan de jaarlijks vastgestelde minimale afname-/omzetnorm (zie TapParfum-dashboard; vraag je accountmanager om een omzetanalyse)."],["vb3","De Tapbar behoudt het alleenrecht zolang de richtlijnen en de minimale regio-omzet worden nageleefd."],["vb4","De Tapbar krijgt ondersteuning van een vaste accountmanager en heeft recht op een meedraaidag."],["vb5","Promotie en verkoop verlopen uitsluitend via parfumstijl en geurnoten; andere promotie wordt als overtreding gezien."],["vb6","Bij het niet naleven van de richtlijnen kan de samenwerking na een schriftelijke waarschuwing worden beëindigd zonder recht op vergoeding."],["vb7","De basis tappunt-voorwaarden zijn eveneens doorgenomen en akkoord."],["vb8","De ondernemer accepteert de Tapbar-voorwaarden en de algemene voorwaarden van RB bv."]]},
   {t:"Opmerkingen",velden:[["textarea","vbopm","Opmerkingen / afspraken"]]}]},
 {id:"vw_winkel",naam:"Voorw. Winkel (400)",titel:"Voorwaarden officieel TapParfum Winkel",desc:"Volledige winkel vanaf 400 geuren incl. bijproducten. Alleenrecht bij minder dan 30.000 inwoners. Recht op accountmanager, begeleiding en meedraaidag.",secties:[
   {t:"Gegevens",velden:[["date","vwdatum","Datum"],["text","vwbedrijf","Bedrijfsnaam / KvK-nummer"]]},
   {t:"Voorwaarden — besproken & akkoord",yesno:[["vw1","De winkel voert minimaal 400 geuren plus de bijbehorende bijproducten (o.a. Moodz en bodymist)."],["vw2","De winkel hanteert de adviesverkoopprijzen en biedt TapParfum-producten nooit onder de adviesprijs aan."],["vw3","De winkel houdt zich aan alle richtlijnen van TapParfum Nederland."],["vw4","De winkel heeft alleenrecht bij minder dan 30.000 inwoners in dorp of stad, mits richtlijnen en regio-omzet worden nageleefd."],["vw5","De winkel voldoet aan de jaarlijks vastgestelde minimale afname (norm in het dashboard)."],["vw6","De winkel realiseert een minimale afname van €5.000 per maand om alleenrecht te behouden (12 maanden opbouwtijd)."],["vw7","De winkel plaatst maximaal 2 TP-spray displays bij collega-ondernemers in eigen dorp of wijk."],["vw8","Inkoopprijzen: reguliere geuren €19,50 ex btw, exclusieve geuren €24,50 ex btw (tenzij officiële prijswijziging)."],["vw9","Verkoop verloopt uitsluitend op geurnoten; elke andere promotie- of marketingvorm is niet toegestaan."],["vw10","Geopende artikelen kunnen niet retour; kwaliteit en oxidatie na openen vallen onder verantwoordelijkheid van de winkel."],["vw11","Nabestellingen worden binnen 7 dagen na factuurdatum betaald; promotie-eerste-orders 2 dagen vóór verzending (tenzij anders overlegd)."],["vw12","Er wordt uitsluitend gewerkt met het officiële geurnotenbook (geen interne lijsten)."],["vw13","Beëindiging wordt gemeld; de winkel wijst niet zelf een vervanger aan (alleen in overleg met TapParfum Nederland)."],["vw14","Bij TapParfum ingekochte producten worden niet elders verkocht dan afgesproken."],["vw15","De ondernemer accepteert deze winkelvoorwaarden en de algemene voorwaarden van RB bv."]]},
   {t:"Opmerkingen",velden:[["textarea","vwopm","Opmerkingen / afspraken"]]}]},
 {id:"voorraad",naam:"Voorraad checklist",titel:"Voorraad checklist",desc:"Bij heractivatie en vóór een (extra) promodag — check of voorraad en presentatie nog op orde zijn. Niet nodig bij een nieuwe start.",secties:[
   {t:"Gegevens",velden:[["date","vdatum","Datum van controle"],["text","vlocatie","Locatie"]]},
   {t:"1 · Vials en testers",yesno:[["v1","Zijn de vials (tapflessen) voldoende gevuld voor verkoop?"],["v2","Zijn alle testers aanwezig en in goede staat?"],["v3","Zijn de testers vrij van oxidatie en verkleuring?"],["v4","Zijn alle testers voorzien van de juiste stickers en dopkleur (LA zilver / LE zwart / T goud)?"]]},
   {t:"2 · Assortiment en presentatie",yesno:[["v5","Is het volledige geurassortiment beschikbaar en op nummer gepresenteerd?"],["v6","Is de actuele TapParfum-uitstraling in de winkel toegepast?"],["v7","Zijn er voldoende lege tapflessen / vervangingsflessen op voorraad?"]]},
   {t:"3 · Promotie en verpakking",yesno:[["v8","Zijn er voldoende verpakkingen en lege flesjes op voorraad?"],["v9","Zijn de promotiematerialen (folders, flyers, QR/poster) compleet en zichtbaar?"]]},
   {t:"4 · Systeem en administratie",yesno:[["v10","Is de tablet bijgewerkt en klaar voor gebruik?"],["v11","Zijn de voorraadgegevens bijgewerkt in HubSpot?"]]},
   {t:"Opmerkingen",velden:[["textarea","vopm","Opmerkingen / actiepunten"]]}]},
 {id:"promodag",naam:"Promodag-voorwaarden",titel:"Voorwaarden promodag klant",desc:"Vóór de demo-/promodag controleren. 1e promodag gratis bij start vanaf 160 geuren; extra promodag €500 per dagdeel (4 uur, incl. promotiepakket).",secties:[
   {t:"Gegevens",velden:[["date","pdatum","Datum promodag"],["text","plocatie","Locatie"]]},
   {t:"Controle vóór de promodag",yesno:[["p1","Zijn de tapflessen en testers in goede staat en vrij van oxidatie?"],["p2","Is de actuele TapParfum-uitstraling toegepast en zijn de testers met stickers goed zichtbaar?"],["p3","Is het promotiemateriaal vooraf goedgekeurd door de marketingafdeling?"],["p4","Staan poster/flyers met de datum van de promodag prominent in de winkel?"],["p5","Is de promodag aangekondigd via social media?"],["p6","Zijn de vials voldoende gevuld zodat klanten de hele dag bediend kunnen worden?"],["p7","Is er een promotionele actie afgesproken (bijv. een 30 ml flesje vullen voor €12,50)?"],["p8","Staat de stand/kraam op een strategische plek (bijv. bij de ingang)?"],["p9","Is de tablet bijgewerkt en klaar voor gebruik tijdens de promodag?"]]},
   {t:"Opmerkingen",velden:[["textarea","popm","Opmerkingen / afspraken"]]}]},
 {id:"demo",naam:"Demodag evaluatie",titel:"Demo Dag Evaluatieformulier",desc:"Direct na de demodag samen invullen.",secties:[
   {t:"Gegevens",velden:[["date","ddatum","Datum demo dag"],["text","dlocatie","Locatie"]]},
   {t:"1 · Voorbereiding",yesno:[["d1","Was het assortiment volledig en up-to-date?"],["d2","Was het promotiemateriaal op tijd aanwezig en zichtbaar?"],["d3","Was het winkelpersoneel voldoende voorbereid?"]]},
   {t:"2 · Uitvoering",opts:[["d4","Samenwerking tussen het TapParfum-team en het winkelpersoneel?",["Uitstekend","Goed","Voldoende","Slecht"]]],yesno:[["d5","Was de stand strategisch geplaatst?"],["d6","Was er voldoende interactie met klanten?"]]},
   {t:"3 · Resultaten",opts:[["d7","Klantrespons op het concept?",["Zeer positief","Positief","Neutraal","Negatief"]]],yesno:[["d8","Waren er directe verkopen tijdens de demodag?"],["d9","Zijn de USP's (betaalbare luxe, duurzaam, keuzevrijheid) goed overgebracht?"]]},
   {t:"4 · Evaluatie",velden:[["textarea","d10","Wat ging er goed?"],["textarea","d11","Wat kan beter / welke vervolgacties?"]]}]},
 {id:"actieplan",naam:"Omzet-actieplan",titel:"Omzet actieplan TapParfum",desc:"Jaardoel en kwartaalacties samen met het tappunt vastleggen. Gebruik promoties (gratis flesjes, refills) om klanten te belonen en aan te trekken.",secties:[
   {t:"Gegevens",velden:[["date","adatum","Datum"]]},
   {t:"Jaardoelen",velden:[["number","a_huidig","Huidige jaaromzet (€)"],["number","a_doel","Gewenste jaaromzet / jaardoel (€)"],["number","a_be","Break-evenpunt (€)"]]},
   {t:"Hoofdactie per kwartaal",velden:[["text","a_q1","Q1 (jan–mrt) — bijv. gratis flesje bij aankoop"],["text","a_q2","Q2 (apr–jun) — bijv. spaaractie 6 refills, 7e gratis"],["text","a_q3","Q3 (jul–sep) — bijv. zomeractie + breng-een-vriend"],["text","a_q4","Q4 (okt–dec) — bijv. feestdagen + Black Friday"]]},
   {t:"Bevestiging",yesno:[["a_ok","Is het actieplan en het jaardoel besproken en akkoord met het tappunt?"]]},
   {t:"Opmerkingen",velden:[["textarea","aopm","Opmerkingen"]]}]},
];

export const SETUPFORM={"0-3":"vw_tappunt","2-2":"promodag","4-0":"demo","5-0":"actieplan"};
// De drie voorwaarden-formulieren zijn onderling uitwisselbaar voor stap 0-3:
// een winkel kwalificeert via tappunt-, tapbar- of winkelvoorwaarden (v71 VW_IDS).
export const VW_IDS = ['vw_tappunt', 'vw_tapbar', 'vw_winkel']

// Ja/nee-sleutels (yn) en keuzevraag-sleutels (op) van een formulier — v71 formYN.
export function formYN(fid) {
  const f = FORMS.find(x => x.id === fid)
  const yn = [], op = []
  if (f) {
    f.secties.forEach(s => {
      (s.yesno || []).forEach(x => { yn.push(x[0]) })
      ;(s.opts || []).forEach(x => { op.push(x[0]) })
    })
  }
  return { yn, op }
}

// Is een formulier "af"? v71 formStatus (r.2597): actieplan apart; anders alle
// ja/nee + keuzevragen ingevuld, of (zonder zulke vragen) minstens 3 gevulde velden.
export function formStatus(t, fid) {
  const f = (t.forms && t.forms[fid]) || {}
  if (fid === 'actieplan') return !!(f.a_doel && f.a_doel !== '' && (f.a_ok === 'Ja' || f.a_ok === 'Nee'))
  const k = formYN(fid)
  if (k.yn.length || k.op.length) return k.yn.every(x => f[x] === 'Ja' || f[x] === 'Nee') && k.op.every(x => !!f[x])
  return Object.keys(f).filter(x => f[x] !== '' && f[x] != null && f[x] !== false).length >= 3
}
