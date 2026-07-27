<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { haalBerichten, haalAccountmanagers, stuurBericht, beantwoord } from '../api.js'
import { haalWinkelvragen, stuurWinkelvraag, beantwoordWinkelvraag, fotoLink } from '../../winkelvragen/api.js'

const auth = useAuth()
const st = useTappunten()
const items = ref([])          // kantoor <-> AM
const vragen = ref([])         // winkel -> AM/kantoor
const ams = ref([])
const fout = ref('')
const bezig = ref(false)
const antwoorden = reactive({})     // bericht-id -> concept (AM)
const vraagAntwoorden = reactive({})// vraag-id -> concept (AM/kantoor)
const nieuw = reactive({ aan_am: '', type: 'vraag', txt: '' })
const nieuweVraag = reactive({ type: 'vraag', txt: '' })
const nieuweFoto = ref(null)          // bewijsfoto bij retour/probleem

const TYPE_LABEL = { vraag: '❓ Vraag', probleem: '⚠️ Probleem', retour: '↩️ Retour' }
const AM_NAAM = () => Object.fromEntries(ams.value.map(a => [a.id, a.naam]))
const WINKEL = () => Object.fromEntries(st.items.map(t => [t.snelstart, t.name]))

async function laad() {
  fout.value = ''
  try {
    if (!auth.isPartner) items.value = await haalBerichten()
    vragen.value = await haalWinkelvragen()
    if (auth.isKantoor) ams.value = await haalAccountmanagers()
    if (!st.items.length) await st.laad()
  } catch (e) { fout.value = 'Kon berichten niet laden: ' + e.message }
}
onMounted(laad)

// -- kantoor: vraag/taak aan AM --
async function versturen() {
  if (bezig.value) return
  if (!nieuw.aan_am || !nieuw.txt.trim()) { fout.value = 'Kies een accountmanager en typ een bericht.'; return }
  bezig.value = true; fout.value = ''
  try {
    await stuurBericht({ aan_am: nieuw.aan_am, type: nieuw.type, txt: nieuw.txt.trim(), van: auth.user?.email || 'kantoor' })
    nieuw.txt = ''; await laad()
  } catch (e) { fout.value = 'Versturen mislukt: ' + e.message }
  bezig.value = false
}

// -- AM: bericht van kantoor beantwoorden --
async function beantwoordItem(b) {
  const a = (antwoorden[b.id] || '').trim(); if (!a) return
  try { await beantwoord(b.id, a); antwoorden[b.id] = ''; await laad() }
  catch (e) { fout.value = 'Beantwoorden mislukt: ' + e.message }
}

// -- partner: winkelvraag melden --
async function meldVraag() {
  if (bezig.value) return
  const eigen = st.items[0]
  if (!eigen) { fout.value = 'Geen winkel gevonden bij je account.'; return }
  if (!nieuweVraag.txt.trim()) { fout.value = 'Typ eerst je bericht.'; return }
  bezig.value = true; fout.value = ''
  try {
    await stuurWinkelvraag({ tappunt_snelstart: eigen.snelstart, type: nieuweVraag.type, txt: nieuweVraag.txt.trim(), foto: nieuweFoto.value })
    nieuweVraag.txt = ''; nieuweFoto.value = null; await laad()
  } catch (e) { fout.value = 'Versturen mislukt: ' + e.message }
  bezig.value = false
}

// Bewijsfoto openen via een tijdelijke (signed) link.
async function openFoto(v) {
  try { window.open(await fotoLink(v.foto_pad), '_blank', 'noopener,noreferrer') }
  catch (e) { fout.value = 'Foto openen mislukt: ' + e.message }
}

// -- AM/kantoor: winkelvraag beantwoorden --
async function beantwoordVraagItem(v) {
  const a = (vraagAntwoorden[v.id] || '').trim(); if (!a) return
  try { await beantwoordWinkelvraag(v.id, a, auth.user?.email || null); vraagAntwoorden[v.id] = ''; await laad() }
  catch (e) { fout.value = 'Beantwoorden mislukt: ' + e.message }
}
</script>

<template>
  <div>
    <header class="vheld">
      <div>
        <p class="eyebrow">Communicatie</p>
        <h1>Berichten</h1>
        <p class="sub" v-if="auth.isKantoor">Vragen & taken aan accountmanagers, en meldingen uit de winkels.</p>
        <p class="sub" v-else-if="auth.isAm">Vragen en taken van kantoor, en meldingen uit jouw winkels.</p>
        <p class="sub" v-else>Vraag, probleem of retour? Meld het hier — je accountmanager reageert.</p>
      </div>
    </header>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- ===== PARTNER: melden ===== -->
    <form v-if="auth.isPartner" class="kaart nieuw" @submit.prevent="meldVraag">
      <div class="rij">
        <label>Soort
          <select v-model="nieuweVraag.type" data-test="vraag-type">
            <option value="vraag">Vraag</option>
            <option value="probleem">Probleem</option>
            <option value="retour">Retour</option>
          </select>
        </label>
      </div>
      <label>Bericht
        <textarea v-model="nieuweVraag.txt" rows="3" required placeholder="Beschrijf je vraag, probleem of retour…" data-test="vraag-txt"></textarea>
      </label>
      <label v-if="nieuweVraag.type !== 'vraag'">Bewijsfoto (aangeraden bij retour)
        <input type="file" accept="image/*" data-test="vraag-foto"
               @change="nieuweFoto = $event.target.files[0] || null" />
      </label>
      <button class="btn" type="submit" :disabled="bezig" data-test="vraag-verstuur">{{ bezig ? 'Bezig…' : 'Versturen' }}</button>
    </form>

    <!-- ===== KANTOOR: vraag/taak aan AM ===== -->
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

    <!-- ===== Winkelvragen (alle rollen zien hun eigen uitsnede) ===== -->
    <h2 v-if="vragen.length || auth.isPartner">{{ auth.isPartner ? 'Jouw meldingen' : 'Meldingen uit winkels' }}</h2>
    <p v-if="auth.isPartner && !vragen.length && !fout" class="stil">Nog geen meldingen.</p>
    <div v-for="v in vragen" :key="v.id" class="kaart item" :class="{ klaar: v.status === 'beantwoord' }" data-test="winkelvraag">
      <div class="itemkop">
        <span class="type">{{ TYPE_LABEL[v.type] || v.type }}</span>
        <span class="meta" v-if="!auth.isPartner">van {{ WINKEL()[v.tappunt_snelstart] || v.tappunt_snelstart }}</span>
        <span class="status" :class="v.status">{{ v.status === 'beantwoord' ? '✓ beantwoord' : 'open' }}</span>
      </div>
      <p class="txt">{{ v.txt }}</p>
      <button v-if="v.foto_pad" class="fotoknop" type="button" data-test="vraag-foto-knop" @click="openFoto(v)">📷 Bekijk bewijsfoto</button>
      <p v-if="v.antwoord" class="antwoord" data-test="vraag-antwoord">↳ {{ v.antwoord }}<span v-if="v.antwoord_door" class="meta"> — {{ v.antwoord_door }}</span></p>
      <div v-if="!auth.isPartner && v.status === 'open'" class="beantwoord">
        <textarea v-model="vraagAntwoorden[v.id]" rows="2" placeholder="Typ je antwoord aan de winkel…" data-test="vraag-antwoord-veld"></textarea>
        <button class="btn" type="button" data-test="vraag-antwoord-knop" @click="beantwoordVraagItem(v)">Beantwoord</button>
      </div>
    </div>

    <!-- ===== Kantoor <-> AM berichten ===== -->
    <template v-if="!auth.isPartner">
      <h2 v-if="items.length">Vragen & taken (kantoor ↔ AM)</h2>
      <p v-if="!items.length && !vragen.length && !fout" class="stil">Nog geen berichten.</p>
      <div v-for="b in items" :key="b.id" class="kaart item" :class="{ klaar: b.status === 'klaar' }" data-test="bericht">
        <div class="itemkop">
          <span class="type">{{ b.type === 'taak' ? '📋 Taak' : '❓ Vraag' }}</span>
          <span class="meta">van {{ b.van }}<template v-if="auth.isKantoor"> · aan {{ AM_NAAM()[b.aan_am] || 'AM' }}</template></span>
          <span class="status" :class="b.status">{{ b.status === 'klaar' ? '✓ beantwoord' : 'open' }}</span>
        </div>
        <p class="txt">{{ b.txt }}</p>
        <p v-if="b.antwoord" class="antwoord" data-test="antwoord">↳ {{ b.antwoord }}</p>
        <div v-if="auth.isAm && b.status === 'open'" class="beantwoord">
          <textarea v-model="antwoorden[b.id]" rows="2" placeholder="Typ je antwoord…" data-test="antwoord-veld"></textarea>
          <button class="btn" type="button" data-test="antwoord-knop" @click="beantwoordItem(b)">Beantwoord</button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{font-size:15px;margin:18px 0 8px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.nieuw{display:flex;flex-direction:column;gap:10px}
.rij{display:flex;gap:12px;flex-wrap:wrap}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:160px}
select,textarea{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
select:focus,textarea:focus{border-color:var(--coral)}
.btn{align-self:flex-start;background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 16px;font-weight:800;cursor:pointer}
.btn:disabled{opacity:.6}
.item.klaar{opacity:.82}
.itemkop{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px}
.type{font-size:12px;font-weight:800}
.meta{color:var(--grey);font-size:12px}
.status{margin-left:auto;font-size:11.5px;font-weight:800;border-radius:6px;padding:2px 8px;background:#fdeee7;color:var(--coral)}
.status.klaar,.status.beantwoord{background:#e7f3d9;color:#2c5a12}
.txt{margin:0;font-size:14.5px}
.antwoord{margin:8px 0 0;font-size:13.5px;color:#2c5a12;background:#f4faf0;border-radius:8px;padding:8px 10px}
.beantwoord{display:flex;gap:8px;margin-top:10px;align-items:flex-start}
.beantwoord textarea{flex:1}
.fotoknop{align-self:flex-start;background:none;border:1.5px solid var(--line);border-radius:8px;padding:5px 12px;font-size:12.5px;font-weight:700;color:var(--grey);cursor:pointer;margin-top:8px}
.fotoknop:hover{border-color:var(--coral);color:var(--coral-d)}
input[type=file]{padding:7px;border:1.5px dashed var(--line);border-radius:10px;font-size:13px}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
