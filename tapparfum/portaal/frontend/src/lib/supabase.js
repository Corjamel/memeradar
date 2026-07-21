// De ENIGE plek die de Supabase-client maakt. Alle modules importeren 'sb' hier.
// Test-vriendelijk: als er een mock op window staat (Playwright), gebruik die.
import { createClient } from '@supabase/supabase-js'

function build() {
  if (typeof window !== 'undefined' && window.__TP_SUPABASE_MOCK) {
    return window.__TP_SUPABASE_MOCK
  }
  const url = import.meta.env.VITE_SUPABASE_URL
  const key = import.meta.env.VITE_SUPABASE_KEY
  if (!url || !key) {
    console.warn('[supabase] VITE_SUPABASE_URL / _KEY ontbreekt — zet ze in .env')
  }
  return createClient(url, key, {
    auth: { persistSession: true, autoRefreshToken: true }
  })
}

export const sb = build()
