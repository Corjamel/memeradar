// Kassa-config: flesmaten + prijzen, netwerkbreed in central (ns 'flesMaten').
// Zelfde structuur als v71: [{m:'15ml',p:12.5}, ...] — maatlabel is de sleutel
// in t.verkopen, de prijs leeft alleen hier (historische omzet beweegt dus mee
// met een prijswijziging; bewuste v71-keuze).
import { sb } from '../../lib/supabase.js'

export const STANDAARD_MATEN = [
  { m: '15ml', p: 12.5 },
  { m: '30ml', p: 19.5 },
  { m: '50ml', p: 29.5 },
  { m: '100ml', p: 44.5 }
]

export async function haalFlesMaten() {
  const { data, error } = await sb.from('central').select('ns,data').eq('ns', 'flesMaten')
  if (error) throw new Error(error.message)
  const row = (data || [])[0]
  const arr = Array.isArray(row && row.data) ? row.data : []
  return arr.length ? arr : STANDAARD_MATEN
}

// Alleen kantoor (RLS central_staff_write).
export async function bewaarFlesMaten(arr) {
  const { error } = await sb.from('central').upsert({ ns: 'flesMaten', data: arr }, { onConflict: 'ns' })
  if (error) throw new Error(error.message)
}

// Modules aan/uit (central ns 'modules', v71-semantiek: !==false betekent aan).
export async function haalModules() {
  const { data, error } = await sb.from('central').select('ns,data').eq('ns', 'modules')
  if (error) throw new Error(error.message)
  const row = (data || [])[0]
  return (row && row.data) || {}
}

// Kassatotalen over t.verkopen = { 'YYYY-MM-DD': { '15ml': n, ... } }
export function vkTotaal(counts, maten) {
  const prijs = Object.fromEntries((maten || []).map(x => [x.m, +x.p || 0]))
  let tot = 0
  for (const [m, n] of Object.entries(counts || {})) tot += (+n || 0) * (prijs[m] || 0)
  return tot
}

export function vkPeriode(t, vanaf, maten) {
  let tot = 0, stuks = 0
  for (const [dag, cs] of Object.entries(t.verkopen || {})) {
    if (dag >= vanaf) {
      tot += vkTotaal(cs, maten)
      for (const n of Object.values(cs || {})) stuks += (+n || 0)
    }
  }
  return { tot, stuks }
}
