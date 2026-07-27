<script setup>
// Niveau, status & spaarcadeaus bij één winkel (v71: LEVELS + REWARDS).
// De engine keurt zelf uit: zodra alle eisen + training binnen zijn wordt de
// beloning eenmalig in t.beloond gezet (met viering) en ziet iedereen
// "Van jou!". Kantoor/AM regelt daarna de fysieke uitkering.
import Icoon from '../../../components/Icoon.vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useAuth } from '../../../stores/auth.js'
import { useTappunten } from '../../tappunten/store.js'
import { eur0 } from '../../../lib/format.js'
import { levelOf, statusKey, STATUS, winkelOmzetInfo, jaaromzet, LEVELS } from '../../rekenhart/logic.js'
import { REWARDS, rewUnlocked, rewPct, academyDone, academyPct, cursusNaam, checkBeloningen, inTraject } from '../logic.js'
import { basisScore, totaalScore, BASIS_MAX } from '../../punten/logic.js'
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

// --- v71-beloningsladder: hero, puntentellers, niveau-pad, topbeloningen ---
const jo = computed(() => jaaromzet(t.value))
const bs = computed(() => basisScore(t.value))
const ts = computed(() => totaalScore(t.value))
const belLevels = LEVELS.filter(L => L.bel)        // A+ en A++ (met korting)
const beloond = computed(() => t.value.beloond || {})
const vrijN = computed(() =>
  kaarten.value.filter(k => k.unlocked).length +
  belLevels.filter(L => beloond.value['lvl-' + L.k] || jo.value >= L.min).length)
const totN = REWARDS.length + belLevels.length
const heroPct = computed(() => totN ? Math.round(vrijN.value / totN * 100) : 0)
// Niveau-pad: 6 nodes gelijk verdeeld; de vulling loopt door tot in het
// huidige segment naar rato van de omzet (v71 r.3505).
const padNodes = computed(() => LEVELS.map((L, i) => ({
  k: L.k, min: L.min, left: i * (100 / (LEVELS.length - 1)), done: jo.value >= L.min
})))
const padFill = computed(() => {
  let idx = 0
  LEVELS.forEach((L, i) => { if (jo.value >= L.min) idx = i })
  const L = LEVELS[idx], next = LEVELS[idx + 1]
  const segPct = next ? Math.min((jo.value - L.min) / (next.min - L.min), 1) : 1
  return Math.min((idx + segPct) / (LEVELS.length - 1) * 100, 100)
})
const groeiKaarten = computed(() => belLevels.map(L => ({
  L,
  unlocked: !!beloond.value['lvl-' + L.k] || jo.value >= L.min,
  pct: Math.min(Math.round(jo.value / L.min * 100), 100),
  rest: Math.max(L.min - jo.value, 0)
})))

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
      <h2><Icoon naam="gift" /> Niveau & beloningen</h2>
      <span class="badge" :style="{ background: status.bg, color: status.fg }" data-test="status-badge">{{ status.l }}</span>
      <span class="niveau" data-test="niveau-badge">{{ lv.k }}</span>
    </div>
    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <!-- Hero: beloningsprogramma-overzicht (v71 rewhero) -->
    <div class="rewhero">
      <div class="rewic">🎁</div>
      <div class="rewtxt">
        <div class="eyebrow">Beloningsprogramma</div>
        <h3>Verdien terwijl je groeit</h3>
        <div class="herosub">Je hebt <b>{{ vrijN }} van de {{ totN }}</b> beloningen vrijgespeeld · niveau <b>{{ lv.k }}</b>: {{ lv.r }} · {{ eur0(jo) }} dit jaar</div>
      </div>
      <div class="heroring" data-test="hero-pct">{{ heroPct }}%</div>
    </div>

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

    <!-- Conceptbeloningen -->
    <div class="zh">Conceptbeloningen — verkoop de lifestyle, niet losse flesjes</div>
    <p class="intro">Deze beloningen verdien je met het échte TapParfum-concept: je winkel op orde, vaste klanten die terugkomen om te hervullen, en de beleving verkopen. Alles wordt automatisch gemeten of door je accountmanager goedgekeurd.</p>
    <div class="tellers">
      <div class="teller">
        <div class="tl">Basispunten <span>{{ bs }}/{{ BASIS_MAX }}</span></div>
        <div class="tbar"><i :style="{ width: Math.round(bs / BASIS_MAX * 100) + '%' }"></i></div>
      </div>
      <div class="teller">
        <div class="tl">Totaalpunten <span>{{ ts }}/128</span></div>
        <div class="tbar"><i class="groen" :style="{ width: Math.min(Math.round(ts / 128 * 100), 100) + '%' }"></i></div>
      </div>
    </div>

    <!-- Spaarcadeaus -->
    <div class="cadeaus">
      <div v-for="k in kaarten" :key="k.rw.key" class="cadeau"
           :class="{ unlocked: k.unlocked, next: k.rw.key === volgendeKey }" :data-test="'rew-' + k.rw.key">
        <img v-if="k.rw.foto" class="cfoto" :src="k.rw.foto" :alt="k.rw.r" loading="lazy" :data-test="'rew-foto-' + k.rw.key">
        <!-- Nog geen productfoto? Dan een merkeigen beeldvlak i.p.v. een leeg,
             onaantrekkelijk kaartkopje — elke beloning ziet er even begeerlijk uit. -->
        <div v-else class="cfoto cfoto-ph" :data-test="'rew-ph-' + k.rw.key" aria-hidden="true">
          <span class="phic">{{ k.rw.ic }}</span>
        </div>
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

    <!-- Topbeloningen — voor omzetkampioenen (v71 groeiladder + niveau-pad) -->
    <div class="zh top">Topbeloningen — voor omzetkampioenen</div>
    <p class="intro">Je niveau (D t/m A++) is je omzet-status. Alleen de absolute top verdient er korting mee — de weg ernaartoe loopt via de conceptbeloningen hierboven.</p>

    <div class="lvlpath">
      <div class="track"></div>
      <div class="pfill" :style="{ width: padFill + '%' }"></div>
      <div v-for="n in padNodes" :key="n.k" class="node" :class="{ done: n.done }" :style="{ left: n.left + '%' }">
        <div class="dot">{{ n.k }}</div>
        <div class="lbl">{{ n.min ? eur0(n.min) : 'start' }}</div>
      </div>
    </div>

    <div class="groei">
      <div v-for="g in groeiKaarten" :key="g.L.k" class="gcard" :class="{ unlocked: g.unlocked }" :data-test="'groei-' + g.L.k">
        <div class="gkop"><span class="niveau sm">{{ g.L.k }}</span><b>{{ g.L.bel }}</b>
          <span v-if="g.unlocked" class="won">✓ VRIJGESPEELD</span></div>
        <div class="gsub">{{ g.L.k }} · {{ g.L.r }}</div>
        <div v-if="!g.unlocked" class="geis">○ {{ eur0(g.L.min) }} jaaromzet <b>· nog {{ eur0(g.rest) }}</b></div>
        <div class="voet"><div class="cbalk"><i :style="{ width: g.pct + '%' }"></i></div><span class="pct">{{ g.pct }}%</span></div>
      </div>
    </div>
    <p class="intro slot">Beloningen keert je accountmanager uit. Kortingen gelden op je bestellingen in de 3 maanden na het vrijspelen.</p>
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
.cadeau{border:1px solid var(--line);border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:8px;background:#fff;overflow:hidden}
/* Productfoto van het cadeau — bovenaan de kaart, van rand tot rand */
.cfoto{width:calc(100% + 28px);margin:-14px -14px 0;aspect-ratio:16/10;object-fit:cover;display:block;background:var(--cream)}
/* Merkeigen beeldvlak als er (nog) geen productfoto is: zacht koraal-crème
   verloop met het beloningsicoon groot in beeld — even af als een echte foto. */
.cfoto-ph{display:flex;align-items:center;justify-content:center;
  background:radial-gradient(120% 130% at 28% 18%, var(--soft) 0%, var(--cream) 62%, var(--sand) 100%);
  border-bottom:1px solid var(--line)}
.cfoto-ph .phic{font-size:46px;line-height:1;filter:drop-shadow(0 6px 14px rgba(42,33,28,.16))}
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
/* Hero */
.rewhero{display:flex;align-items:center;gap:16px;flex-wrap:wrap;background:var(--sig);color:#fff;padding:16px 18px;margin-top:12px}
.rewic{width:52px;height:52px;background:rgba(255,255,255,.22);display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0}
.rewtxt{flex:1;min-width:220px}
.eyebrow{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:1.4px;opacity:.9}
.rewhero h3{margin:2px 0 4px;font-size:20px;font-weight:800}
.herosub{font-size:13px;opacity:.96}
.heroring{background:rgba(255,255,255,.92);color:var(--coral-d);font-weight:900;font-size:18px;padding:10px 14px;font-variant-numeric:tabular-nums}
/* Concept/top secties */
.zh{font-size:12px;text-transform:uppercase;letter-spacing:1px;color:var(--coral-d);font-weight:800;margin:18px 0 6px}
.zh.top{margin-top:22px}
.intro{margin:0 0 10px;color:var(--grey);font-size:13px;line-height:1.55}
.intro.slot{margin-top:12px}
.tellers{display:flex;gap:18px;flex-wrap:wrap;margin-bottom:6px}
.teller{flex:1;min-width:180px}
.tl{font-size:12px;font-weight:700;margin-bottom:4px}
.tl span{color:var(--grey)}
.tbar{height:10px;background:#f0ebe3;overflow:hidden}
.tbar i{display:block;height:100%;background:var(--coral)}
.tbar i.groen{background:linear-gradient(90deg,#7fb05a,#3B6D11)}
/* Niveau-pad */
.lvlpath{position:relative;height:56px;margin:10px 4px 26px}
.lvlpath .track{position:absolute;top:11px;left:0;right:0;height:4px;background:#f0ebe3}
.lvlpath .pfill{position:absolute;top:11px;left:0;height:4px;background:var(--coral)}
.node{position:absolute;top:0;transform:translateX(-50%);text-align:center}
.node .dot{width:26px;height:26px;border-radius:50%;background:#fff;border:2px solid var(--line);color:var(--grey);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:11px;margin:0 auto}
.node.done .dot{background:var(--coral);border-color:var(--coral);color:#fff}
.node .lbl{font-size:10px;color:var(--grey);margin-top:4px;font-weight:700;white-space:nowrap}
/* Groei-kaarten */
.groei{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.gcard{border:1px solid var(--line);padding:14px;display:flex;flex-direction:column;gap:6px;background:#fff}
.gcard.unlocked{border-color:#bcd9a0;background:linear-gradient(180deg,#fbfdf8,#fff)}
.gkop{display:flex;align-items:center;gap:8px}
.niveau.sm{width:26px;height:26px;border-radius:8px;font-size:11px}
.gkop b{font-size:13px;flex:1}
.gsub{font-size:11.5px;color:var(--grey)}
.geis{font-size:11.5px;font-weight:600}
.geis b{color:var(--coral-d)}
</style>
