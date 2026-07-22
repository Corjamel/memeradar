// Auth-store (Pinia): de ingelogde gebruiker + zijn ROL.
//
// BELANGRIJK: deze rol stuurt alleen wat je in de UI ziet. Wat je daadwerkelijk
// mag lezen/schrijven dwingt Postgres af via Row Level Security — ook als iemand
// hier met DevTools 'role' zou veranderen, komt hij niet bij data die niet van
// hem is. De frontend is nooit de beveiliging.
//
// Rolbepaling (één canonieke set: 'kantoor' | 'am' | 'partner'):
//   - JWT app_metadata.role === 'staff'      -> 'kantoor'
//   - anders: staat de gebruiker in accountmanagers? -> 'am'
//   - anders                                  -> 'partner'
import { defineStore } from 'pinia'
import { sb } from '../lib/supabase.js'

export const useAuth = defineStore('auth', {
  state: () => ({
    user: null,
    role: null,        // 'kantoor' | 'am' | 'partner'
    amId: null,        // gezet als de gebruiker een accountmanager is
    ready: false,      // eerste sessie-check afgerond
    error: ''
  }),
  getters: {
    ingelogd: (s) => !!s.user,
    isKantoor: (s) => s.role === 'kantoor',
    isAm: (s) => s.role === 'am',
    isPartner: (s) => s.role === 'partner'
  },
  actions: {
    async _bepaalRol(user) {
      const meta = (user && user.app_metadata) || {}
      if (meta.role === 'staff') { this.role = 'kantoor'; this.amId = null; return }
      // AM? -> zoek koppeling (RLS geeft alleen de eigen rij terug)
      try {
        const { data } = await sb.from('accountmanagers')
          .select('id').eq('auth_user_id', user.id).limit(1)
        if (data && data.length) { this.role = 'am'; this.amId = data[0].id; return }
      } catch (e) { /* val terug op partner */ }
      this.role = 'partner'; this.amId = null
    },

    async init() {
      try {
        const { data } = await sb.auth.getSession()
        const user = data && data.session && data.session.user
        if (user) { this.user = user; await this._bepaalRol(user) }
      } catch (e) { /* geen sessie */ }
      this.ready = true
    },

    async signIn(email, password) {
      this.error = ''
      const { data, error } = await sb.auth.signInWithPassword({ email, password })
      if (error || !data || !data.user) {
        this.error = 'Onjuiste inloggegevens.'
        return false
      }
      this.user = data.user
      // Eerste-keer-flow met e-mailbevestiging: als er nog een snelstartcode
      // klaarligt voor dit adres, koppel de winkel alsnog (claim_tappunt is
      // server-side beveiligd: werkt alleen op een nog-ongekoppelde winkel).
      try {
        const k = 'tp_pending_claim::' + String(email).toLowerCase()
        const pend = localStorage.getItem(k)
        if (pend) {
          const r = await sb.rpc('claim_tappunt', { p_snelstart: pend, p_user: email })
          if (!r || !r.error) localStorage.removeItem(k)
        }
      } catch (e) { /* koppeling kan later alsnog */ }
      await this._bepaalRol(data.user)
      return true
    },

    // Eerste keer (winkel): account aanmaken + winkel koppelen via snelstartcode.
    // De server (RPC claim_tappunt, migratie 001) bewaakt dat de code klopt en
    // de winkel nog vrij is — de browser wordt ook hier niet vertrouwd.
    async signUpMetCode({ email, wachtwoord, code }) {
      this.error = ''
      const { data, error } = await sb.auth.signUp({ email, password: wachtwoord })
      if (error || !data || !data.user) {
        this.error = 'Account aanmaken mislukt' + (error && error.message ? ': ' + error.message : '.')
        return 'fout'
      }
      if (data.session && data.user) {
        this.user = data.user
        const r = await sb.rpc('claim_tappunt', { p_snelstart: code, p_user: email })
        if (r && r.error) this.error = 'Winkel koppelen mislukt: ' + r.error.message
        await this._bepaalRol(data.user)
        return 'ingelogd'
      }
      // E-mailbevestiging staat aan: onthoud de code; na de eerste login
      // koppelt de winkel automatisch (zie signIn).
      try { localStorage.setItem('tp_pending_claim::' + String(email).toLowerCase(), code) } catch (e) {}
      return 'bevestig'
    },

    async wachtwoordVergeten(email) {
      try { await sb.auth.resetPasswordForEmail(email) } catch (e) { /* stil: geen adres-lek */ }
      return true
    },

    async signOut() {
      try { await sb.auth.signOut() } catch (e) {}
      this.user = null; this.role = null; this.amId = null
    }
  }
})
