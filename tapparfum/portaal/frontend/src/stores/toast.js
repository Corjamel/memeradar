// Toast-store (Pinia): de vluchtige feedback-melding uit v71 (toast()).
//
// Eén gedeelde wachtrij zodat elke actie — een opgeslagen wijziging, een
// verstuurde opdracht, een fout — op dezelfde manier een korte bevestiging
// toont, rechtsonder in beeld. Puur UI: de toast draagt nooit beveiliging en
// bewaart niets; hij verdwijnt vanzelf.
import { defineStore } from 'pinia'

let _teller = 0

export const useToast = defineStore('toast', {
  state: () => ({
    items: []   // [{ id, txt, type, uit }]  type: 'ok' | 'fout' | 'info'
  }),
  actions: {
    // Toon een melding. `type` stuurt alleen de kleur; `ms` de levensduur.
    toon(txt, type = 'ok', ms = 3200) {
      if (!txt) return
      const id = ++_teller
      this.items.push({ id, txt: String(txt), type, uit: false })
      // Auto-sluiten: eerst uitfaden (voor de CSS-transitie), dan weghalen.
      setTimeout(() => this.sluit(id), Math.max(1200, ms))
      return id
    },
    ok(txt, ms) { return this.toon(txt, 'ok', ms) },
    fout(txt, ms) { return this.toon(txt, 'fout', ms || 4200) },
    info(txt, ms) { return this.toon(txt, 'info', ms) },
    sluit(id) {
      const it = this.items.find(x => x.id === id)
      if (!it) return
      it.uit = true
      setTimeout(() => { this.items = this.items.filter(x => x.id !== id) }, 220)
    }
  }
})
