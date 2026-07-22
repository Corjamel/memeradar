// API-laag Producten — lanceringen met fase-tijdlijn (v71 r.2104-2165).
// Netwerkbreed in central (ns 'producten'): [{id,naam,desc,artnr,verwacht,
// fase:0-3,img,at,archived}]. Iedereen leest, alleen kantoor schrijft.
import { sb } from '../../lib/supabase.js'

export const PROD_FASES = ['💡 In ontwikkeling', '🏭 In productie', '📦 Bijna leverbaar', '✅ Leverbaar']

export async function haalProducten() {
  const { data, error } = await sb.from('central').select('ns,data').eq('ns', 'producten')
  if (error) throw new Error(error.message)
  const row = (data || [])[0]
  return Array.isArray(row && row.data) ? row.data : []
}

// Alleen kantoor (RLS central_staff_write).
export async function bewaarProducten(lijst) {
  const { error } = await sb.from('central').upsert({ ns: 'producten', data: lijst }, { onConflict: 'ns' })
  if (error) throw new Error(error.message)
}

export const actieveProducten = (lijst) => (lijst || []).filter(p => !p.archived)
export const prodLeverbaar = (p) => (+p.fase || 0) >= 3
