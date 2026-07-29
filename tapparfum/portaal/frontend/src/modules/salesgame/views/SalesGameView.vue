<script setup>
// Sales Game — de jaarwedstrijd. Kantoor stelt hem in (central 'salesgame');
// AM/kantoor zien het groei- en nieuwkomers-klassement over hun winkels;
// de partner ziet zijn eigen score, positie en of hij gekwalificeerd is
// (geen andere winkels — dat zou RLS/privacy schenden).
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { eur0 } from '../../../lib/format.js'
import { haalCentral, bewaarCentral } from '../../beheer/api.js'
import { jaaromzet } from '../../rekenhart/logic.js'
import { gameKlassement, gamePositie, gameDagen, gameScoreVan } from '../logic.js'
import { haalGameBoard } from '../api.js'

const auth = useAuth()
const st = useTappunten()
const sg = ref(null)
const fout = ref('')
const melding = ref('')
const bezig = ref(false)
const vorm = reactive({ actief: false, titel: '', prijs: '', waarde: '', eind: '', minPunten: 0, minBasis: 0, regels: '' })

const board = ref(null)   // landelijk klassement (RPC) of null bij terugval

onMounted(async () => {
  try {
    if (!st.items.length) await st.laad()
    sg.value = (await haalCentral('salesgame')) || null
    if (sg.value) Object.assign(vorm, { ...vorm, ...sg.value })
    // Landelijk aggregaat ophalen zodra de game actief is; faalt dit (nog niet
    // gedeployed), dan blijft board null en rekent de view lokaal verder.
    if (sg.value && sg.value.actief) {
      try { board.value = await haalGameBoard({ minPunten: sg.value.minPunten, minBasis: sg.value.minBasis }) }
      catch { board.value = null }
    }
  } catch (e) { fout.value = 'Kon de Sales Game niet laden: ' + e.message }
})

const dagen = computed(() => gameDagen(sg.value))
const eigen = computed(() => auth.isPartner ? (st.items[0] || null) : null)
const mijnScore = computed(() => eigen.value ? gameScoreVan(eigen.value) : null)

// Eén genormaliseerd klassement — landelijk (RPC) heeft voorrang, anders lokaal.
const klas = computed(() => {
  if (board.value) {
    const m = r => ({ naam: r.naam, score: r.score, groeiPct: r.groei_pct == null ? null : Number(r.groei_pct), jo: Number(r.jo), isZelf: r.is_zelf })
    const groei = board.value.filter(r => r.klasse === 'groei').sort((a, b) => a.rang - b.rang).map(m)
    const nieuw = board.value.filter(r => r.klasse === 'nieuw').sort((a, b) => a.rang - b.rang).map(m)
    return { groei, nieuw, landelijk: true, zelf: board.value.find(r => r.is_zelf) || null }
  }
  const k = gameKlassement(sg.value, st.items)
  if (!k) return null
  const m = x => ({ naam: x.t.name, score: x.sc.score, groeiPct: x.sc.groeiPct, jo: x.jo != null ? x.jo : jaaromzet(x.t), isZelf: false })
  return { groei: k.groei.map(m), nieuw: k.nieuw.map(m), landelijk: false, _k: k }
})

const podium = computed(() => {
  if (!klas.value) return []
  return (klas.value.groei.length ? klas.value.groei : klas.value.nieuw).slice(0, 3)
})
const podiumIsGroei = computed(() => !!(klas.value && klas.value.groei.length))

const mijnPositie = computed(() => {
  if (!klas.value) return null
  if (klas.value.landelijk) {
    const z = klas.value.zelf
    if (!z) return null
    if (z.klasse === 'nietq') return { kl: 'nietq', reden: z.reden, tekort: Number(z.tekort) || 0 }
    const van = z.klasse === 'groei' ? klas.value.groei.length : klas.value.nieuw.length
    return { kl: z.klasse, pos: Number(z.rang), van }
  }
  return eigen.value ? gamePositie(klas.value._k, eigen.value.snelstart) : null
})

async function opslaan() {
  if (bezig.value) return
  bezig.value = true; fout.value = ''; melding.value = ''
  try {
    const g = {
      actief: !!vorm.actief, titel: vorm.titel.trim() || 'TapParfum Sales Game',
      prijs: vorm.prijs.trim(), waarde: parseInt(String(vorm.waarde).replace(/[^\d]/g, '')) || 0,
      eind: vorm.eind || '', minPunten: Math.max(0, parseInt(vorm.minPunten) || 0),
      minBasis: Math.max(0, parseInt(vorm.minBasis) || 0), regels: vorm.regels.trim()
    }
    await bewaarCentral('salesgame', g)
    sg.value = g
    melding.value = g.actief ? '✓ Sales Game staat live — zichtbaar voor AM\'s en partners.' : '✓ Opgeslagen (game staat uit).'
  } catch (e) { fout.value = 'Opslaan mislukt: ' + e.message }
  bezig.value = false
}
</script>

<template>
  <div>
    <h1>🏆 Sales Game</h1>

    <!-- Kantoor: instellen -->
    <form v-if="auth.magBeheer" class="kaart vorm" @submit.prevent="opslaan">
      <h2>Instellen</h2>
      <label class="schakel"><input type="checkbox" v-model="vorm.actief" data-test="game-actief" /> Game staat live</label>
      <div class="rij">
        <label>Titel<input v-model="vorm.titel" placeholder="TapParfum Sales Game" data-test="game-titel" /></label>
        <label>Prijs<input v-model="vorm.prijs" placeholder="bijv. weekendje weg" /></label>
        <label>Waarde (€)<input v-model="vorm.waarde" type="number" min="0" /></label>
      </div>
      <div class="rij">
        <label>Einddatum<input v-model="vorm.eind" type="date" /></label>
        <label>Min. totaalpunten<input v-model="vorm.minPunten" type="number" min="0" data-test="game-minp" /></label>
        <label>Min. basis vorig jaar (€)<input v-model="vorm.minBasis" type="number" min="0" /></label>
      </div>
      <label>Spelregels<textarea v-model="vorm.regels" rows="2"></textarea></label>
      <div class="acties">
        <button class="btn" type="submit" :disabled="bezig" data-test="game-opslaan">Opslaan</button>
        <span v-if="melding" class="melding" role="status">{{ melding }}</span>
      </div>
    </form>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Niet actief -->
    <p v-if="!sg || !sg.actief" class="stil" data-test="game-uit">De Sales Game staat nu niet aan.{{ auth.magBeheer ? ' Zet hem hierboven live.' : '' }}</p>

    <template v-else>
      <!-- Hero -->
      <div class="hero" data-test="game-hero">
        <div class="hkop"><b>{{ sg.titel }}</b><span v-if="dagen != null" class="dagen">{{ dagen }} dagen te gaan</span></div>
        <p v-if="sg.prijs" class="prijs">🎁 {{ sg.prijs }}<template v-if="sg.waarde"> · t.w.v. {{ eur0(sg.waarde) }}</template></p>
        <p v-if="sg.regels" class="regels">{{ sg.regels }}</p>

        <!-- Podium -->
        <div v-if="podium.length" class="podium">
          <div v-for="(x, i) in podium" :key="i" class="plek" :class="'p' + i" :data-test="'podium-' + i">
            <div class="medal">{{ ['🥇','🥈','🥉'][i] }}</div>
            <div class="pnaam">{{ x.naam }}</div>
            <div class="pscore">{{ podiumIsGroei ? x.score + ' ptn' + (x.groeiPct != null ? ' · +' + x.groeiPct + '%' : '') : eur0(x.jo) + ' omzet' }}</div>
            <div class="staaf" :style="{ height: [58, 42, 30][i] + 'px' }">{{ i + 1 }}</div>
          </div>
        </div>
        <p class="klas-lbl">{{ podiumIsGroei ? 'Groei-klassement' : '🌱 Nieuwkomers van het jaar' }}<template v-if="klas && klas.landelijk"> · landelijk</template></p>
      </div>

      <!-- Partner: eigen positie -->
      <div v-if="auth.isPartner && mijnScore" class="kaart eigen" data-test="game-mijn">
        <h2>Jullie stand</h2>
        <p class="regel">Score: <b>{{ mijnScore.score }} punten</b>
          <template v-if="mijnScore.groeiPct != null"> · groei <b>+{{ mijnScore.groeiPct }}%</b></template>
          · {{ mijnScore.acties }} acties · bonus {{ mijnScore.bonus }}</p>
        <p v-if="mijnPositie && mijnPositie.kl === 'groei'" class="regel groen">🏆 Positie {{ mijnPositie.pos }} van {{ mijnPositie.van }} in het groei-klassement.</p>
        <p v-else-if="mijnPositie && mijnPositie.kl === 'nieuw'" class="regel groen">🌱 Positie {{ mijnPositie.pos }} van {{ mijnPositie.van }} bij de nieuwkomers.</p>
        <p v-else-if="mijnPositie && mijnPositie.kl === 'nietq'" class="regel amber">
          Nog niet gekwalificeerd{{ mijnPositie.reden === 'punten' ? ` — nog ${mijnPositie.tekort} totaalpunten te gaan!` : ' (te kleine basis vorig jaar).' }}
        </p>
      </div>

      <!-- AM/kantoor: volledig klassement (landelijk indien beschikbaar) -->
      <div v-if="!auth.isPartner && klas" class="kaart">
        <h2>Groei-klassement<span v-if="klas.landelijk" class="landelijk"> · landelijk</span></h2>
        <div v-for="(x, i) in klas.groei" :key="i" class="rijk" :class="{ zelf: x.isZelf }" data-test="klas-groei">
          <span class="pos">{{ i + 1 }}</span><b>{{ x.naam }}</b>
          <span class="mo">{{ x.score }} ptn<template v-if="x.groeiPct != null"> · +{{ x.groeiPct }}%</template></span>
        </div>
        <p v-if="!klas.groei.length" class="stil">Nog geen gekwalificeerde winkels.</p>
        <template v-if="klas.nieuw.length">
          <h2 style="margin-top:16px">🌱 Nieuwkomers</h2>
          <div v-for="(x, i) in klas.nieuw" :key="i" class="rijk" :class="{ zelf: x.isZelf }" data-test="klas-nieuw">
            <span class="pos">{{ i + 1 }}</span><b>{{ x.naam }}</b><span class="mo">{{ eur0(x.jo) }} omzet</span>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<style scoped>
h1{margin:0 0 10px;font-size:22px}
h2{margin:0 0 10px;font-size:15px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.vorm{display:flex;flex-direction:column;gap:10px}
.rij{display:flex;gap:12px;flex-wrap:wrap}
label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;font-weight:700;color:var(--grey);flex:1;min-width:120px}
.schakel{flex-direction:row;align-items:center;gap:8px}
input,textarea{padding:9px 11px;border:1.5px solid var(--line);border-radius:10px;font-size:14px;font-family:inherit}
input:focus,textarea:focus{border-color:var(--coral)}
.btn{align-self:flex-start;background:var(--coral);color:#fff;border:0;border-radius:10px;padding:9px 16px;font-weight:800;cursor:pointer}
.btn:disabled{opacity:.6}
.acties{display:flex;align-items:center;gap:10px}
.melding{color:#2c5a12;font-size:13px}
.hero{background:linear-gradient(135deg,var(--coral),var(--coral-d));color:#fff;border-radius:18px;padding:20px 22px;margin-bottom:14px}
.hkop{display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap}
.hkop b{font-size:19px}
.dagen{background:rgba(255,255,255,.25);border-radius:999px;padding:3px 12px;font-size:12px;font-weight:800}
.prijs{margin:6px 0 0;font-weight:700}
.regels{margin:6px 0 0;font-size:13px;opacity:.9}
.podium{display:flex;gap:12px;justify-content:center;align-items:flex-end;margin-top:16px;flex-wrap:wrap}
.plek{text-align:center;min-width:92px}
.plek.p0{order:2}.plek.p1{order:1}.plek.p2{order:3}
.medal{font-size:30px}
.plek.p0 .medal{font-size:38px}
.pnaam{font-weight:800;font-size:13px;max-width:120px;margin:0 auto}
.pscore{font-size:12px;font-weight:700;opacity:.9}
.staaf{width:78px;margin:8px auto 0;background:linear-gradient(180deg,rgba(255,255,255,.55),rgba(255,255,255,.26));border-radius:10px 10px 0 0;display:flex;align-items:flex-start;justify-content:center;padding-top:5px;color:#fff;font-weight:900;font-size:15px;box-shadow:inset 0 1px 0 rgba(255,255,255,.65),0 6px 14px -8px rgba(0,0,0,.4);font-variant-numeric:tabular-nums}
.plek.p0 .staaf{background:linear-gradient(180deg,rgba(255,255,255,.72),rgba(255,255,255,.34))}
.klas-lbl{text-align:center;font-size:10.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;opacity:.9;margin:8px 0 0}
.eigen .regel{margin:4px 0;font-size:14px}
.regel.groen{color:#2c5a12;font-weight:700}
.regel.amber{color:#8a6210;font-weight:700}
.rijk{display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--line);font-size:14px}
.rijk:last-child{border-bottom:0}
.rijk.zelf{background:var(--soft);border-radius:8px;padding-left:6px;padding-right:6px}
.landelijk{font-size:11px;font-weight:800;color:var(--coral-d);letter-spacing:.04em}
.pos{width:26px;height:26px;flex-shrink:0;border-radius:8px;background:var(--soft);color:var(--coral-d);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px}
.mo{margin-left:auto;color:var(--grey);font-size:13px}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
