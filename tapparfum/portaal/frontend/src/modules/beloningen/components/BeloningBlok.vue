<script setup>
// Niveau, status & spaarcadeaus bij één winkel (v71: LEVELS + REWARDS).
// De engine keurt zelf uit: zodra alle eisen + training binnen zijn wordt de
// beloning eenmalig in t.beloond gezet (met viering) en ziet iedereen
// "Van jou!". Kantoor/AM regelt daarna de fysieke uitkering.
import { computed, onMounted, ref, watch } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { eur0 } from '../../../lib/format.js'
import { levelOf, statusKey, STATUS, winkelOmzetInfo, jaaromzet } from '../../rekenhart/logic.js'
import { REWARDS, rewUnlocked, rewPct, academyDone, academyPct, cursusNaam, checkBeloningen, inTraject } from '../logic.js'
import { haalRekenConfig } from '../api.js'
import { stuurWinkelvraag } from '../../winkelvragen/api.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const emit = defineEmits(['bijgewerkt'])
const auth = useAuth()
const st = useTappunten()
const fout = ref('')
const marge = ref(1)
const maten = ref([])
const geladen = ref(false)
const netUitgekeerd = ref([])   // vieringsbanner voor deze sessie

const t = computed(() => props.tappunt)
const lv = computed(() => levelOf(jaaromzet(t.value), marge.value))
const status = computed(() => STATUS[statusKey(t.value, marge.value)] || STATUS.groeit)
const wo = computed(() => winkelOmzetInfo(t.value, marge.value, maten.value))
const bronTekst = { kassa: 'uit de kassa', teller: 'uit de flessenteller' }

const kaarten = computed(() => REWARDS.map(rw => ({
  rw,
  unlocked: rewUnlocked(t.value, rw) || !!(t.value.beloond || {})[rw.key],
  datum: (t.value.beloond || {})[rw.key] || null,
  pct: rewPct(t.value, rw),
  eisen: rw.eisen.map(e => ({ txt: e.txt, ok: e.ok(t.value), rest: e.ok(t.value) ? '' : e.rest(t.value) })),
  cursusOk: !rw.cursus || academyDone(t.value, rw.cursus),
  cursusNaam: rw.cursus ? cursusNaam(rw.cursus) : '',
  cursusPct: rw.cursus ? academyPct(t.value, rw.cursus) : 100
})))
// De eerstvolgende (nog niet vrijgespeelde) beloning krijgt de gloed.
const volgendeKey = computed(() => {
  const open = kaarten.value.filter(k => !k.unlocked)
  if (!open.length) return null
  return open.reduce((a, b) => (b.pct > a.pct ? b : a)).rw.key
})

// Voortgang niveau-balk: hoe ver zit de winkelomzet tussen huidige en volgende drempel?
const nivoPct = computed(() => {
  if (!lv.value.nextMin) return 100
  const start = lv.value.min
  return Math.max(0, Math.min(100, ((wo.value.bedrag - start) / (lv.value.nextMin - start)) * 100))
})

/* Vangnet (v71 checkBeloningenAll): groei-eisen verschuiven met de tijd, dus we
   lopen de engine na bij elke keer dat deze winkel in beeld komt of wijzigt. */
async function keurUit() {
  if (!geladen.value) return
  const res = checkBeloningen(t.value, marge.value)
  if (!res) return
  try {
    await st.bewaar(res.t2)
    emit('bijgewerkt', res.t2)
    netUitgekeerd.value = res.nieuw
    // Melding op de berichtlijn ("regel de uitkering") — best effort: de RLS
    // laat alleen de partner zelf en kantoor hier insturen.
    if (auth.isPartner || auth.isKantoor) {
      for (const n of res.nieuw) {
        try {
          await stuurWinkelvraag({ tappunt_snelstart: t.value.snelstart, type: 'mijlpaal', txt: `Beloning vrijgespeeld (${n.bron}): ${n.r} — regel de uitkering.` })
        } catch { /* melding is een extraatje; de uitkering zelf staat al vast */ }
      }
    }
  } catch (e) { fout.value = 'Uitkering opslaan mislukte: ' + e.message }
}

onMounted(async () => {
  try { const c = await haalRekenConfig(); marge.value = c.marge; maten.value = c.maten }
  catch { /* zonder config rekenen we met factor 1 en standaardmaten */ }
  geladen.value = true
  await keurUit()
})
watch(() => props.tappunt, keurUit)
</script>

<template>
  <section v-if="inTraject(t)" class="blok">
    <div class="kop">
      <h2>🎁 Niveau & beloningen</h2>
      <span class="badge" :style="{ background: status.bg, color: status.fg }" data-test="status-badge">{{ status.l }}</span>
      <span class="niveau" data-test="niveau-badge">{{ lv.k }}</span>
    </div>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Niveau-kaart -->
    <div class="nivo">
      <p class="regel"><b>Niveau {{ lv.k }}</b> — {{ lv.r }}</p>
      <p class="mo">Winkelomzet dit jaar: <b data-test="wo-bedrag">{{ eur0(wo.bedrag) }}</b>
        {{ ' ' }}<span class="bron">({{ wo.bron === 'schatting' ? `schatting: inkoop × ${String(marge).replace('.', ',')}` : bronTekst[wo.bron] }})</span>
        · inkoop bij TapParfum: {{ eur0(jaaromzet(t)) }}</p>
      <template v-if="lv.next">
        <div class="balk"><div class="vul" :style="{ width: nivoPct + '%' }"></div></div>
        <p class="mo">Nog <b>{{ eur0(lv.gap) }}</b> tot niveau {{ lv.next }}<template v-if="lv.nextR"> — {{ lv.nextR }}</template></p>
      </template>
      <p v-else class="mo">🏆 Hoogste niveau bereikt.</p>
      <p v-if="lv.bel" class="mo top">🎉 Niveaubeloning actief: {{ lv.bel }}</p>
    </div>

    <!-- Zojuist vrijgespeeld -->
    <div v-for="n in netUitgekeerd" :key="n.key" class="viering" role="status" data-test="viering">
      🎉 Beloning vrijgespeeld ({{ n.bron }}): <b>{{ n.r }}</b> — kantoor/AM regelt de uitkering.
    </div>

    <!-- Spaarcadeaus -->
    <div class="cadeaus">
      <div v-for="k in kaarten" :key="k.rw.key" class="cadeau"
           :class="{ unlocked: k.unlocked, next: k.rw.key === volgendeKey }" :data-test="'rew-' + k.rw.key">
        <div class="ckop">
          <span class="ic" aria-hidden="true">{{ k.rw.ic }}</span>
          <span class="chip">{{ k.rw.chip }}</span>
          <span v-if="k.unlocked" class="won" :data-test="'rew-won-' + k.rw.key">✓ VRIJGESPEELD</span>
          <span v-else-if="k.rw.key !== volgendeKey" class="slot" aria-label="nog vergrendeld">🔒</span>
        </div>
        <div class="titel">{{ k.rw.r }}</div>
        <div class="sub">{{ k.rw.sub }}</div>
        <div class="eisen">
          <div v-for="e in k.eisen" :key="e.txt" class="eis" :class="{ ok: e.ok }">
            <span class="vink">{{ e.ok ? '✓' : '○' }}</span>
            <span>{{ e.txt }}<b v-if="e.rest"> · {{ e.rest }}</b></span>
          </div>
          <div v-if="k.rw.cursus" class="eis" :class="{ ok: k.cursusOk }">
            <span class="vink">{{ k.cursusOk ? '✓' : '○' }}</span>
            <span>🎓 {{ k.cursusNaam }}<b v-if="!k.cursusOk"> · {{ k.cursusPct }}% af</b></span>
          </div>
        </div>
        <div v-if="k.unlocked" class="voet won-voet">Van jou!<template v-if="k.datum && k.datum !== 'import'"> · {{ k.datum }}</template></div>
        <div v-else class="voet">
          <div class="cbalk"><i :style="{ width: k.pct + '%' }"></i></div>
          <span class="pct" :data-test="'rew-pct-' + k.rw.key">{{ k.pct }}%</span>
        </div>
      </div>
    </div>
  </section>
</template>


<style scoped>
.blok{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-top:14px}
.kop{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
h2{margin:0;font-size:16px;flex:1}
.badge{font-size:11.5px;font-weight:800;border-radius:6px;padding:3px 10px}
.niveau{width:34px;height:34px;border-radius:10px;background:var(--coral);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:14px}
.nivo{background:var(--cream);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-top:12px}
.regel{margin:0;font-size:14px}
.mo{color:var(--grey);font-size:12.5px;margin:5px 0 0}
.mo b{color:var(--ink)}
.mo.top{color:#2c5a12;font-weight:700}
.bron{font-size:11.5px}
.balk{height:8px;border-radius:6px;background:#f0ebe3;overflow:hidden;margin:8px 0 0}
.vul{height:100%;background:var(--coral)}
.viering{background:var(--green-soft);border:1px solid #bcd9a0;color:#2c5a12;border-radius:12px;padding:10px 14px;margin-top:12px;font-size:13.5px}
.cadeaus{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin-top:14px}
.cadeau{border:1px solid var(--line);border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:8px;background:#fff}
.cadeau.next{border-color:var(--coral);box-shadow:0 0 0 3px var(--soft)}
.cadeau.unlocked{border-color:#bcd9a0;background:linear-gradient(180deg,#fbfdf8,#fff)}
.ckop{display:flex;align-items:center;gap:8px}
.ic{font-size:22px}
.chip{background:var(--soft);color:var(--coral-d);font-size:11px;font-weight:800;border-radius:999px;padding:3px 10px}
.won{margin-left:auto;color:#2c5a12;background:var(--green-soft);font-size:10.5px;font-weight:900;border-radius:6px;padding:3px 8px;letter-spacing:.05em}
.slot{margin-left:auto;opacity:.5}
.titel{font-weight:800;font-size:13.5px;line-height:1.35}
.sub{font-size:11.5px;color:var(--grey);line-height:1.4}
.eisen{display:flex;flex-direction:column;gap:4px}
.eis{display:flex;gap:7px;font-size:11.5px;line-height:1.4;font-weight:600}
.eis .vink{color:#c9c0b2;font-weight:800;flex-shrink:0}
.eis.ok{color:var(--grey);font-weight:400}
.eis.ok .vink{color:var(--green)}
.eis b{color:var(--coral-d)}
.voet{display:flex;align-items:center;gap:8px;margin-top:auto}
.won-voet{color:#2c5a12;font-weight:800;font-size:12.5px}
.cbalk{flex:1;height:7px;border-radius:6px;background:#f0ebe3;overflow:hidden}
.cbalk i{display:block;height:100%;background:var(--coral)}
.pct{font-size:11.5px;font-weight:800;color:var(--grey);font-variant-numeric:tabular-nums}
.fout{color:#b3261e;font-size:13px}
</style>
