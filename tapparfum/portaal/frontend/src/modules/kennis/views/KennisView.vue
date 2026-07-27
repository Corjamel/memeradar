<script setup>
// Kennisbank — naslag (v71 KENNIS). Uitklapbare blokken; eerste staat open.
import { ref } from 'vue'
import { KENNIS } from '../data.js'
const open = ref(0)
</script>

<template>
  <div>
    <h1>📚 Kennisbank</h1>
    <p class="sub">Het merkverhaal, de USP's en de spelregels — altijd bij de hand.</p>
    <div v-for="(k, i) in KENNIS" :key="k.t" class="blok" data-test="kennis-blok">
      <button class="kop" type="button" :aria-expanded="open === i" @click="open = open === i ? -1 : i">
        <span>{{ k.t }}</span><span class="chev">{{ open === i ? '▴' : '▾' }}</span>
      </button>
      <div v-if="open === i" class="body">
        <p v-if="k.lead" class="lead">{{ k.lead }}</p>
        <p v-for="(p, j) in (k.p || [])" :key="j">{{ p }}</p>
        <ul v-if="k.li"><li v-for="(l, j) in k.li" :key="j">{{ l }}</li></ul>
        <p v-if="k.note" class="note">{{ k.note }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--grey);margin:0 0 14px;font-size:13.5px}
.blok{background:#fff;border:1px solid var(--line);border-radius:14px;margin-bottom:10px;overflow:hidden}
.kop{display:flex;justify-content:space-between;align-items:center;width:100%;background:none;border:0;padding:14px 18px;font-size:15px;font-weight:800;cursor:pointer;font-family:inherit;text-align:left;color:var(--ink)}
.kop:hover{color:var(--coral-d)}
.chev{color:var(--coral-d);font-size:13px}
.body{padding:0 18px 16px;font-size:14px;line-height:1.6}
.body p{margin:0 0 8px}
.lead{font-weight:800;font-size:15px;color:var(--coral-d)}
ul{margin:0;padding-left:20px}
li{margin:4px 0}
.note{color:var(--grey);font-size:12.5px;background:var(--cream);border-radius:8px;padding:8px 10px;margin-top:6px}
</style>
