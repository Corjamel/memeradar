// Kennisbank & proces — naslag uit v71 (r.626, 637, 682-690), als structurele
// data (geen v-html): elk blok heeft een titel + regels (paragraaf of lijst).

export const KENNIS = [
  { t: 'Visie & missie', lead: '"Ruiken met je neus, niet je portemonnee."', p: ['Door het refill-model groeit de omzet cumulatief met het aantal vaste klanten dat een tappunt opbouwt: wie zijn favoriete geur vindt, blijft terugkomen. Het doel is dus zoveel mogelijk klanten genereren én vasthouden — daarom houd je per tappunt het klantenaantal én de omzet bij.'] },
  { t: "USP's — verkoopargumenten", li: ['Betaalbare luxe — hoge kwaliteit, eerlijke prijs.', 'Duurzaam — hervullen i.p.v. weggooien.', '400+ tappunten — bewezen, groeiend concept.', 'Keuzevrijheid — dames (LA), heren (LE), niche/unisex (TN/TF).', 'Klantbinding — spaaracties zoals "6 refills → 7e gratis".'] },
  { t: 'Klanten genereren (groei)', li: ['Gratis leeg flesje weggeven · gratis refill bij 3 nieuwe klanten.', 'Seizoensacties (lente / zomer / feestdagen / Black Friday).', 'Social media 2–3× per week met een duidelijke call-to-action.', 'Laat klanten hun favoriete geur vinden (testers / parfumquiz) — dat is dé conversie naar vaste klant.'] },
  { t: 'Vaste klanten maken (vasthouden)', li: ['Spaaractie: 6 refills → de 7e gratis.', 'Favoriete geur per klant vastleggen.', 'Welkomstmail (10% op 1e hervulling) + maandelijkse update-mail.'] },
  { t: 'Heractiveren & belonen', li: ['Stagneert: bel- of mailronde, nieuwe actie inzetten, voorraad/presentatie checken.', 'Top: belonen en opschalen — meer geuren, Exclusive, of een extra module (Niventi / Candle / Home).'] },
  { t: 'Fundament / start-stappenplan', li: ['Werk met min. 2 personen: één installeert de labelprinter, de ander vult de tapflessen.', 'Tapflessen vullen: 1 volle fles van 250 ml in een tapfles van 350 ml. Op nummer presenteren.', 'Testers / dopkleuren: LA (dames) zilver, LE (heren) zwart, T (niche) goud. Dun laagje tegen diefstal.', 'Tablet klaar; trainingsdag aanvragen.'], note: 'Materialen: Dropbox · B2B: retail-brands.nl' },
  { t: 'Voorwaarden promodag', li: ['1e promodag gratis bij start met min. 160 geuren (anders € 500 / 4 uur).', 'Assortiment fris, testers vrij van oxidatie, stickers correct en zichtbaar.', 'Poster met datum prominent; vials voldoende gevuld; stand bij de ingang.'] }
]

// Het verkooppad (SALE_STEPS r.626) en de aftersales-cadans (AFTERSALES r.637).
export const SALE_STEPS = [
  'Eerste contact & informatie (geen prijzen)',
  'Verkoopgesprek — toon het terugverdienverhaal met de calculator',
  'Voorwaarden & akkoord',
  'Order geplaatst'
]

export const AFTERSALES = [
  ['Dag 7', 'Belcheck'],
  ['Dag 30', 'Omzetreview'],
  ['Dag 60', 'Bijsturen'],
  ['Dag 90', 'Kwartaal + upsell']
]
