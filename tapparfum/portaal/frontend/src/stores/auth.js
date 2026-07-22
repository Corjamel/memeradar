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
    rechten: null,     // kantoor: rechten-matrix uit central 'kantoorRechten' (null = alles)
    ready: false,      // eerste sessie-check afgerond
    error: ''
  }),
  getters: {
    ingelogd: (s) => !!s.user,
    isKantoor: (s) => s.role === 'kantoor',
    isAm: (s) => s.role === 'am',
    isPartner: (s) => s.role === 'partner',
    // Rechten-matrix (v71 ALLE_RECHTEN): rol 'beheer' heeft alles; een entry
    // met rol 'kantoor' krijgt alleen de aangevinkte onderdelen. Net als in
    // v71 filtert dit het MENU — de data-beveiliging blijft RLS (staff).
    magBeheer: (s) => s.role === 'kantoor' && (!s.rechten || s.rechten.rol === 'beheer'),
    magActiesBeheren: (s) => s.role === 'kantoor' && (!s.rechten || s.rechten.rol === 'beheer' || s.rechten.acties !== false),
    magProductenBeheren: (s) => s.role === 'kantoor' && (!s.rechten || s.rechten.rol === 'beheer' || s.rechten.producten !== false)
  },
  actions: {
    async _bepaalRol(user) {
      const meta = (user && user.app_metadata) || {}
      if (meta.role === 'staff') {
        this.role = 'kantoor'; this.amId = null
        // Rechten-matrix ophalen voor dit kantoor-account (geen entry = alles).
        try {
          const { data } = await sb.from('central').select('ns,data').eq('ns', 'kantoorRechten')
          const matrix = (data && data[0] && data[0].data) || {}
          this.rechten = matrix[String(user.email || '').toLowerCase()] || null
        } catch (e) { this.rechten = null }
        return
      }
      // AM? -> zoek koppeling (RLS geeft alleen de eigen rij terug)
      try {
        const { data } = await sb.from('accountmanagers')
          .select('id').eq('auth_user_id', user.id).limit(1)
        if (data && data.length) { this.role = 'am'; this.amId = data[0].id; return }
      } catch (e) { /* val terug op partner */ }
      // Nog niet gekoppeld: misschien is dit een uitgenodigde AM (kantoor heeft
      // zijn e-mail in Beheer gezet). De server koppelt alleen bij exacte
      // e-mailmatch op een nog-vrije rij (RPC tp_koppel_am, migratie 009).
      try {
        const r = await sb.rpc('tp_koppel_am')
        if (r && !r.error && r.data) { this.role = 'am'; this.amId = r.data; return }
      } catch (e) { /* geen AM-uitnodiging */ }
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

    // Eerste keer (accountmanager, uitgenodigd door kantoor): account aanmaken
    // zonder code — de koppeling loopt server-side op e-mailmatch (tp_koppel_am).
    async signUpAm({ email, wachtwoord }) {
      this.error = ''
      const { data, error } = await sb.auth.signUp({ email, password: wachtwoord })
      if (error || !data || !data.user) {
        this.error = 'Account aanmaken mislukt' + (error && error.message ? ': ' + error.message : '.')
        return 'fout'
      }
      if (data.session && data.user) {
        this.user = data.user
        await this._bepaalRol(data.user)   // koppelt op e-mail als er een uitnodiging is
        return 'ingelogd'
      }
      return 'bevestig'                    // e-mail bevestigen; koppeling volgt bij eerste login
    },

    async wachtwoordVergeten(email) {
      try { await sb.auth.resetPasswordForEmail(email) } catch (e) { /* stil: geen adres-lek */ }
      return true
    },

    async signOut() {
      try { await sb.auth.signOut() } catch (e) {}
      this.user = null; this.role = null; this.amId = null; this.rechten = null
    }
  }
})
