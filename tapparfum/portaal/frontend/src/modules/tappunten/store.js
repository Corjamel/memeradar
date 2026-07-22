import { defineStore } from 'pinia'
import { haalTappunten, bewaarTappunt, zetBlokkade } from './api.js'

export const useTappunten = defineStore('tappunten', {
  state: () => ({ items: [], laden: false, fout: '' }),
  getters: {
    byCode: (s) => (code) =>
      s.items.find(t => (t.snelstart || '').toLowerCase() === String(code || '').toLowerCase())
  },
  actions: {
    async laad() {
      this.laden = true; this.fout = ''
      try { this.items = await haalTappunten() }
      catch (e) { this.fout = 'Kon de winkels niet laden: ' + e.message }
      this.laden = false
    },
    async bewaar(t) {
      await bewaarTappunt(t)
      const i = this.items.findIndex(x => x.snelstart === t.snelstart)
      if (i >= 0) this.items[i] = { ...t }
    },
    async blokkade(code, aan) {
      await zetBlokkade(code, aan)
      const t = this.byCode(code); if (t) t.geblokkeerd = aan
    }
  }
})
