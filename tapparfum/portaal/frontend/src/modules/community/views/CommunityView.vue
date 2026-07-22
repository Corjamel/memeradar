<script setup>
// Community — de besloten tijdlijn per accountmanager-portefeuille (v71 pcommunity).
// Partners delen tips/vragen/successen; AM's plaatsen mededelingen; kantoor
// modereert. Wie wat ziet is server-side dichtgezet (RLS, migratie 013):
// partners van verschillende AM's zien elkaars posts NIET — dat is de
// "geen datalek"-eis. De client stuurt alleen de tekst; de database bepaalt
// portefeuille, auteur en rol.
import { computed, onMounted, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { haalPosts, plaats, verwijder } from '../api.js'

const auth = useAuth()
const posts = ref([])
const tekst = ref('')
const fout = ref('')
const melding = ref('')
const bezig = ref(false)
const laden = ref(true)

// Partner en AM mogen plaatsen; kantoor modereert (en verwijdert).
const magPlaatsen = computed(() => auth.isPartner || auth.isAm)
const magModereren = computed(() => auth.isKantoor)

const ROLLABEL = { hq: 'TapParfum HQ', am: 'Accountmanager', partner: 'Partner' }

function wanneer(iso) {
  if (!iso) return ''
  const d = new Date(iso), nu = new Date()
  const min = Math.round((nu - d) / 60000)
  if (min < 1) return 'zojuist'
  if (min < 60) return min + ' min geleden'
  const uur = Math.round(min / 60)
  if (uur < 24) return uur + ' uur geleden'
  const dag = Math.round(uur / 24)
  if (dag < 14) return dag + ' dag' + (dag === 1 ? '' : 'en') + ' geleden'
  return d.toLocaleDateString('nl-NL')
}

async function laad() {
  laden.value = true; fout.value = ''
  try { posts.value = await haalPosts() }
  catch (e) { fout.value = 'Kon de community niet laden: ' + e.message }
  laden.value = false
}
onMounted(laad)

async function plaatsen() {
  const t = tekst.value.trim()
  if (!t) { fout.value = 'Schrijf eerst een bericht.'; return }
  if (bezig.value) return
  bezig.value = true; fout.value = ''; melding.value = ''
  try {
    await plaats(t)
    tekst.value = ''
    melding.value = '✓ Geplaatst in de community'
    await laad()
  } catch (e) { fout.value = 'Plaatsen mislukt: ' + e.message }
  bezig.value = false
}

async function verwijderen(id) {
  if (bezig.value) return
  bezig.value = true; fout.value = ''
  try { await verwijder(id); await laad() }
  catch (e) { fout.value = 'Verwijderen mislukt: ' + e.message }
  bezig.value = false
}
</script>

<template>
  <div>
    <h1>💬 Community</h1>
    <p class="sub">Een besloten tijdlijn — deel tips, vragen en successen met de andere tappunten van je accountmanager.</p>
    <p v-if="fout" class="fout" role="alert" data-test="com-fout">{{ fout }}</p>

    <div v-if="magPlaatsen" class="kaart composer">
      <div class="zh">Plaats een bericht</div>
      <textarea v-model="tekst" rows="3" data-test="com-tekst"
                placeholder="Deel een tip, vraag of succes met andere tappunten…"></textarea>
      <div class="acties">
        <button class="btn" type="button" :disabled="bezig" data-test="com-plaats" @click="plaatsen">
          {{ bezig ? 'Bezig…' : 'Plaatsen' }}
        </button>
        <span v-if="melding" class="melding" role="status" data-test="com-melding">{{ melding }}</span>
      </div>
    </div>
    <div v-else class="kaart mod">
      <span>🛡️ Kantoor modereert deze tijdlijnen. Plaatsen doen partners en accountmanagers binnen hun eigen portefeuille.</span>
    </div>

    <p v-if="laden" class="stil">Laden…</p>
    <p v-else-if="!posts.length" class="stil" data-test="com-leeg">Nog geen berichten. Wees de eerste die iets deelt.</p>

    <div v-for="p in posts" :key="p.id" class="kaart post" data-test="com-post">
      <div class="kop">
        <b>{{ p.author }}</b>
        <span class="rol" :class="'r-' + p.role">{{ ROLLABEL[p.role] || p.role }}</span>
        <span class="tijd">{{ wanneer(p.created_at) }}</span>
        <button v-if="magModereren" class="wis" type="button" :disabled="bezig"
                :data-test="'com-wis-' + p.id" title="Verwijderen" @click="verwijderen(p.id)">🗑</button>
      </div>
      <p class="tekst">{{ p.txt }}</p>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px}
.composer{margin-bottom:14px}
.zh{font-size:12.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--coral-d);margin-bottom:8px}
textarea{width:100%;padding:10px 12px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit;resize:vertical}
textarea:focus{border-color:var(--coral);outline:none}
.acties{display:flex;align-items:center;gap:10px;margin-top:10px}
.btn{background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 16px;font-weight:800;cursor:pointer}
.btn:disabled{opacity:.6}
.melding{color:#2c5a12;font-size:13px}
.mod{margin-bottom:14px;color:var(--grey);font-size:13.5px;background:var(--cream)}
.post{margin-top:10px}
.kop{display:flex;align-items:center;gap:10px}
.kop b{font-size:14.5px}
.rol{font-size:11px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;border-radius:999px;padding:3px 9px;background:var(--soft);color:var(--ink)}
.rol.r-hq{background:var(--coral);color:#fff}
.rol.r-am{background:#e6e2f2;color:#3a2f5a}
.tijd{color:var(--grey);font-size:12px;margin-left:auto}
.wis{background:none;border:0;cursor:pointer;font-size:14px;opacity:.6;padding:2px}
.wis:hover{opacity:1}
.tekst{margin:8px 0 0;line-height:1.5;font-size:14px;white-space:pre-wrap}
.stil{color:var(--grey)}
.fout{color:#b3261e}
</style>
