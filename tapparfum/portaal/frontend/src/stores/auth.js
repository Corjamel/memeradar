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
      await this._bepaalRol(data.user)
      return true
    },

    async signOut() {
      try { await sb.auth.signOut() } catch (e) {}
      this.user = null; this.role = null; this.amId = null
    }
  }
})
