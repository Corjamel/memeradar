<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTappunten } from '../store.js'
import { useAuth } from '../../../stores/auth.js'

const st = useTappunten()
const auth = useAuth()
const router = useRouter()
const zoek = ref('')

const lijst = computed(() => {
  const q = zoek.value.trim().toLowerCase()
  if (!q) return st.items
  return st.items.filter(t =>
    (t.name || '').toLowerCase().includes(q) ||
    (t.snelstart || '').toLowerCase().includes(q) ||
    (t.plaats || '').toLowerCase().includes(q))
})

onMounted(async () => {
  if (!st.items.length) await st.laad()
  // Partner heeft precies één winkel -> direct naar het detail.
  if (auth.isPartner && st.items.length === 1) {
    router.replace({ name: 'winkel', params: { code: st.items[0].snelstart } })
  }
})
</script>

<template>
  <div>
    <div class="kop">
      <h1>Winkels</h1>
      <input v-model="zoek" class="zoek" type="search" placeholder="Zoek op naam, code of plaats…" />
    </div>

    <p v-if="st.fout" class="fout" role="alert">{{ st.fout }}</p>
    <p v-else-if="st.laden" class="stil">Laden…</p>
    <p v-else-if="!lijst.length" class="stil">Geen winkels gevonden.</p>

    <div v-else class="rows">
      <button v-for="t in lijst" :key="t.snelstart" class="row" data-test="tappunt-rij"
              @click="router.push({ name: 'winkel', params: { code: t.snelstart } })">
        <span class="nm">{{ t.name }}</span>
        <span class="mo">{{ t.snelstart }}<template v-if="t.plaats"> · {{ t.plaats }}</template></span>
        <span v-if="t.geblokkeerd" class="badge">geblokkeerd</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.kop{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:14px}
h1{margin:0;font-size:22px}
.zoek{flex:1;min-width:220px;max-width:340px;padding:9px 12px;border:1.5px solid var(--line);border-radius:10px;font-size:14px}
.zoek:focus{border-color:var(--coral)}
.rows{display:flex;flex-direction:column;gap:8px}
.row{display:flex;align-items:center;gap:10px;text-align:left;background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;cursor:pointer;font-size:14px}
.row:hover{border-color:var(--coral)}
.nm{font-weight:700;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mo{color:var(--grey);font-size:12.5px}
.badge{margin-left:auto;background:#333;color:#fff;font-size:11px;font-weight:700;border-radius:6px;padding:2px 8px}
.fout{color:#b3261e}
.stil{color:var(--grey)}
</style>
