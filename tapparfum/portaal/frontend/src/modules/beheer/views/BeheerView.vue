<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useTappunten } from '../../tappunten/store.js'
import { haalAms, voegAmToe, verwijderAm, zetWinkelAm } from '../api.js'

const st = useTappunten()
const ams = ref([])
const fout = ref('')
const bezig = ref(false)
const nieuw = reactive({ naam: '', email: '' })
const wis = ref(null)          // twee-staps verwijderen (AM weggooien is ingrijpend)

const AANTAL = computed(() => {
  const m = {}
  st.items.forEach(t => { if (t.am_id) m[t.am_id] = (m[t.am_id] || 0) + 1 })
  return m
})

async function laad() {
  fout.value = ''
  try {
    ams.value = await haalAms()
    if (!st.items.length) await st.laad()
  } catch (e) { fout.value = 'Kon beheer niet laden: ' + e.message }
}
onMounted(laad)

async function toevoegen() {
  if (bezig.value) return
  if (!nieuw.naam.trim() || !nieuw.email.trim()) { fout.value = 'Vul naam én e-mailadres in.'; return }
  bezig.value = true; fout.value = ''
  try {
    await voegAmToe(nieuw.naam.trim(), nieuw.email.trim())
    nieuw.naam = ''; nieuw.email = ''
    await laad()
  } catch (e) { fout.value = 'Toevoegen mislukt: ' + e.message }
  bezig.value = false
}

async function weg(a) {
  if (wis.value !== a) { wis.value = a; return }   // bevestiging: tweede klik voert uit
  wis.value = null
  try { await verwijderAm(a.id); await laad() }
  catch (e) { fout.value = 'Verwijderen mislukt: ' + e.message }
}

async function wijsToe(t, ev) {
  try { await zetWinkelAm(t.snelstart, ev.target.value || null); await st.laad() }
  catch (e) { fout.value = 'Toewijzen mislukt: ' + e.message }
}
</script>

<template>
  <div>
    <h1>Beheer</h1>
    <p class="sub">Accountmanagers uitnodigen en winkels toewijzen — alleen zichtbaar voor kantoor.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- AM's -->
    <div class="kaart">
      <h2>🚗 Accountmanagers</h2>
      <form class="rij vorm" @submit.prevent="toevoegen">
        <label>Naam<input v-model="nieuw.naam" required placeholder="bijv. Marian" data-test="am-naam" /></label>
        <label>E-mailadres<input v-model="nieuw.email" type="email" required placeholder="marian@tapparfum.nl" data-test="am-email" /></label>
        <button class="knop" type="submit" :disabled="bezig" data-test="am-toevoegen">+ Uitnodigen</button>
      </form>
      <p class="note">De accountmanager gaat daarna zelf naar het portaal → <b>Eerste keer? Account aanmaken</b> → kiest
        "Ik ben accountmanager" en registreert met precies dít e-mailadres. De koppeling gebeurt automatisch en is
        server-bewaakt.</p>

      <div v-for="a in ams" :key="a.id" class="rij item" data-test="am-rij">
        <b>{{ a.naam }}</b>
        <span class="mo">{{ a.email || '—' }}</span>
        <span class="badge" :class="a.auth_user_id ? 'ok' : 'wacht'" data-test="am-status">
          {{ a.auth_user_id ? '✓ gekoppeld' : 'uitgenodigd' }}
        </span>
        <span class="mo">{{ AANTAL[a.id] || 0 }} winkel{{ (AANTAL[a.id] || 0) === 1 ? '' : 's' }}</span>
        <button class="weg" :class="{ zeker: wis === a }" type="button" data-test="am-verwijder"
                aria-label="Accountmanager verwijderen" @click="weg(a)">{{ wis === a ? 'Zeker?' : '✕' }}</button>
      </div>
      <p v-if="!ams.length" class="stil">Nog geen accountmanagers uitgenodigd.</p>
    </div>

    <!-- Winkels toewijzen -->
    <div class="kaart">
      <h2>🏬 Winkels toewijzen</h2>
      <div v-for="t in st.items" :key="t.snelstart" class="rij item" data-test="winkel-rij">
        <b>{{ t.name }}</b>
        <span class="mo">{{ t.snelstart }}</span>
        <select class="amsel" :value="t.am_id || ''" :aria-label="'Accountmanager voor ' + t.name" data-test="winkel-am" @change="wijsToe(t, $event)">
          <option value="">— geen AM —</option>
          <option v-for="a in ams" :key="a.id" :value="a.id">{{ a.naam }}</option>
        </select>
      </div>
      <p v-if="!st.items.length" class="stil">Nog geen winkels.</p>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 12px;font-size:16px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:14px}
.rij{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.vorm{align-items:flex-end;margin-bottom:8px}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:160px}
input,select{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
input:focus,select:focus{border-color:var(--coral)}
.knop{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer}
.knop:disabled{opacity:.6}
.note{font-size:12.5px;color:var(--grey);background:#faf7f2;border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:0 0 10px}
.item{padding:9px 0;border-bottom:1px solid var(--line);font-size:14px}
.item:last-of-type{border-bottom:0}
.mo{color:var(--grey);font-size:12.5px}
.badge{font-size:11.5px;font-weight:800;border-radius:6px;padding:2px 10px}
.badge.ok{background:#e7f3d9;color:#2c5a12}
.badge.wacht{background:#fdeee7;color:var(--coral)}
.amsel{margin-left:auto;max-width:200px}
.weg{background:none;border:0;color:var(--grey);cursor:pointer;font-size:14px}
.weg:hover{color:#b3261e}
.weg.zeker{color:#b3261e;font-weight:800}
.fout{color:#b3261e}
.stil{color:var(--grey);font-size:13px}
</style>
