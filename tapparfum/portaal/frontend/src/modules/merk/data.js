// Merk & Assets — inhoud 1-op-1 uit v71 (VIEWS.merk, r.3482-3487), aangevuld
// met écht TapParfum-materiaal (aangeleverd door kantoor). Bewust in twee
// lagen geordend: CONCEPT (video's die vertellen wáár TapParfum voor staat:
// hervullen, geurbeleving, de winkelervaring) en PRODUCT (kale productfoto's
// uit de sell-sheets). De merkwereld-tegels en materialen blijven v71.

// HET CONCEPT — merkvideo's: laten de beleving zien, niet het artikel.
// src verwijst naar /assets/video/ (meegebundeld); preload=metadata houdt
// de pagina licht (alleen het eerste frame wordt opgehaald).
export const CONCEPT_VIDEOS = [
  { t: 'Het refill-concept', cat: 'Duurzaam', sub: 'Flesje leeg? Tappen, niet weggooien — de kern van TapParfum.', src: '/assets/video/refill.mp4' },
  { t: 'De geurbeleving', cat: 'Beleving', sub: 'Ruiken, ontdekken, verliefd worden op een geur.', src: '/assets/video/scent.mp4' },
  { t: '“Lekker luchtje, hè”', cat: 'Winkelvloer', sub: 'Zo voelt de Tapbar in de winkel — laagdrempelig en met een knipoog.', src: '/assets/video/lekker-luchtje.mp4' },
  { t: 'Nieuwe geuren', cat: 'Assortiment', sub: 'Zo kondigen we nieuwe geuren aan richting de klant.', src: '/assets/video/nieuwe-geuren.mp4' },
  { t: 'Social reel · 6', cat: 'Social', sub: 'Voorbeeld-reel voor je eigen kanalen.', src: '/assets/video/reel-6.mp4' },
  { t: 'Social reel · 7', cat: 'Social', sub: 'Voorbeeld-reel voor je eigen kanalen.', src: '/assets/video/reel-7.mp4' }
]

// DE PRODUCTEN — productfotografie uit de officiële sell-sheets (PDF's):
// gewoon het artikel laten zien, zonder verhaal eromheen.
export const PRODUCT_FOTOS = [
  { t: 'Bodymist', sub: '5 geuren · 100 ml', src: '/assets/bodymist.jpg' },
  { t: 'Giftset — de lijn', sub: 'Cadeausets in één beeld', src: '/assets/giftset-algemeen.jpg' },
  { t: 'Giftset 30 ml · 2 × 15 ml', sub: 'Twee geuren om te combineren', src: '/assets/giftset-30ml-2x15.jpg' },
  { t: 'Giftset 30 ml · 3 vials', sub: 'Proeverij: drie geuren in vials', src: '/assets/giftset-30ml-3vials.jpg' },
  { t: 'Giftset 50 ml · 2 vials', sub: 'De grote fles + twee vials', src: '/assets/giftset-50ml-2vials.jpg' }
]

// MERKWERELD — v71 r.3482: [afbeelding, label, categorie]. Beeld -> emoji + tint.
export const MERKWERELD = [
  { t: 'Het logo', cat: 'Merk', ic: '🌸', bg: 'var(--soft)' },
  { t: 'Hervulbaar', cat: 'Duurzaam', ic: '♻️', bg: 'var(--green-soft)' },
  { t: 'Lifestyle · fris', cat: 'Beleving', ic: '🍐', bg: 'var(--soft)' },
  { t: 'Samen ontdekken', cat: 'Beleving', ic: '💞', bg: '#F3EEF8' },
  { t: 'Sfeer', cat: 'Beleving', ic: '🕯️', bg: '#F3EEF8' },
  { t: 'Verpakking', cat: 'Retail', ic: '🛍️', bg: 'var(--sand)' },
  { t: 'Recyclen', cat: 'Duurzaam', ic: '🌱', bg: 'var(--green-soft)' },
  { t: '400+ tappunten', cat: 'Internationaal', ic: '🌍', bg: 'var(--mist)' }
]

// MERK_ASSETS — v71 r.3435: de downloadbare merkmaterialen.
export const MERK_ASSETS = [
  { t: 'Brandbook 2026', fmt: 'PDF · 23 pagina\'s', label: 'BRANDBOOK 2026', bg: 'var(--coral)', fg: '#fff' },
  { t: 'Logo & emblemen', fmt: 'SVG · PNG', label: 'TP — LOGO PACK', bg: 'var(--coral)', fg: '#fff' },
  { t: 'Productfotografie', fmt: 'ZIP · alle lijnen', label: 'PRODUCTFOTO’S', bg: 'var(--mist)', fg: '#21343f' },
  { t: 'Social templates', fmt: 'Canva · PNG', label: 'SOCIAL TEMPLATES', bg: '#DCD9E8', fg: '#3a2f5a' }
]

// Merkregels — kort (v71 r.3487), woordelijk overgenomen.
export const MERKREGELS =
  'Eén primaire kleur per ontwerp · vaste logo’s en lettertype (Gravesend Sans · Nunito Sans) · nooit onder de adviesprijs · altijd verkopen op parfumstijl en geurnoten.'
