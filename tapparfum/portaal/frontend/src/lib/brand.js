// Huisstijl (v71 thema): kantoor kan de merkkleuren en de logotekst bijstellen.
// De config staat netwerkbreed in central 'brand' en wordt bij het laden van de
// app toegepast als CSS-variabelen op :root. Puur cosmetisch — geen data, geen
// beveiliging; RLS bewaakt dat alleen kantoor central mag schrijven.
//
// Contrast-bewaking: --coral-d wordt op tekst gebruikt, dus die maken we zo
// nodig automatisch donkerder tot hij ≥4.5:1 haalt op wit — nooit onleesbaar.

export const BRAND_STD = { coral: '#EE644D', corald: '#D9543C', green: '#3B6D11', amber: '#BA7517' }

function lum(h) {
  h = String(h).replace('#', '')
  if (h.length === 3) h = h.split('').map(c => c + c).join('')
  const f = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4) }
  return 0.2126 * f(parseInt(h.slice(0, 2), 16)) + 0.7152 * f(parseInt(h.slice(2, 4), 16)) + 0.0722 * f(parseInt(h.slice(4, 6), 16))
}
export function contrast(a, b) {
  const x = lum(a), y = lum(b), hi = Math.max(x, y), lo = Math.min(x, y)
  return (hi + 0.05) / (lo + 0.05)
}
function donker(h, f) {
  h = String(h).replace('#', '')
  if (h.length === 3) h = h.split('').map(c => c + c).join('')
  const d = i => Math.max(0, Math.round(parseInt(h.slice(i, i + 2), 16) * f)).toString(16).padStart(2, '0')
  return '#' + d(0) + d(2) + d(4)
}
// Maak een kleur net zo lang donkerder tot hij leesbaar is op wit (≥4.6:1).
export function aaDonker(h) {
  let f = 0.95, c = h
  while (contrast('#ffffff', c) < 4.6 && f > 0.2) { f -= 0.05; c = donker(h, f) }
  return c
}
const HEX = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i

let _stijl = null
// Past de merkkleuren toe (of ruimt ze op als de config leeg is).
export function applyBrand(cfg) {
  cfg = cfg || {}
  let css = ''
  const set = (k, varn, safe) => {
    const v = cfg[k]
    if (v && HEX.test(v)) css += `${varn}:${safe ? (contrast('#ffffff', v) >= 4.5 ? v : aaDonker(v)) : v};`
  }
  set('coral', '--coral', false)
  set('corald', '--coral-d', true)
  set('green', '--green', true)
  set('amber', '--amber', true)
  try {
    if (typeof document === 'undefined') return
    if (!_stijl) { _stijl = document.createElement('style'); _stijl.setAttribute('data-tp-brand', '1'); document.head.appendChild(_stijl) }
    _stijl.textContent = css ? `:root{${css}}` : ''
  } catch (e) { /* stijl toepassen kan mislukken in een rare omgeving; niet fataal */ }
}
