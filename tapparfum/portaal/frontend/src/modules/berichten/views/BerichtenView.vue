<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { haalBerichten, haalAccountmanagers, stuurBericht, beantwoord } from '../api.js'

const auth = useAuth()
const items = ref([])
const ams = ref([])
const fout = ref('')
const bezig = ref(false)
const antwoorden = reactive({})   // id -> conceptantwoord (AM)
const nieuw = reactive({ aan_am: '', type: 'vraag', txt: '' })

const AM_NAAM = () => Object.fromEntries(ams.value.map(a => [a.id, a.naam]))

async function laad() {
  fout.value = ''
  try {
    items.value = await haalBerichten()
    if (auth.isKantoor) ams.value = await haalAccountmanagers()
  } catch (e) { fout.value = 'Kon berichten niet laden: ' + e.message }
}
onMounted(laad)

async function versturen() {
  if (bezig.value) return
  if (!nieuw.aan_am || !nieuw.txt.trim()) { fout.value = 'Kies een accountmanager en typ een bericht.'; return }
  bezig.value = true; fout.value = ''
  try {
    await stuurBericht({ aan_am: nieuw.aan_am, type: nieuw.type, txt: nieuw.txt.trim(), van: auth.user?.email || 'kantoor' })
    nieuw.txt = ''
    await laad()
  } catch (e) { fout.value = 'Versturen mislukt: ' + e.message }
  bezig.value = false
}

async function beantwoordItem(b) {
  const a = (antwoorden[b.id] || '').trim()
  if (!a) return
  try {
    await beantwoord(b.id, a)
    antwoorden[b.id] = ''
    await laad()
  } catch (e) { fout.value = 'Beantwoorden mislukt: ' + e.message }
}
</script>

<template>
  <div>
    <h1>Berichten</h1>
    <p class="sub" v-if="auth.isKantoor">Stuur een vraag of taak aan een accountmanager — het antwoord komt hier terug.</p>
    <p class="sub" v-else>Vragen en taken van kantoor. Beantwoord ze hier; kantoor ziet je antwoord direct.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Kantoor: nieuw bericht -->
    <form v-if="auth.isKantoor" class="kaart nieuw" @submit.prevent="versturen">
      <div class="rij">
        <label>Aan
          <select v-model="nieuw.aan_am" required data-test="am-select">
            <option value="" disabled>Kies accountmanager…</option>
            <option v-for="a in ams" :key="a.id" :value="a.id">{{ a.naam }}</option>
          </select>
        </label>
        <label>Soort
          <select v-model="nieuw.type">
            <option value="vraag">Vraag</option>
            <option value="taak">Taak</option>
          </select>
        </label>
      </div>
      <label>Bericht
        <textarea v-model="nieuw.txt" rows="3" required placeholder="Typ je vraag of taak…"></textarea>
      </label>
      <button class="btn" type="submit" :disabled="bezig" data-test="verstuur">{{ bezig ? 'Bezig…' : 'Versturen' }}</button>
    </form>

    <!-- Lijst -->
    <p v-if="!items.length && !fout" class="stil">Nog geen berichten.</p>
    <div v-for="b in items" :key="b.id" class="kaart item" :class="{ klaar: b.status === 'klaar' }" data-test="bericht">
      <div class="itemkop">
        <span class="type" :class="b.type">{{ b.type === 'taak' ? '📋 Taak' : '❓ Vraag' }}</span>
        <span class="meta">van {{ b.van }}<template v-if="auth.isKantoor"> · aan {{ AM_NAAM()[b.aan_am] || 'AM' }}</template></span>
        <span class="status" :class="b.status">{{ b.status === 'klaar' ? '✓ beantwoord' : 'open' }}</span>
      </div>
      <p class="txt">{{ b.txt }}</p>
      <p v-if="b.antwoord" class="antwoord" data-test="antwoord">↳ {{ b.antwoord }}</p>

      <!-- AM: beantwoorden -->
      <div v-if="auth.isAm && b.status === 'open'" class="beantwoord">
        <textarea v-model="antwoorden[b.id]" rows="2" placeholder="Typ je antwoord…" data-test="antwoord-veld"></textarea>
        <button class="btn" type="button" data-test="antwoord-knop" @click="beantwoordItem(b)">Beantwoord</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.nieuw{display:flex;flex-direction:column;gap:10px}
.rij{display:flex;gap:12px;flex-wrap:wrap}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:160px}
select,textarea{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
select:focus,textarea:focus{outline:none;border-color:var(--coral)}
.btn{align-self:flex-start;background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 16px;font-weight:800;cursor:pointer}
.btn:disabled{opacity:.6}
.item.klaar{opacity:.82}
.itemkop{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px}
.type{font-size:12px;font-weight:800}
.meta{color:var(--grey);font-size:12px}
.status{margin-left:auto;font-size:11.5px;font-weight:800;border-radius:6px;padding:2px 8px;background:#fdeee7;color:var(--coral)}
.status.klaar{background:#e7f3d9;color:#2c5a12}
.txt{margin:0;font-size:14.5px}
.antwoord{margin:8px 0 0;font-size:13.5px;color:#2c5a12;background:#f4faf0;border-radius:8px;padding:8px 10px}
.beantwoord{display:flex;gap:8px;margin-top:10px;align-items:flex-start}
.beantwoord textarea{flex:1}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
