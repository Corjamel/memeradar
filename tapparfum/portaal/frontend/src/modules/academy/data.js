// Academy-lesinhoud — de invulling van de 28 lessen uit COURSES
// (beloningen/logic.js). v71 toonde alleen lestitels met een vinkje; hier
// krijgt elke les échte stof: korte uitleg, kernpunten en een praktijktip.
// Structuur: LESINHOUD[cursusKey][lesIndex] = { d: uitleg, p: [kernpunten], tip }
// De volgorde MOET gelijk lopen met COURSES[x][4] — daar leunt t.academy op.

export const LESINHOUD = {
  onboarding: [
    { d: 'TapParfum is hervulbaar parfum van hoge kwaliteit voor een eerlijke prijs. Klanten kopen één mooi flesje en komen daarna terug om te tappen — in jouw winkel.',
      p: ['Meer dan 400 tappunten, en het netwerk groeit', 'Geuren geïnspireerd op bekende parfumstijlen, zonder de designer-prijs', 'Jij verdient aan élke refill — de klant komt steeds terug'],
      tip: 'Loop vandaag langs je Tapbar en tap één geur op een teststrip. Ruik wat je verkoopt.' },
    { d: 'Het refill-concept is de kern: flesje leeg? Niet weggooien maar hervullen. Duurzaam voor de klant, terugkerende omzet voor jou.',
      p: ['Refill is gemiddeld voordeliger dan een nieuw flesje — dat voelt als winst voor de klant', 'Elke refill is een terugkeermoment: dé kans om iets nieuws te laten ruiken', 'Duurzaamheid is een verkoopargument: minder verpakking, minder verspilling'],
      tip: 'Zeg bij elke verkoop: "Als hij leeg is, neem je het flesje gewoon mee terug — dan vullen we hem hier."' },
    { d: 'Onze missie: luxe geur bereikbaar maken voor iedereen, zonder concessies aan kwaliteit. De visie: een landelijk netwerk van winkels waar geur een beleving is.',
      p: ['Eerlijke prijs, eerlijk verhaal — nooit doen alsof het "namaak" is, het is een eigen kwaliteitsproduct', 'De winkel is het podium: ruiken, proberen, ontdekken', 'Samen groeien: jouw omzetgroei is ons succes'],
      tip: 'Vertel het verhaal in je eigen woorden aan een collega en vraag of het overtuigt.' },
    { d: 'Ken je assortiment: parfums in meerdere formaten, plus de lijnen eromheen — bodymist, homegeuren (kaars, homespray, reed diffuser) en giftsets.',
      p: ['Parfum: het hart van het concept, hervulbaar in de winkel', 'Bodymist & body: lichte instap, ideaal als tweede product', 'Home-lijn: kaarsen, homespray en diffusers — geur voor thuis', 'Giftsets: hét antwoord op "ik zoek een cadeautje"'],
      tip: 'Leg één giftset naast de kassa. Cadeauvraag? Wijzen en uitleggen — klaar.' },
    { d: 'Het Geurnotenboek is jouw naslagwerk: per geur de top-, hart- en basisnoten en de stijl waar hij bij past. Zo adviseer je gericht in plaats van te gokken.',
      p: ['Zoek op geurstijl die de klant al draagt en noem 2-3 passende nummers', 'Gebruik de noten om het verschil uit te leggen tussen twee twijfelgeuren', 'Verkoop op geurbeleving, niet op nummer'],
      tip: 'Kies drie bestsellers en leer hun topnoten uit je hoofd — dat klinkt direct professioneel.' },
    { d: 'Je eerste week: winkel op orde, systeem door, eerste verkopen draaien. Werk samen met je accountmanager de opstartchecklist af.',
      p: ['Dag 1-2: Tapbar compleet, testers fris, prijzen zichtbaar', 'Dag 3-4: oefen de demo op collega\'s tot hij vloeiend is', 'Dag 5-7: spreek actief klanten aan en registreer elke verkoop in het portaal'],
      tip: 'Plan nu je eerste weekdoel in het portaal — een doel dat je nét moet najagen.' }
  ],
  geurnoten: [
    { d: 'Een geur opent met topnoten (eerste kwartier), ontwikkelt zich in hartnoten (uren) en blijft hangen op basisnoten (rest van de dag).',
      p: ['Top = de eerste indruk: citrus, fris, sprankelend', 'Hart = het karakter: bloemen, kruiden, fruit', 'Basis = de herinnering: hout, musk, vanille, amber'],
      tip: 'Laat de klant een strip na 10 minuten nóg eens ruiken: "Ruik je dat hij warmer wordt? Dat is het hart."' },
    { d: 'Geurfamilies helpen je snel de smaak van de klant te vinden: fris, bloemig, oriëntaals/warm, houtig — en alles ertussenin.',
      p: ['Fris: citrus, aquatisch — dagelijks en zomers', 'Bloemig: roos, jasmijn — klassiek en vrouwelijk', 'Oriëntaals: vanille, amber, specerijen — avond en winter', 'Houtig: ceder, vetiver — warm en verzorgd'],
      tip: 'Vraag: "Wat draag je nu het liefst?" — het antwoord verraadt bijna altijd de familie.' },
    { d: 'Klanten onthouden geen notenlijstjes. Vat elke geur samen in één zin die beeld oproept.',
      p: ['Formule: [gevoel] + [moment] — "Warm en verslavend, perfect voor de avond"', 'Gebruik vergelijkingen die de klant kent', 'Eén zin, dan de strip laten ruiken — de neus doet de rest'],
      tip: 'Schrijf voor je drie favoriete geuren zo\'n zin en gebruik ze deze week letterlijk.' },
    { d: 'Op de meeste klantvragen bestaat een kort, eerlijk antwoord. Ken ze, dan sta je nooit met je mond vol tanden.',
      p: ['"Is dit namaak?" — Nee, eigen geuren geïnspireerd op bekende stijlen, gemaakt van kwaliteitsoliën', '"Blijft hij zitten?" — Ja, en zo verleng je hem: op de huid na het douchen, niet wrijven', '"Waarom zo voordelig?" — Je betaalt geen marketing en designer-flacon, wel de geur zelf'],
      tip: 'Oefen deze drie antwoorden hardop tot ze ontspannen klinken in plaats van verdedigend.' }
  ],
  funnel: [
    { d: 'De TapParfum-funnel is vijf stappen: geur kiezen → formaat kiezen → upsell → refill uitleggen → afronden. Elke stap heeft één doel.',
      p: ['1. Geur: beleving eerst, prijs later', '2. Formaat: standaard het middelgrote adviseren', '3. Upsell: bodymist, tweede geur of giftset', '4. Refill: de terugkomreden', '5. Afronden: bevestigen en uitzwaaien met een reden om terug te komen'],
      tip: 'Loop de vijf stappen vandaag één keer bewust langs bij een echte klant.' },
    { d: 'Het Geurnotenboek maakt van "even snuffelen" een gerichte keuze: zoek op wat de klant al draagt of op de beleving die die zoekt.',
      p: ['Vraag naar de huidige geur en zoek de stijl op', 'Geef maximaal 2-3 opties — meer keuze verlamt', 'Laat ruiken op strips, pas daarna op de huid'],
      tip: 'Nooit meer dan drie strips tegelijk: de neus is na drie geuren vol.' },
    { d: 'De upsell is een service, geen trucje: je maakt het plaatje af. En refill is je sterkste verkoopargument — vertel het bij élke verkoop.',
      p: ['Koppel logisch: parfum → bodymist in dezelfde geur ("layering: houdt langer")', 'Cadeau? Giftset erbij noemen', 'Refill-zin: "Flesje leeg? Meenemen — hervullen is voordeliger dan nieuw"'],
      tip: 'Tel deze week hoe vaak je de refill-zin zegt. Doel: 100% van de verkopen.' },
    { d: 'Afronden is de klant helpen beslissen — vriendelijk, zonder druk. Twijfel is normaal; jouw taak is de keuze klein maken.',
      p: ['Twijfel tussen twee? "Welke blijft in je hoofd hangen?" — die wordt het', 'Vat samen: geur, formaat, prijs — en knik', 'Geef een terugkomreden mee: refill, nieuwe geuren, de volgende actie'],
      tip: 'Sluit af met de naam van de geur ("Veel plezier met TN056!") — dat maakt de koop persoonlijk.' },
    { d: 'Oefencases: droogzwemmen met echte situaties, zodat het in de winkel vanzelf gaat.',
      p: ['Case 1: klant zoekt een cadeau van ±€20 — welke twee opties bied je?', 'Case 2: klant vindt alles "te sterk" — welke familie pak je?', 'Case 3: klant wil "iets als zijn oude designer-geur" — hoe gebruik je het Geurnotenboek?'],
      tip: 'Speel één case na met een collega als klant. Wissel om en geef elkaar één verbeterpunt.' }
  ],
  aanspreken: [
    { d: 'De eerste indruk bepaalt of een klant blijft hangen. Open, actief en zonder verkoopdruk — je nodigt uit om te ruiken, meer niet.',
      p: ['Sta niet achter maar naast de Tapbar', 'Oogcontact + glimlach binnen de eerste seconden', 'Openingszin zonder ja/nee-fuik: "Lekker luchtje? Deze mag je proberen"'],
      tip: 'Vervang "Kan ik je helpen?" een week lang door een uitnodiging om te ruiken en tel het verschil.' },
    { d: 'Je pitch van 20 seconden: wat is TapParfum, waarom is het slim, wat moet de klant nu doen. Kort, eigen woorden, met een strip in de hand.',
      p: ['Wat: kwaliteitsparfum, hervulbaar, eerlijke prijs', 'Waarom: dezelfde beleving als duur parfum, en je flesje vul je hier gewoon bij', 'Nu: "Ruik deze eens — dit is onze populairste"'],
      tip: 'Neem je pitch op met je telefoon en luister terug. Alles wat langer dan 20 seconden duurt, schrap je.' },
    { d: 'Bezwaren zijn interesse in vermomming. Luister, erken, geef één sterk antwoord — en vraag daarna iets terug.',
      p: ['"Te goedkoop om goed te zijn" → "Snap ik. Ruik zelf, dan proef je de kwaliteit"', '"Ik heb al parfum" → "Perfect — voor welke momenten? Dan heb je hiernaast iets voor elke dag"', '"Geen tijd" → "Eén strip, kost je drie seconden" (en meegeven!)'],
      tip: 'Noteer het bezwaar dat jij het vaakst hoort en formuleer één vast antwoord dat bij je past.' },
    { d: 'Live oefenen: kennis wordt pas kunde op de winkelvloer. Oefen bewust, één vaardigheid per keer.',
      p: ['Dag 1: alleen de openingszin oefenen, bij iedereen', 'Dag 2: pitch + strip meegeven', 'Dag 3: bewust één bezwaar ombuigen'],
      tip: 'Spreek vandaag drie klanten aan die je normaal voorbij zou laten lopen.' },
    { d: 'Afsluiten & motivatie: verkopen is een ritme. Vier kleine successen en hou je energie vast — de klant voelt jouw plezier.',
      p: ['Elke "nee" brengt je dichter bij een "ja" — het is een getallenspel', 'Vier elke eerste verkoop van de dag even bewust', 'Deel wat werkt met je team (en in de Community)'],
      tip: 'Zet een dagdoel van drie aansprekingen extra. Klein genoeg om te halen, groot genoeg om te groeien.' }
  ],
  geurnotenboek: [
    { d: 'De tablet met de geurquiz laat de klant zélf ontdekken — jij hoeft alleen te begeleiden. Ideaal bij drukte of verlegen klanten.',
      p: ['Zet de tablet zichtbaar en werkend bij de Tapbar', 'Nodig uit: "Doe de quiz, dan vindt hij jouw geur"', 'Blijf in de buurt voor het moment dat de match verschijnt'],
      tip: 'Check elke ochtend even of de tablet aanstaat en de quiz opent. Een zwart scherm verkoopt niets.' },
    { d: 'Zoeken op geurbeleving draait de verkoop om: niet "welk nummer wil je" maar "hoe wil je ruiken" — fris, warm, zoet, kruidig.',
      p: ['Vraag naar het moment: werk, avond, sport, date', 'Vertaal het antwoord naar een familie en pak 2-3 matches', 'Laat de klant kiezen met de neus, niet met het prijskaartje'],
      tip: 'Vraag vandaag eens niet "waar zoek je naar?" maar "wanneer wil je hem dragen?" — en merk het verschil.' },
    { d: 'Eén klant, meerdere matches: wie op beleving zoekt, vindt vaak twee of drie geuren leuk. Dat is geen probleem — dat is je kans.',
      p: ['Benoem het verschil per moment: "Deze voor overdag, die voor de avond"', 'Twee geuren = twee refill-klanten in één persoon', 'Twijfel? De bodymist-versie van de tweede geur is een lichte instap'],
      tip: 'Stel bij elke tweede match de vraag: "Waarom kiezen? Voor dit bedrag kun je ze allebei hebben."' }
  ],
  tapbar: [
    { d: 'De Tapbar is je podium. Compleet, schoon en uitnodigend — zodat een klant er niet omheen kan.',
      p: ['Alle geuren gevuld, etiketten leesbaar, prijzen duidelijk', 'Teststrips en het Geurnotenboek binnen handbereik', 'Sta er niet achter als een kassa — sta ernaast als een gastheer'],
      tip: 'Maak een foto van je Tapbar en vergelijk met de foto uit het brandbook. Wat valt op?' },
    { d: 'De demo: tap, ruik, ontdek. Drie stappen, dertig seconden — en de klant heeft de beleving te pakken.',
      p: ['Tap de geur op een strip, wapper even, geef hem aan', 'Vertel er één zin bij (je pitch!)', 'Laat de klant reageren voordat jij verder praat'],
      tip: 'Geef de strip mee: "Neem hem mee, thuis ruikt hij nog." Zo loopt je merk de winkel uit.' },
    { d: 'Beleving en sfeer verkopen meer dan argumenten. Licht, muziek, geur in de lucht — de omgeving doet het halve werk.',
      p: ['Sproei op rustige momenten een topgeur in de buurt van de Tapbar', 'Werk met de seizoenen: fris in de zomer, warm in december', 'Combineer met de home-lijn: een brandende kaars verkoopt zichzelf'],
      tip: 'Zet in het weekend een geurkaars aan bij de kassa en tel hoe vaak iemand ernaar vraagt.' },
    { d: 'Hygiëne en onderhoud: een plakkerige tap of lege tester breekt de beleving direct af.',
      p: ['Dagelijks: doekje over de taps, strips aanvullen', 'Wekelijks: voorraad checken en bijbestellen vóór iets leeg is', 'Direct: lekkage of defect melden bij je accountmanager'],
      tip: 'Koppel het aan een vast moment: elke ochtend bij het openen twee minuten Tapbar-check.' },
    { d: 'Veelgemaakte fouten — en dus snel te winnen punten. Herken ze bij jezelf, verbeter er één per week.',
      p: ['Te veel praten, te weinig laten ruiken', 'De refill niet noemen (daar zit je terugkerende omzet!)', 'Verkoop niet registreren — dan mist het portaal je groei én je beloningen', 'De Tapbar als meubel behandelen in plaats van als podium'],
      tip: 'Kies de fout die jou het meest raakt en hang er deze week een geeltje over bij de kassa.' }
  ]
}
