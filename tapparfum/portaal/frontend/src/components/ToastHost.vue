<script setup>
// ToastHost — rendert de gedeelde toast-wachtlijst rechtsonder (v71-stijl).
// Wordt éénmalig gemount in App.vue; alle views praten via de toast-store.
import { useToast } from '../stores/toast.js'
const toast = useToast()
</script>

<template>
  <div class="toasthost" aria-live="polite" aria-atomic="false">
    <div v-for="t in toast.items" :key="t.id"
         class="toast" :class="[t.type, { uit: t.uit }]"
         role="status" data-test="toast"
         @click="toast.sluit(t.id)">
      <span class="tic" aria-hidden="true">{{ t.type === 'fout' ? '⚠' : t.type === 'info' ? 'ℹ' : '✓' }}</span>
      <span class="ttx">{{ t.txt }}</span>
    </div>
  </div>
</template>

<style scoped>
.toasthost{position:fixed;right:20px;bottom:20px;z-index:9000;display:flex;flex-direction:column;gap:10px;align-items:flex-end;pointer-events:none;max-width:min(92vw,380px)}
.toast{pointer-events:auto;display:flex;align-items:center;gap:10px;background:var(--ink);color:#fff;padding:12px 15px;border-radius:12px;box-shadow:0 8px 26px rgba(0,0,0,.22);font-size:13.5px;font-weight:600;line-height:1.35;cursor:pointer;animation:toastIn .22s ease}
.toast.ok{background:var(--green)}
.toast.fout{background:var(--coral-d)}
.toast.info{background:#245b7a}
.toast.uit{opacity:0;transform:translateY(6px);transition:opacity .2s ease,transform .2s ease}
.tic{font-weight:900;flex-shrink:0}
.ttx{min-width:0}
@keyframes toastIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@media(prefers-reduced-motion:reduce){.toast{animation:none}.toast.uit{transition:none}}
</style>
