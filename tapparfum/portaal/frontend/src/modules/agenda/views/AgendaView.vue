<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { haalAgenda, planBezoek, zetStatus } from '../api.js'

const auth = useAuth()
const st = useTappunten()
const items = ref([])
const fout = ref('')
const bezig = ref(false)
const nieuw = reactive({ tappunt_snelstart: '', datum: '', tijd: '', type: 'bezoek', notitie: '' })

const STATUS_LABEL = { voorgesteld: 'wacht op winkel', geaccepteerd: 'geaccepteerd', afgewezen: 'afgewezen', afgerond: '✓ afgerond' }
const WINKEL = computed(() => Object.fromEntries(st.items.map(t => [t.snelstart, t.name])))
const open = computed(() => items.value.filter(i => i.status === 'voorgesteld' || i.status === 'geaccepteerd'))
const klaar = computed(() => items.value.filter(i => i.status === 'afgewezen' || i.status === 'afgerond'))

async function laad() {
  fout.value = ''
  try { items.value = await haalAgenda() }
  catch (e) { fout.value = 'Kon de agenda niet laden: ' + e.message }
}
onMounted(async () => {
  if (!st.items.length) await st.laad()
  await laad()
})

async function plannen() {
  if (bezig.value) return
  if (!nieuw.tappunt_snelstart || !nieuw.datum) { fout.value = 'Kies een winkel en een datum.'; return }
  bezig.value = true; fout.value = ''
  try {
    await planBezoek({ ...nieuw, am_id: auth.amId })
    nieuw.tappunt_snelstart = ''; nieuw.datum = ''; nieuw.tijd = ''; nieuw.notitie = ''
    await laad()
  } catch (e) { fout.value = 'Plannen mislukt: ' + e.message }
  bezig.value = false
}

async function status(i, s) {
  try { await zetStatus(i.id, s); await laad() }
  catch (e) { fout.value = 'Actie mislukt: ' + e.message }
}
</script>

<template>
  <div>
    <header class="vheld">
      <div>
        <p class="eyebrow">Planning</p>
        <h1>Agenda</h1>
        <p class="sub" v-if="auth.isPartner">Bezoekvoorstellen van je accountmanager — accepteer of wijs af.</p>
        <p class="sub" v-else>Plan bezoeken; de winkel accepteert of wijst af.</p>
      </div>
    </header>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- AM/kantoor: bezoek plannen -->
    <form v-if="!auth.isPartner" class="kaart nieuw" @submit.prevent="plannen">
      <div class="rij">
        <label>Winkel
          <select v-model="nieuw.tappunt_snelstart" required data-test="winkel-select">
            <option value="" disabled>Kies winkel…</option>
            <option v-for="t in st.items" :key="t.snelstart" :value="t.snelstart">{{ t.name }}</option>
          </select>
        </label>
        <label>Datum<input v-model="nieuw.datum" type="date" required data-test="datum" /></label>
        <label>Tijd<input v-model="nieuw.tijd" type="time" /></label>
        <label>Soort
          <select v-model="nieuw.type">
            <option value="bezoek">Bezoek</option>
            <option value="telefoon">Telefonisch</option>
          </select>
        </label>
      </div>
      <button class="btn" type="submit" :disabled="bezig" data-test="plan-knop">{{ bezig ? 'Bezig…' : 'Inplannen' }}</button>
    </form>

    <h2 v-if="open.length">Gepland</h2>
    <div v-for="i in open" :key="i.id" class="kaart item" data-test="agenda-item">
      <div class="itemkop">
        <b>{{ WINKEL[i.tappunt_snelstart] || i.tappunt_snelstart }}</b>
        <span class="meta">{{ i.type === 'telefoon' ? '📞' : '📍' }} {{ i.datum }}<template v-if="i.tijd"> · {{ i.tijd }}</template></span>
        <span class="status" :class="i.status" data-test="status">{{ STATUS_LABEL[i.status] }}</span>
      </div>
      <p v-if="i.notitie" class="notitie">{{ i.notitie }}</p>
      <div class="acties">
        <!-- Partner: accepteren / afwijzen bij een voorstel -->
        <template v-if="auth.isPartner && i.status === 'voorgesteld'">
          <button class="btn" data-test="accepteer" @click="status(i, 'geaccepteerd')">Accepteer</button>
          <button class="btn donker" data-test="wijs-af" @click="status(i, 'afgewezen')">Wijs af</button>
        </template>
        <!-- AM/kantoor: afronden zodra geaccepteerd -->
        <button v-if="!auth.isPartner && i.status === 'geaccepteerd'" class="btn" data-test="afronden"
                @click="status(i, 'afgerond')">✓ Afronden</button>
      </div>
    </div>
    <p v-if="!open.length && !fout" class="stil">Niets gepland.</p>

    <details v-if="klaar.length" class="hist">
      <summary>Afgerond & afgewezen ({{ klaar.length }})</summary>
      <div v-for="i in klaar" :key="i.id" class="kaart item klaar">
        <div class="itemkop">
          <b>{{ WINKEL[i.tappunt_snelstart] || i.tappunt_snelstart }}</b>
          <span class="meta">{{ i.datum }}</span>
          <span class="status" :class="i.status">{{ STATUS_LABEL[i.status] }}</span>
        </div>
      </div>
    </details>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{font-size:15px;margin:16px 0 8px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:10px}
.nieuw{display:flex;flex-direction:column;gap:10px}
.rij{display:flex;gap:12px;flex-wrap:wrap}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:140px}
select,input{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
select:focus,input:focus{border-color:var(--coral)}
.btn{align-self:flex-start;background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 14px;font-weight:800;cursor:pointer}
.btn.donker{background:#333}
.btn:disabled{opacity:.6}
.itemkop{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.meta{color:var(--grey);font-size:12.5px}
.status{margin-left:auto;font-size:11.5px;font-weight:800;border-radius:6px;padding:2px 8px;background:#fdeee7;color:var(--coral)}
.status.geaccepteerd{background:#e7f3d9;color:#2c5a12}
.status.afgerond{background:#e7f3d9;color:#2c5a12}
.status.afgewezen{background:#eee;color:#666}
.notitie{margin:6px 0 0;font-size:13.5px;color:var(--grey)}
.acties{display:flex;gap:8px;margin-top:10px}
.item.klaar{opacity:.75}
.hist{margin-top:14px}
.hist summary{cursor:pointer;font-size:13px;color:var(--grey);font-weight:700;margin-bottom:8px}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
