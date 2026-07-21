<script setup>
// Tijdelijk startscherm — bewijst dat login + rol + guard werken.
// De echte modules (winkels, berichten, agenda) komen hier stap voor stap bij.
import { useAuth } from '../../../stores/auth.js'
const auth = useAuth()
const UITLEG = {
  kantoor: 'Je ziet straks het hele netwerk: alle accountmanagers en winkels.',
  am: 'Je ziet straks alleen je eigen winkels.',
  partner: 'Je ziet straks alleen je eigen winkel.'
}
</script>

<template>
  <div class="home">
    <h1>Welkom</h1>
    <p class="rolregel">Je bent ingelogd als <b>{{ auth.role }}</b>.</p>
    <p class="uitleg">{{ UITLEG[auth.role] }}</p>
    <div class="note">
      Dit is de fundering (Fase 0). Toegang wordt door de database afgedwongen
      (Row Level Security), niet door dit scherm. De winkel-, berichten- en
      agenda-modules bouwen we hier stap voor stap bovenop.
    </div>
  </div>
</template>

<style scoped>
.home{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px}
h1{margin:0 0 8px}
.rolregel{margin:0 0 4px}
.uitleg{color:var(--grey);margin:0 0 16px}
.note{font-size:13px;color:var(--grey);background:#faf7f2;border:1px solid var(--line);border-radius:10px;padding:12px}
</style>
