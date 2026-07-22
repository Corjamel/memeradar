<script setup>
// Verkoop & omzet bij één winkel — het hart van de oude app, 1-op-1
// datacompatibel met v71: t.jaaromzet (inkoop bij TapParfum), t.doel en
// t.flesLog met regels {at:'YYYY-MM-DD', n:aantal, ti:type}. Beide apps lezen
// en schrijven dezelfde JSON, dus de cijfers blijven overal gelijk.
import { computed, reactive, ref } from 'vue'
import { useTappunten } from '../../tappunten/store.js'
import { eur0 } from '../../../lib/format.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const emit = defineEmits(['bijgewerkt'])
const st = useTappunten()
const vandaag = new Date().toISOString().slice(0, 10)

const fout = ref('')
const melding = ref('')
const bezig = ref(false)
const wis = ref(null)          // twee-staps verwijderen: eerste klik = 'Zeker?'
const omzet = reactive({ jaaromzet: props.tappunt.jaaromzet || '', doel: props.tappunt.doel || '' })
const reg = reactive({ datum: vandaag, aantal: 1 })

const log = computed(() => props.tappunt.flesLog || [])
function vanafN(vanaf) { return log.value.filter(e => e.at >= vanaf).reduce((s, e) => s + (+e.n || 0), 0) }
const flesVandaag = computed(() => log.value.filter(e => e.at === vandaag).reduce((s, e) => s + (+e.n || 0), 0))
const flesWeek = computed(() => vanafN(new Date(Date.now() - 6 * 864e5).toISOString().slice(0, 10)))
const flesJaar = computed(() => vanafN(new Date().getFullYear() + '-01-01'))
const laatste = computed(() => [...log.value].sort((a, b) => (a.at < b.at ? 1 : -1)).slice(0, 5))

async function bewaar(t2, ok) {
  bezig.value = true; fout.value = ''; melding.value = ''
  try { await st.bewaar(t2); emit('bijgewerkt', t2); melding.value = ok }
  catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function omzetOpslaan() {
  if (bezig.value) return
  const t2 = { ...props.tappunt, jaaromzet: Number(omzet.jaaromzet) || 0, doel: Number(omzet.doel) || 0 }
  await bewaar(t2, '✓ Omzet & doel bijgewerkt')
}

async function registreer() {
  if (bezig.value) return
  const n = Math.max(parseInt(reg.aantal) || 0, 1)
  const entry = { at: reg.datum || vandaag, n, ti: 1 }
  const t2 = { ...props.tappunt, flesLog: [...log.value, entry].sort((a, b) => (a.at < b.at ? -1 : 1)) }
  await bewaar(t2, `✓ ${n} fles${n === 1 ? '' : 'sen'} geregistreerd`)
  reg.aantal = 1; reg.datum = vandaag
}

async function verwijder(e) {
  if (bezig.value) return
  if (wis.value !== e) { wis.value = e; return }   // bevestiging: tweede klik voert uit
  wis.value = null
  const t2 = { ...props.tappunt, flesLog: log.value.filter(x => x !== e) }
  await bewaar(t2, 'Regel verwijderd')
}
</script>

<template>
  <section class="blok">
    <h2>🧾 Verkoop & omzet</h2>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Jaaromzet + doel (drijft niveaus en beloningen) -->
    <div class="rij vorm">
      <label>Jaaromzet dit jaar (inkoop)
        <input v-model="omzet.jaaromzet" type="number" min="0" placeholder="0" data-test="omzet-jaaromzet" />
      </label>
      <label>Jaardoel
        <input v-model="omzet.doel" type="number" min="0" placeholder="0" data-test="omzet-doel" />
      </label>
      <button class="knop" type="button" :disabled="bezig" data-test="omzet-opslaan" @click="omzetOpslaan">Opslaan</button>
    </div>

    <!-- Flessenteller -->
    <div class="teller">
      <div class="tegels">
        <div class="tegel"><b data-test="fles-vandaag">{{ flesVandaag }}</b><span>vandaag</span></div>
        <div class="tegel"><b data-test="fles-week">{{ flesWeek }}</b><span>laatste 7 dagen</span></div>
        <div class="tegel"><b data-test="fles-jaar">{{ flesJaar }}</b><span>dit jaar</span></div>
      </div>
      <div class="rij vorm">
        <label>Datum<input v-model="reg.datum" type="date" data-test="fles-datum" /></label>
        <label>Aantal flessen<input v-model="reg.aantal" type="number" min="1" data-test="fles-aantal" /></label>
        <button class="knop" type="button" :disabled="bezig" data-test="fles-registreer" @click="registreer">+ Registreer</button>
      </div>
      <div v-if="laatste.length" class="loglijst">
        <div v-for="(e, i) in laatste" :key="e.at + '-' + i" class="logrij" data-test="fles-regel">
          <span>{{ e.at }}</span><b>{{ e.n }} fles{{ e.n === 1 ? '' : 'sen' }}</b>
          <button class="weg" :class="{ zeker: wis === e }" type="button" data-test="fles-verwijder"
                  aria-label="Verkoopregel verwijderen" @click="verwijder(e)">{{ wis === e ? 'Zeker?' : '✕' }}</button>
        </div>
      </div>
    </div>
    <p v-if="melding" class="ok" role="status">{{ melding }}</p>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-top:14px}
h2{margin:0 0 12px;font-size:16px}
.rij{display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:140px}
input{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
input:focus{border-color:var(--coral)}
.knop{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer}
.knop:disabled{opacity:.6}
.teller{margin-top:14px;border-top:1px solid var(--line);padding-top:14px}
.tegels{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.tegel{flex:1;min-width:110px;background:#faf7f2;border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:flex;flex-direction:column;gap:2px}
.tegel b{font-size:20px;color:var(--coral)}
.tegel span{font-size:11.5px;color:var(--grey);font-weight:700}
.loglijst{margin-top:12px;display:flex;flex-direction:column;gap:4px}
.logrij{display:flex;align-items:center;gap:12px;font-size:13px;padding:6px 0;border-bottom:1px solid var(--line)}
.logrij:last-child{border-bottom:0}
.logrij b{flex:1}
.weg{background:none;border:0;color:var(--grey);cursor:pointer;font-size:13px}
.weg:hover{color:#b3261e}
.weg.zeker{color:#b3261e;font-weight:800}
.fout{color:#b3261e;font-size:13px}
.ok{color:#2c5a12;font-size:13px;margin:8px 0 0}
</style>
