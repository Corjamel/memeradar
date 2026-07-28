<script setup>
// HubSpot-paneel op de winkelpagina (alleen kantoor/AM): toont de gematchte
// HubSpot-bedrijven, contactpersonen en deals bij dit tappunt — read-only.
// Degradeert netjes: is de koppeling nog niet gedeployed of is er geen match,
// dan een rustige melding i.p.v. een foutscherm.
import { onMounted, ref } from 'vue'
import { haalHubspot } from '../api.js'
import { eur0 } from '../../../lib/format.js'

const props = defineProps({ tappunt: { type: Object, required: true } })
const laden = ref(true)
const fout = ref('')
const data = ref(null)

onMounted(async () => {
  try {
    const t = props.tappunt
    data.value = await haalHubspot({ winkelnaam: t.name || '', email: t.email || '', snelstart: t.snelstart || '' })
  } catch (e) { fout.value = e.message || 'Kon HubSpot niet laden.' }
  finally { laden.value = false }
})

const bedrag = (d) => d.amount ? eur0(Number(d.amount)) : '—'
const naam = (c) => [c.firstname, c.lastname].filter(Boolean).join(' ') || c.email || 'Contact'
</script>

<template>
  <section class="blok" data-test="hubspot-paneel">
    <div class="kop">
      <span class="hs">HubSpot</span>
      <span class="mo">gekoppelde bedrijven, contacten & deals — read-only</span>
    </div>

    <p v-if="laden" class="mo laad" data-test="hs-laden">HubSpot ophalen…</p>
    <p v-else-if="fout" class="mo stil" data-test="hs-fout">{{ fout }}</p>
    <template v-else-if="data">
      <div v-if="!data.companies.length && !data.contacts.length && !data.deals.length" class="mo stil" data-test="hs-leeg">
        Geen HubSpot-match gevonden voor deze winkel.
      </div>

      <template v-else>
        <div v-if="data.companies.length" class="rij" data-test="hs-bedrijven">
          <h3>Bedrijf</h3>
          <div v-for="c in data.companies" :key="c.id" class="item">
            <b>{{ c.name }}</b><span v-if="c.city" class="mo"> · {{ c.city }}</span>
            <span v-if="c.phone" class="mo"> · {{ c.phone }}</span>
          </div>
        </div>

        <div v-if="data.contacts.length" class="rij" data-test="hs-contacten">
          <h3>Contactpersonen</h3>
          <div v-for="c in data.contacts" :key="c.id" class="item">
            <b>{{ naam(c) }}</b>
            <span v-if="c.jobtitle" class="mo"> · {{ c.jobtitle }}</span>
            <span v-if="c.email" class="mo"> · {{ c.email }}</span>
            <span v-if="c.phone" class="mo"> · {{ c.phone }}</span>
          </div>
        </div>

        <div v-if="data.deals.length" class="rij" data-test="hs-deals">
          <h3>Deals</h3>
          <div v-for="d in data.deals" :key="d.id" class="item deal">
            <b>{{ d.dealname || 'Deal' }}</b>
            <span class="prijs">{{ bedrag(d) }}</span>
            <span v-if="d.dealstage" class="stage">{{ d.dealstage }}</span>
          </div>
        </div>
      </template>
    </template>
  </section>
</template>

<style scoped>
.blok{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px 18px;margin-top:14px}
.kop{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px}
.hs{font-weight:800;font-size:14px;background:#ff7a59;color:#fff;border-radius:8px;padding:3px 10px;letter-spacing:.02em}
.mo{color:var(--grey);font-size:12.5px}
.stil{margin:4px 0 0}
.laad{margin:4px 0 0}
.rij{margin-top:10px}
.rij h3{margin:0 0 4px;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--coral-d)}
.item{font-size:13.5px;padding:3px 0;border-bottom:1px solid var(--line)}
.item:last-child{border-bottom:0}
.item.deal{display:flex;align-items:center;gap:10px}
.item.deal b{flex:1}
.prijs{font-weight:800;color:var(--coral-d);font-variant-numeric:tabular-nums}
.stage{font-size:11px;font-weight:700;color:var(--grey);background:var(--cream);border:1px solid var(--line);border-radius:6px;padding:2px 8px}
</style>
