// Routes + guards. De guard is UX (waar stuur ik je heen), NIET de beveiliging —
// die zit in RLS. meta.roles bepaalt welke rol een route in de UI mag openen.
import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth.js'

import LoginView from '../modules/auth/views/LoginView.vue'
import DashboardView from '../modules/dashboard/views/DashboardView.vue'
import TappuntenListView from '../modules/tappunten/views/TappuntenListView.vue'
import TappuntDetailView from '../modules/tappunten/views/TappuntDetailView.vue'
import BerichtenView from '../modules/berichten/views/BerichtenView.vue'
import AgendaView from '../modules/agenda/views/AgendaView.vue'
import ActiesView from '../modules/acties/views/ActiesView.vue'
import BeloningenView from '../modules/beloningen/views/BeloningenView.vue'
import DealsView from '../modules/deals/views/DealsView.vue'
import TakenView from '../modules/taken/views/TakenView.vue'
import BeheerView from '../modules/beheer/views/BeheerView.vue'
import CalculatorView from '../modules/calculator/views/CalculatorView.vue'
import ProductenView from '../modules/producten/views/ProductenView.vue'
import VandaagView from '../modules/vandaag/views/VandaagView.vue'
import BestellenView from '../modules/bestellen/views/BestellenView.vue'
import AcademyView from '../modules/academy/views/AcademyView.vue'
import AnalyseView from '../modules/analyse/views/AnalyseView.vue'
import TrajectenView from '../modules/trajecten/views/TrajectenView.vue'
import KennisView from '../modules/kennis/views/KennisView.vue'
import ProcesView from '../modules/kennis/views/ProcesView.vue'
import SalesGameView from '../modules/salesgame/views/SalesGameView.vue'
import BestellingenView from '../modules/bestellingen/views/BestellingenView.vue'

const ALLE_ROLLEN = ['kantoor', 'am', 'partner']

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { publiek: true } },
  { path: '/', name: 'home', component: DashboardView, meta: { roles: ALLE_ROLLEN } },
  { path: '/winkels', name: 'winkels', component: TappuntenListView, meta: { roles: ALLE_ROLLEN } },
  { path: '/winkels/:code', name: 'winkel', component: TappuntDetailView, props: true, meta: { roles: ALLE_ROLLEN } },
  { path: '/berichten', name: 'berichten', component: BerichtenView, meta: { roles: ALLE_ROLLEN } },
  { path: '/agenda', name: 'agenda', component: AgendaView, meta: { roles: ALLE_ROLLEN } },
  { path: '/acties', name: 'acties', component: ActiesView, meta: { roles: ALLE_ROLLEN } },
  { path: '/beloningen', name: 'beloningen', component: BeloningenView, meta: { roles: ALLE_ROLLEN } },
  { path: '/deals', name: 'deals', component: DealsView, meta: { roles: ['kantoor', 'am'] } },
  { path: '/taken', name: 'taken', component: TakenView, meta: { roles: ['kantoor', 'am'] } },
  { path: '/vandaag', name: 'vandaag', component: VandaagView, meta: { roles: ['kantoor', 'am'] } },
  { path: '/producten', name: 'producten', component: ProductenView, meta: { roles: ALLE_ROLLEN } },
  { path: '/bestellingen', name: 'bestellingen', component: BestellingenView, meta: { roles: ['kantoor', 'am'] } },
  { path: '/bestellen', name: 'bestellen', component: BestellenView, meta: { roles: ALLE_ROLLEN } },
  { path: '/academy', name: 'academy', component: AcademyView, meta: { roles: ALLE_ROLLEN } },
  { path: '/analyse', name: 'analyse', component: AnalyseView, meta: { roles: ['kantoor', 'am'] } },
  { path: '/trajecten', name: 'trajecten', component: TrajectenView, meta: { roles: ['kantoor', 'am'] } },
  { path: '/kennisbank', name: 'kennisbank', component: KennisView, meta: { roles: ALLE_ROLLEN } },
  { path: '/proces', name: 'proces', component: ProcesView, meta: { roles: ALLE_ROLLEN } },
  { path: '/game', name: 'game', component: SalesGameView, meta: { roles: ALLE_ROLLEN } },
  { path: '/beheer', name: 'beheer', component: BeheerView, meta: { roles: ['kantoor'] } },
  { path: '/calculator', name: 'calculator', component: CalculatorView, meta: { roles: ['kantoor', 'am'] } },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  const auth = useAuth()
  if (!auth.ready) { await auth.init() }        // eerste keer: sessie ophalen

  if (to.meta.publiek) {
    // al ingelogd? login-scherm overslaan
    if (to.name === 'login' && auth.ingelogd) return { name: 'home' }
    return true
  }
  if (!auth.ingelogd) return { name: 'login' }  // niet ingelogd -> naar login
  if (to.meta.roles && !to.meta.roles.includes(auth.role)) return { name: 'home' }
  return true
})
