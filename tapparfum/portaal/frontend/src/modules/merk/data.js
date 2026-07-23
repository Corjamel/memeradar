// Merk & Assets — inhoud 1-op-1 uit v71 (VIEWS.merk, r.3482-3487).
// De originele app toont hier een "merkwereld" (sfeer-/merkbeelden), de
// downloadbare merkmaterialen en de korte merkregels. Omdat de herbouw geen
// beeldassets meebundelt, tonen we de merkwereld als getinte tegels met een
// emoji-cue; de labels/subtitels en teksten zijn woordelijk gelijk aan v71.

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
