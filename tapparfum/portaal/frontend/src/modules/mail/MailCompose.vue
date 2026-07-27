<script setup>
// Mail schrijven — het v71 "HubSpot-patroon" (r.1395-1416): eerst volledig
// registreren in het logboek van de winkel, daarna je eigen mailprogramma
// openen met alles ingevuld. Zo staat élk klantcontact vast in het systeem.
import { computed, reactive, ref, watch } from 'vue'
import { useAuth } from '../../stores/auth.js'
import { useToast } from '../../stores/toast.js'
import { useTappunten } from '../tappunten/store.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const emit = defineEmits(['sluit', 'gelogd'])
const auth = useAuth()
const toast = useToast()
const st = useTappunten()
const bezig = ref(false)
const fout = ref('')

const voornaam = computed(() => String(props.tappunt.contact || '').split(' ')[0] || 'relatie')
const vorm = reactive({ aan: '', onderwerp: '', bericht: '' })
watch(() => props.tappunt, t => {
  vorm.aan = t.email || ''
  vorm.onderwerp = 'TapParfum · ' + (t.name || '')
  vorm.bericht = `Beste ${voornaam.value},\n\n\n\nMet vriendelijke groet,\n${(auth.user && auth.user.email) || ''}\nTapParfum`
}, { immediate: true })

async function verstuur() {
  fout.value = ''
  if (!vorm.onderwerp.trim() || !vorm.bericht.trim()) { fout.value = 'Vul onderwerp én bericht in.'; return }
  bezig.value = true
  try {
    // 1) Registreren bij de winkel — dít is het v71/HubSpot-gedrag.
    const entry = {
      id: 'm-' + Math.random().toString(36).slice(2, 10),
      at: new Date().toISOString().slice(0, 10),
      type: 'mail', dir: 'uit',
      subject: vorm.onderwerp.trim(), body: vorm.bericht.trim(),
      txt: '✉️ ' + vorm.onderwerp.trim() + ' — ' + vorm.bericht.trim(),
      nextDate: '', nextDone: false
    }
    const t2 = { ...props.tappunt, logboek: [entry, ...(props.tappunt.logboek || [])] }
    await st.bewaar(t2)
    emit('gelogd', t2)
    // 2) Eigen mailprogramma openen met alles ingevuld (mailto).
    try {
      window.location.href = 'mailto:' + encodeURIComponent(vorm.aan) +
        '?subject=' + encodeURIComponent(vorm.onderwerp.trim()) +
        '&body=' + encodeURIComponent(vorm.bericht.trim().replace(/\n/g, '\r\n'))
    } catch (e) { /* mailto is een extraatje; de registratie staat al vast */ }
    toast.ok('Mail geregistreerd in het logboek — je mailprogramma opent nu')
    emit('sluit')
  } catch (e) { fout.value = 'Registreren mislukt: ' + e.message }
  bezig.value = false
}
</script>

<template>
  <div class="overlay" role="dialog" aria-modal="true" :aria-label="'Mail aan ' + tappunt.name" @click.self="emit('sluit')">
    <div class="paneel">
      <div class="kop">
        <b>✉️ Mail aan {{ tappunt.name }}</b>
        <button class="dicht" type="button" aria-label="Sluiten" data-test="mail-sluit" @click="emit('sluit')">×</button>
      </div>
      <p class="uitleg">De mail wordt éérst vastgelegd in het logboek van de winkel; daarna opent je eigen mailprogramma met alles ingevuld.</p>
      <label>Aan<input v-model="vorm.aan" type="email" data-test="mail-aan" /></label>
      <label>Onderwerp<input v-model="vorm.onderwerp" data-test="mail-onderwerp" /></label>
      <label>Bericht<textarea v-model="vorm.bericht" rows="8" data-test="mail-bericht"></textarea></label>
      <p v-if="fout" class="fout" role="alert">{{ fout }}</p>
      <div class="voet">
        <button class="btn" type="button" :disabled="bezig" data-test="mail-verstuur" @click="verstuur">
          {{ bezig ? 'Bezig…' : 'Registreren & versturen →' }}
        </button>
        <button class="ghost" type="button" @click="emit('sluit')">Annuleren</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay{position:fixed;inset:0;background:rgba(42,33,28,.45);display:flex;align-items:center;justify-content:center;z-index:60;padding:20px}
.paneel{background:#fff;border-radius:16px;padding:20px 22px;width:100%;max-width:560px;max-height:92vh;overflow:auto;box-shadow:0 18px 50px -18px rgba(0,0,0,.4)}
.kop{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:6px}
.kop b{font-size:15.5px}
.dicht{background:none;border:0;font-size:22px;line-height:1;cursor:pointer;color:var(--grey)}
.uitleg{margin:0 0 12px;font-size:12.5px;color:var(--grey);line-height:1.5}
label{display:flex;flex-direction:column;gap:4px;font-size:12px;font-weight:700;color:var(--grey);margin-bottom:10px}
input,textarea{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:13.5px;font-family:inherit;color:var(--ink)}
textarea{resize:vertical;line-height:1.5}
input:focus,textarea:focus{border-color:var(--coral);outline:none}
.voet{display:flex;gap:10px;align-items:center}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:800;font-size:13px;cursor:pointer}
.btn:hover{background:var(--coral-d)}
.ghost{background:none;border:1.5px solid var(--line);border-radius:10px;padding:9px 14px;font-weight:700;font-size:12.5px;color:var(--grey);cursor:pointer}
.fout{color:#b3261e;font-size:13px;margin:0 0 8px}
</style>
