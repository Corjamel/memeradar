// Merk & Assets — inhoud 1-op-1 uit v71 (VIEWS.merk, r.3482-3487), aangevuld
// met écht TapParfum-materiaal (aangeleverd door kantoor). Bewust in twee
// lagen geordend: CONCEPT (video's die vertellen wáár TapParfum voor staat:
// hervullen, geurbeleving, de winkelervaring) en PRODUCT (kale productfoto's
// uit de sell-sheets). De merkwereld-tegels en materialen blijven v71.

// De merkvideo's staan in de Academy (videotheek, academy/data.js) — daar
// wordt geleerd; hier blijven de merkwereld, productfoto's en materialen.
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
