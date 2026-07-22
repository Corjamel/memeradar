<script setup>
// Bestellingen bij één winkel (inkoop bij TapParfum) — v71-datamodel.
// AM/kantoor registreert; de partner kijkt mee en bestelt via het portaal.
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { eur0 } from '../../../lib/format.js'
import { haalCentral } from '../../beheer/api.js'
import { bestellingenVan, inkoopJaar, dagenSindsBestelling, bestelStil, voegBestellingToe, BESTEL_STIL_DAGEN } from '../logic.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const emit = defineEmits(['bijgewerkt'])
const auth = useAuth()
const st = useTappunten()
const vandaag = new Date().toISOString().slice(0, 10)

const fout = ref('')
const bezig = ref(false)
const wis = ref(null)            // twee-staps verwijderen
const shopUrl = ref('')
const vorm = reactive({ at: vandaag, ref: '', totaal: '', omschrijving: '' })

const t = computed(() => props.tappunt)
const lijst = computed(() => bestellingenVan(t.value))
const dagen = computed(() => dagenSindsBestelling(t.value))
const stil = computed(() => bestelStil(t.value))

onMounted(async () => {
  try { shopUrl.value = String(await haalCentral('shopUrl') || '') } catch { /* knop blijft dan weg */ }
})

async function bewaar(t2) {
  bezig.value = true; fout.value = ''
  try { await st.bewaar(t2); emit('bijgewerkt', t2) }
  catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}

async function toevoegen() {
  if (bezig.value) return
  const t2 = voegBestellingToe(t.value, { ...vorm, bron: 'handmatig' })
  if (!t2) { fout.value = `Ordernummer «${vorm.ref.trim()}» is al geregistreerd (dubbel).`; return }
  await bewaar(t2)
  Object.assign(vorm, { at: vandaag, ref: '', totaal: '', omschrijving: '' })
}

async function verwijder(b) {
  if (bezig.value) return
  if (wis.value !== b.id) { wis.value = b.id; return }
  wis.value = null
  await bewaar({ ...t.value, bestellingen: lijst.value.filter(x => x.id !== b.id) })
}
</script>

<template>
  <section class="blok">
    <div class="kop">
      <h2>📦 Bestellingen bij TapParfum</h2>
      <span v-if="dagen != null" class="badge" :class="stil ? 'amber' : 'groen'" data-test="bestel-ritme">
        {{ stil ? `⚠ ${dagen} dagen stil (drempel ${BESTEL_STIL_DAGEN})` : `laatste ${dagen} dagen geleden` }}
      </span>
      <span v-else class="badge grijs" data-test="bestel-ritme">nog geen bestellingen</span>
    </div>
    <p class="mo">Inkoop dit jaar: <b data-test="inkoop-jaar">{{ eur0(inkoopJaar(t)) }}</b> · dit is wat de winkel bij TapParfum inkoopt — de winkelverkoop staat er los van.</p>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- AM/kantoor: registreren -->
    <form v-if="!auth.isPartner" class="vorm" @submit.prevent="toevoegen">
      <input v-model="vorm.at" type="date" aria-label="Datum" data-test="best-datum" />
      <input v-model="vorm.ref" placeholder="ordernr." class="kort" data-test="best-ref" />
      <input v-model.number="vorm.totaal" type="number" min="0" step="0.01" placeholder="totaal €" class="kort" required data-test="best-totaal" />
      <input v-model="vorm.omschrijving" placeholder="omschrijving" class="lang" />
      <button class="btn" type="submit" :disabled="bezig" data-test="best-toevoegen">Registreren</button>
    </form>
    <a v-else-if="shopUrl" class="btn portaal" :href="shopUrl" target="_blank" rel="noopener noreferrer">🛒 Naar het bestelportaal →</a>

    <div v-for="b in lijst.slice(0, 8)" :key="b.id" class="rij" data-test="bestelling">
      <span class="datum">{{ b.at }}</span>
      <b>{{ eur0(b.totaal) }}</b>
      <span v-if="b.ref" class="mo">#{{ b.ref }}</span>
      <span v-if="b.omschrijving" class="mo oms">{{ b.omschrijving }}</span>
      <span class="bron">{{ b.bron }}</span>
      <button v-if="!auth.isPartner" class="wis" type="button" :data-test="'best-wis-' + b.id"
              :aria-label="'Bestelling verwijderen: ' + b.at" @click="verwijder(b)">
        {{ wis === b.id ? 'Zeker?' : '×' }}
      </button>
    </div>
    <p v-if="!lijst.length" class="stil">Nog geen bestellingen geregistreerd.</p>
    <p v-if="lijst.length > 8" class="mo">… en nog {{ lijst.length - 8 }} oudere.</p>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-top:14px}
.kop{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
h2{margin:0;font-size:16px;flex:1}
.badge{font-size:11.5px;font-weight:800;border-radius:6px;padding:3px 10px}
.badge.groen{background:var(--green-soft);color:#2c5a12}
.badge.amber{background:var(--amber);color:#412402}
.badge.grijs{background:var(--cream);color:var(--grey)}
.mo{color:var(--grey);font-size:12.5px;margin:6px 0 0}
.mo b{color:var(--ink)}
.vorm{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.vorm input{padding:8px 10px;border:1.5px solid var(--line);border-radius:10px;font-size:13.5px;font-family:inherit}
.vorm input:focus{border-color:var(--coral)}
.kort{width:110px}
.lang{flex:1;min-width:160px}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:8px 14px;font-weight:800;cursor:pointer;font-size:13px}
.btn:disabled{opacity:.6}
.btn.portaal{display:inline-block;text-decoration:none;margin:10px 0}
.rij{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid var(--line);font-size:13.5px}
.rij:last-of-type{border-bottom:0}
.datum{color:var(--grey);font-size:12.5px;font-variant-numeric:tabular-nums}
.rij b{font-variant-numeric:tabular-nums}
.rij .mo{margin:0}
.oms{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bron{margin-left:auto;font-size:10.5px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:var(--grey);background:var(--cream);border-radius:5px;padding:2px 7px}
.wis{background:none;border:1.5px solid var(--line);border-radius:8px;padding:2px 9px;font-size:12px;font-weight:700;color:var(--coral-d);cursor:pointer}
.wis:hover{border-color:var(--coral-d)}
.fout{color:#b3261e;font-size:13px}
.stil{color:var(--grey);font-size:13px}
</style>
