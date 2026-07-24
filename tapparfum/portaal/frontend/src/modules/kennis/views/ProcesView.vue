<script setup>
// Proces — het succespad in één beeld (v71 VIEWS.proces): het verkooppad,
// de eenmalige opstart (de 6 checklist-fases) en de doorlopende aftersales-
// cadans. Naslag; leunt op bestaande data (SETUP, AFTERSALES).
import { SALE_STEPS, AFTERSALES } from '../data.js'
import { SETUP } from '../../setup/logic.js'
function print() { window.print() }
</script>

<template>
  <div>
    <div class="titelrij"><h1>🧭 Het proces</h1><button class="print geen-print" type="button" data-test="proces-print" @click="print">🖨 Print / PDF</button></div>
    <p class="sub">Van eerste contact tot een zelfstandig draaiend tappunt — en hoe je het daarna volgt.</p>

    <section class="kaart">
      <h2>1 · Het verkooppad</h2>
      <ol class="pad">
        <li v-for="(s, i) in SALE_STEPS" :key="i" data-test="sale-step"><span class="nr">{{ i + 1 }}</span>{{ s }}</li>
      </ol>
    </section>

    <section class="kaart">
      <h2>2 · Eenmalige opstart</h2>
      <p class="mo">De opstartchecklist bij elke winkel doorloopt zes fases:</p>
      <div class="fases">
        <div v-for="(f, i) in SETUP" :key="i" class="fase" data-test="proces-fase">
          <span class="fnr">{{ f.nr }}</span><b>{{ f.titel }}</b>
          <span class="mo">{{ f.acties.length }} stappen</span>
        </div>
      </div>
    </section>

    <section class="kaart">
      <h2>3 · Doorlopende groeimotor & aftersales</h2>
      <p class="mo">Na livegang volgt de vaste opvolgcadans — je vindt deze momenten automatisch terug op Vandaag:</p>
      <div class="cadans">
        <div v-for="(a, i) in AFTERSALES" :key="i" class="stap" data-test="aftersales-stap">
          <b>{{ a[0] }}</b><span>{{ a[1] }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
.titelrij{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap}
.print{background:#fff;border:1.5px solid var(--line);padding:8px 13px;font-weight:800;font-size:12.5px;cursor:pointer;text-transform:uppercase;letter-spacing:.4px}
.print:hover{border-color:var(--coral);color:var(--coral)}
h2{margin:0 0 10px;font-size:15px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.kaart{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:12px}
.mo{color:var(--grey);font-size:12.5px;margin:0 0 10px}
.pad{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}
.pad li{display:flex;align-items:center;gap:12px;font-size:14px;padding:8px 0;border-bottom:1px solid var(--line)}
.pad li:last-child{border-bottom:0}
.nr{width:26px;height:26px;flex-shrink:0;border-radius:8px;background:var(--coral);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px}
.fases{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}
.fase{display:flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:10px;padding:9px 11px;font-size:13px}
.fnr{width:22px;height:22px;flex-shrink:0;border-radius:6px;background:var(--soft);color:var(--coral-d);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px}
.fase b{flex:1;min-width:0}
.cadans{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px}
.stap{background:var(--cream);border-radius:10px;padding:12px;text-align:center}
.stap b{display:block;color:var(--coral-d);font-size:15px}
.stap span{font-size:12px;color:var(--grey);font-weight:700}
</style>
