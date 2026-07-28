<script setup>
// Bestellen — de v71-pakketcatalogus voor partners (en AM/kantoor als
// naslagwerk in het verkoopgesprek): startpakketten per segment, uitbreidingen
// (bijproducten) en per pakket de volledige stuklijst incl. gratis materialen.
// Bestellen zelf gebeurt in het bestelportaal (central shopUrl).
import Icoon from '../../../components/Icoon.vue'
import { onMounted, ref } from 'vue'
import { eur0 } from '../../../lib/format.js'
import { haalCentral } from '../../beheer/api.js'
import { PAKKETTEN, BIJPRODUCTEN, PAK_BOM, pakSamenstelling, pakBtw } from '../data.js'

const shopUrl = ref('')
const open = ref(null)          // pakketnaam waarvan de stuklijst open staat
const fotoFout = ref({})        // producten waarvan de foto niet laadt -> merkvlak

// Echte productfoto's hergebruiken waar ze eerlijk passen (bijproducten met een
// eigen productlijn). De geuren-startpakketten krijgen een merkvlak met het
// geuren-aantal groot in beeld — de landingspagina-look, zonder misleidende foto.
const FOTO = {
  'Bodyspray — 10 geuren': '/assets/bodymist.jpg',
  'Bodyspray — 20 geuren': '/assets/bodymist.jpg',
  'Candle — 12 geuren (6 st.)': '/assets/kaarsen-selflove.jpg',
  'Candle — 12 geuren (2 st.)': '/assets/kaarsen-selflove.jpg',
  'Home — Reed & Homespray': '/assets/home-selflove.jpg',
  'Home — Reed Diffuser': '/assets/home-selflove.jpg',
  'Home — Homespray': '/assets/home-selflove.jpg'
}
const foto = (naam) => (!fotoFout.value[naam] && FOTO[naam]) || ''

onMounted(async () => {
  try { shopUrl.value = String(await haalCentral('shopUrl') || '') } catch { /* knop blijft weg */ }
})

const eur = (v) => eur0(v).replace(',00', '')
function bom(naam) { return PAK_BOM[naam] || null }
// Samenstelling-strook (v71): geuren/Exclusive/regulier · incl. btw · per geur.
function samenvatting(naam, prijs) {
  const s = pakSamenstelling(naam)
  return { ...s, incl: pakBtw(prijs), perGeur: s.tot ? Math.round(prijs / s.tot) : null }
}
</script>

<template>
  <div>
    <header class="vheld"><div>
      <p class="eyebrow">Assortiment</p>
      <h1><Icoon naam="bestellen" /> Bestellen</h1>
      <p class="sub">De startpakketten en uitbreidingen — met per pakket precies wat je krijgt (prijzen excl. btw). Bestellen doe je in het bestelportaal.</p>
    </div>
      <a v-if="shopUrl" class="btn portaal" :href="shopUrl" target="_blank" rel="noopener noreferrer" data-test="shop-knop">Naar het bestelportaal →</a>
      <p v-else class="mo">Het bestelportaal is nog niet gekoppeld — kantoor stelt de link in bij Beheer → Instellingen.</p>
    </header>

    <template v-for="seg in PAKKETTEN" :key="seg.seg">
      <h2 :data-test="'seg-' + seg.seg">{{ seg.seg }}</h2>
      <div class="grid">
        <div v-for="[naam, prijs] in seg.items" :key="naam" class="pak" :data-test="'pak-' + naam">
          <img v-if="foto(naam)" class="pfoto" :src="foto(naam)" :alt="naam" loading="lazy" @error="fotoFout[naam] = true">
          <div v-else class="pfoto pfoto-ph" aria-hidden="true">
            <b v-if="samenvatting(naam, prijs).tot">{{ samenvatting(naam, prijs).tot }}</b>
            <span>{{ samenvatting(naam, prijs).tot ? 'geuren' : naam }}</span>
          </div>
          <div class="pkop">
            <b>{{ naam }}</b>
            <span class="prijs">{{ eur(prijs) }}</span>
          </div>
          <div class="samenvat" :data-test="'samenvat-' + naam">
            <span v-if="samenvatting(naam, prijs).tot" class="chip">🧴 {{ samenvatting(naam, prijs).tot }} geuren<template v-if="samenvatting(naam, prijs).exc"> · {{ samenvatting(naam, prijs).exc }} Exclusive + {{ samenvatting(naam, prijs).reg }} regulier</template></span>
            <span class="chip">{{ eur(prijs) }} excl. · <b>{{ eur(samenvatting(naam, prijs).incl) }}</b> incl. btw</span>
            <span v-if="samenvatting(naam, prijs).perGeur" class="chip">≈ {{ eur(samenvatting(naam, prijs).perGeur) }} per geur</span>
          </div>
          <button v-if="bom(naam)" class="klein" type="button" :data-test="'bom-knop-' + naam"
                  @click="open = open === naam ? null : naam">
            {{ open === naam ? 'Verberg inhoud ▴' : 'Wat zit erin? ▾' }}
          </button>
          <div v-if="open === naam && bom(naam)" class="bom" :data-test="'bom-' + naam">
            <h3>Inhoud</h3>
            <div v-for="[item, n] in bom(naam).i" :key="'i' + item" class="regel">
              <span class="n">{{ n != null ? n + '×' : '' }}</span><span>{{ item }}</span>
            </div>
            <template v-if="bom(naam).g && bom(naam).g.length">
              <h3 class="gratis">🎁 Gratis erbij</h3>
              <div v-for="[item, n] in bom(naam).g" :key="'g' + item" class="regel gratis">
                <span class="n">{{ n != null ? n + '×' : '' }}</span><span>{{ item }}</span>
              </div>
            </template>
            <p class="totaal">Pakketprijs: <b>{{ eur(bom(naam).t) }}</b> excl. btw</p>
          </div>
        </div>
      </div>
    </template>

    <h2>Uitbreidingen & modules</h2>
    <div class="grid">
      <div v-for="[naam, prijs] in BIJPRODUCTEN" :key="naam" class="pak" data-test="bijproduct">
        <img v-if="foto(naam)" class="pfoto" :src="foto(naam)" :alt="naam" loading="lazy" @error="fotoFout[naam] = true">
        <div v-else class="pfoto pfoto-ph" aria-hidden="true">
          <b v-if="samenvatting(naam, prijs).tot">{{ samenvatting(naam, prijs).tot }}</b>
          <span>{{ samenvatting(naam, prijs).tot ? 'geuren' : naam }}</span>
        </div>
        <div class="pkop">
          <b>{{ naam }}</b>
          <span class="prijs">{{ eur(prijs) }}</span>
        </div>
        <div class="samenvat">
          <span class="chip">{{ eur(prijs) }} excl. · <b>{{ eur(samenvatting(naam, prijs).incl) }}</b> incl. btw</span>
        </div>
        <button v-if="bom(naam)" class="klein" type="button" @click="open = open === naam ? null : naam">
          {{ open === naam ? 'Verberg inhoud ▴' : 'Wat zit erin? ▾' }}
        </button>
        <div v-if="open === naam && bom(naam)" class="bom">
          <h3>Inhoud</h3>
          <div v-for="[item, n] in bom(naam).i" :key="'i' + item" class="regel">
            <span class="n">{{ n != null ? n + '×' : '' }}</span><span>{{ item }}</span>
          </div>
          <template v-if="bom(naam).g && bom(naam).g.length">
            <h3 class="gratis">🎁 Gratis erbij</h3>
            <div v-for="[item, n] in bom(naam).g" :key="'g' + item" class="regel gratis">
              <span class="n">{{ n != null ? n + '×' : '' }}</span><span>{{ item }}</span>
            </div>
          </template>
          <p class="totaal">Prijs: <b>{{ eur(bom(naam).t) }}</b> excl. btw</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
h2{margin:20px 0 10px;font-size:13px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--grey)}
h3{margin:10px 0 4px;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--grey)}
h3.gratis{color:#2c5a12}
.sub{color:var(--grey);margin:0 0 12px;font-size:13.5px}
.btn.portaal{display:inline-block;background:var(--coral);color:#fff;border-radius:10px;padding:10px 18px;font-weight:800;text-decoration:none;margin-bottom:6px}
.mo{color:var(--grey);font-size:12.5px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.pak{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:8px;overflow:hidden}
/* Beeld-/merkvlak bovenaan de kaart, van rand tot rand (landingspagina-look) */
.pfoto{width:calc(100% + 28px);margin:-14px -14px 0;aspect-ratio:16/10;object-fit:cover;display:block;background:var(--cream)}
.pfoto-ph{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0;
  background:radial-gradient(120% 130% at 28% 18%, var(--soft) 0%, var(--cream) 62%, var(--sand) 100%);
  border-bottom:1px solid var(--line);color:var(--coral-d);text-align:center;padding:6px}
.pfoto-ph b{font-family:var(--font-display);font-weight:500;font-size:38px;line-height:1;letter-spacing:.02em}
.pfoto-ph span{font-size:11px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--grey);margin-top:3px;max-width:90%}
.pkop{display:flex;align-items:baseline;gap:10px}
.pkop b{flex:1;font-size:13.5px;line-height:1.35}
.prijs{font-weight:800;color:var(--coral-d);font-variant-numeric:tabular-nums;white-space:nowrap}
.samenvat{display:flex;flex-wrap:wrap;gap:6px}
.samenvat .chip{background:var(--cream);border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:11px;font-weight:600;color:var(--grey)}
.samenvat .chip b{color:var(--ink)}
.klein{align-self:flex-start;background:none;border:1.5px solid var(--line);border-radius:8px;padding:4px 11px;font-size:12px;font-weight:700;color:var(--grey);cursor:pointer}
.klein:hover{border-color:var(--coral);color:var(--coral-d)}
.bom{border-top:1px solid var(--line);padding-top:6px}
.regel{display:flex;gap:8px;font-size:12px;padding:2px 0;color:var(--ink)}
.regel.gratis{color:#2c5a12}
.n{width:38px;flex-shrink:0;font-weight:700;color:var(--grey);font-variant-numeric:tabular-nums;text-align:right}
.totaal{margin:10px 0 0;font-size:12.5px;color:var(--grey)}
</style>
