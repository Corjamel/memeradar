<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { haalTreden, bewaarTreden, tredeVoor } from '../api.js'
import { eur0 } from '../../../lib/format.js'

const auth = useAuth()
const st = useTappunten()
const treden = ref([])
const bewerk = ref([])       // kantoor: bewerkbare kopie
const fout = ref('')
const melding = ref('')

onMounted(async () => {
  try {
    if (!st.items.length) await st.laad()
    treden.value = await haalTreden()
    bewerk.value = treden.value.map(t => ({ ...t }))
  } catch (e) { fout.value = 'Kon beloningen niet laden: ' + e.message }
})

const lijst = computed(() => [...treden.value].sort((a, b) => a.drempel - b.drempel))
const eigen = computed(() => st.items[0] || null)
const mijn = computed(() => eigen.value ? tredeVoor(Number(eigen.value.jaaromzet) || 0, treden.value) : null)
const perWinkel = computed(() => st.items.map(t => {
  const r = tredeVoor(Number(t.jaaromzet) || 0, treden.value)
  return { t, trede: r.huidig ? r.huidig.naam : '—' }
}).sort((a, b) => (Number(b.t.jaaromzet) || 0) - (Number(a.t.jaaromzet) || 0)))

async function opslaan() {
  fout.value = ''; melding.value = ''
  try {
    const schoon = bewerk.value.map(t => ({ ...t, drempel: Number(t.drempel) || 0 }))
    await bewaarTreden(schoon)
    treden.value = schoon
    melding.value = '✓ Treden opgeslagen — direct zichtbaar voor het hele netwerk.'
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
}
</script>

<template>
  <div>
    <h1>Beloningen</h1>
    <p class="sub" v-if="auth.isPartner">Waar je voor speelt — groei in omzet en klim in de ladder.</p>
    <p class="sub" v-else>De beloningsladder van het netwerk{{ auth.isKantoor ? ' — pas de treden hieronder aan' : '' }}.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Partner: eigen ladder -->
    <template v-if="auth.isPartner && eigen">
      <div class="kaart" v-if="mijn">
        <p class="regel">Jullie jaaromzet: <b>{{ eur0(eigen.jaaromzet) }}</b> ·
          huidige trede: <b data-test="mijn-trede">{{ mijn.huidig ? mijn.huidig.naam : 'nog geen' }}</b></p>
        <template v-if="mijn.volgende">
          <div class="balk"><div class="vul" :style="{ width: mijn.pct + '%' }"></div></div>
          <p class="mo">Nog {{ eur0(Math.max(0, mijn.volgende.drempel - (eigen.jaaromzet || 0))) }} tot <b>{{ mijn.volgende.naam }}</b></p>
        </template>
        <p v-else class="mo">🏆 Hoogste trede bereikt!</p>
      </div>
      <div v-for="tr in lijst" :key="tr.id" class="kaart trede" data-test="trede"
           :class="{ behaald: (eigen.jaaromzet || 0) >= tr.drempel }">
        <div class="itemkop">
          <b>{{ (eigen.jaaromzet || 0) >= tr.drempel ? '✓' : '○' }} {{ tr.naam }}</b>
          <span class="meta">vanaf {{ eur0(tr.drempel) }}</span>
        </div>
        <p class="txt">{{ tr.tekst }}</p>
      </div>
    </template>

    <!-- AM/kantoor: winkels + hun trede -->
    <div v-if="!auth.isPartner" class="kaart">
      <h2>Winkels & treden</h2>
      <div v-for="r in perWinkel" :key="r.t.snelstart" class="rij" data-test="winkel-trede">
        <b>{{ r.t.name }}</b>
        <span class="mo">{{ eur0(r.t.jaaromzet) }}</span>
        <span class="badge">{{ r.trede }}</span>
      </div>
      <p v-if="!perWinkel.length" class="stil">Geen winkels.</p>
    </div>

    <!-- Kantoor: treden aanpassen -->
    <details v-if="auth.isKantoor" class="kaart beheer" open>
      <summary>Treden aanpassen</summary>
      <div v-for="(t, i) in bewerk" :key="t.id" class="bewerkrij">
        <input v-model="t.naam" class="kort" :data-test="'trede-naam-' + i" />
        <input v-model="t.drempel" type="number" min="0" class="kort" :data-test="'trede-drempel-' + i" />
        <input v-model="t.tekst" class="lang" />
      </div>
      <div class="acties">
        <button class="btn" type="button" data-test="treden-opslaan" @click="opslaan">Opslaan voor het hele netwerk</button>
        <span v-if="melding" class="mo" role="status">{{ melding }}</span>
      </div>
    </details>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 10px;font-size:15px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.regel{margin:0 0 8px;font-size:14.5px}
.balk{height:8px;border-radius:6px;background:#f0ebe3;overflow:hidden;margin:6px 0}
.vul{height:100%;background:var(--coral)}
.mo{color:var(--grey);font-size:13px;margin:4px 0 0}
.trede{opacity:.75}
.trede.behaald{opacity:1;border-color:#bcd9a0}
.itemkop{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.meta{margin-left:auto;color:var(--grey);font-size:12.5px}
.txt{margin:6px 0 0;font-size:13.5px;color:var(--grey)}
.rij{display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--line);font-size:14px}
.rij:last-child{border-bottom:0}
.rij .mo{margin-left:auto}
.badge{background:#fdeee7;color:var(--coral);font-size:11.5px;font-weight:800;border-radius:6px;padding:2px 10px}
.beheer summary{cursor:pointer;font-weight:800;font-size:14px;margin-bottom:10px}
.bewerkrij{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap}
input{padding:8px 10px;border:1.5px solid var(--line);border-radius:10px;font-size:13.5px;font-family:inherit}
input:focus{border-color:var(--coral)}
.kort{width:130px}
.lang{flex:1;min-width:220px}
.acties{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:6px}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 16px;font-weight:800;cursor:pointer}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
