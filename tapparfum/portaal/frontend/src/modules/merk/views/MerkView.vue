<script setup>
// Merk & Assets (v71 VIEWS.merk) — de merkwereld, de productfotografie en de
// downloadbare materialen. De merkvideo's staan bewust in de Academy
// (videotheek): daar wordt geleerd, hier wordt gedownload.
import Icoon from '../../../components/Icoon.vue'
import { ref } from 'vue'
import { MERKWERELD, MERK_ASSETS, MERKREGELS, PRODUCT_FOTOS } from '../data.js'
const melding = ref('')
function download() {
  melding.value = 'Download volgt zodra de portal online staat.'
  setTimeout(() => { melding.value = '' }, 2500)
}
</script>

<template>
  <div>
    <h1><Icoon naam="merk" /> Merk &amp; Assets</h1>
    <p class="sub">Officiële logo’s, kleuren en materialen — alles om TapParfum consistent neer te zetten. De merkvideo's vind je in de <router-link :to="{ name: 'academy' }">Academy</router-link>.</p>

    <div class="blk-t">De merkwereld van TapParfum</div>
    <div class="wereld">
      <div v-for="m in MERKWERELD" :key="m.t" class="mcard" :style="{ background: m.bg }" data-test="merkwereld-kaart">
        <span class="mic">{{ m.ic }}</span>
        <div class="mlab">{{ m.t }}<small>{{ m.cat }}</small></div>
      </div>
    </div>

    <!-- Laag 2: de producten — gewoon het artikel laten zien -->
    <div class="blk-t">De producten in beeld</div>
    <p class="uitleg">Officiële productfotografie uit de sell-sheets — voor je eigen posts, schapkaartjes of etalage. Klik op Download voor het originele bestand.</p>
    <div class="prods">
      <figure v-for="p in PRODUCT_FOTOS" :key="p.src" class="pcard" data-test="merk-product">
        <img :src="p.src" :alt="p.t" loading="lazy">
        <figcaption>
          <div class="mlab">{{ p.t }}<small>{{ p.sub }}</small></div>
          <a class="btn ghost dl" :href="p.src" download>Download</a>
        </figcaption>
      </figure>
    </div>

    <div class="blk-t">Materialen</div>
    <div class="assets">
      <div v-for="a in MERK_ASSETS" :key="a.t" class="asset" data-test="merk-asset">
        <div class="alabel" :style="{ background: a.bg, color: a.fg }">{{ a.label }}</div>
        <div class="arow">
          <div><b>{{ a.t }}</b><span class="fmt">{{ a.fmt }}</span></div>
          <button class="btn ghost" type="button" @click="download">Download</button>
        </div>
      </div>
    </div>

    <div class="regels">
      <div class="zh">Merkregels — kort</div>
      <p>{{ MERKREGELS }}</p>
    </div>

    <p v-if="melding" class="melding" role="status" data-test="merk-melding">{{ melding }}</p>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--grey);margin:0 0 16px;font-size:13.5px}
.blk-t{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:1px;color:var(--coral-d);margin:18px 0 10px}
.uitleg{color:var(--grey);font-size:12.5px;margin:-4px 0 12px;line-height:1.5}
/* Producten: kale productfoto's, beeld eerst */
.prods{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
@media(max-width:900px){.prods{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.prods{grid-template-columns:1fr}}
.pcard{margin:0;background:#fff;border:1px solid var(--line);display:flex;flex-direction:column}
.pcard img{width:100%;aspect-ratio:5/7;object-fit:cover;display:block;background:var(--cream)}
.pcard figcaption{padding:10px 12px;display:flex;align-items:center;justify-content:space-between;gap:10px}
.dl{align-self:flex-start;text-decoration:none;display:inline-block}
.pcard .dl{align-self:center;flex-shrink:0}
.wereld{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
@media(max-width:760px){.wereld{grid-template-columns:repeat(2,1fr)}}
.mcard{border:1px solid var(--line);padding:16px;min-height:104px;display:flex;flex-direction:column;justify-content:space-between}
.mic{font-size:26px}
.mlab{font-weight:800;font-size:14px;line-height:1.2}
.mlab small{display:block;font-weight:700;font-size:10.5px;text-transform:uppercase;letter-spacing:.6px;color:var(--grey);margin-top:3px}
.assets{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:760px){.assets{grid-template-columns:1fr}}
.asset{background:#fff;border:1px solid var(--line)}
.alabel{height:76px;display:flex;align-items:center;justify-content:center;font-weight:800;letter-spacing:1px;font-size:13px}
.arow{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:12px 14px}
.arow b{font-size:14px}
.fmt{display:block;color:var(--grey);font-size:12px;margin-top:2px}
.btn{border:1.5px solid var(--line);background:#fff;color:var(--ink);padding:7px 13px;font-weight:800;font-size:12px;cursor:pointer}
.btn:hover{border-color:var(--coral);color:var(--coral)}
.regels{background:#fff;border:1px solid var(--line);padding:16px;margin-top:16px}
.zh{font-size:12px;text-transform:uppercase;letter-spacing:1px;color:var(--coral-d);font-weight:800;margin-bottom:8px}
.regels p{margin:0;color:var(--grey);font-size:13.5px;line-height:1.6}
.melding{color:#2c5a12;font-size:13px;margin-top:10px}
</style>
