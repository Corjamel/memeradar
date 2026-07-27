// Routes + guards. De guard is UX (waar stuur ik je heen), NIET de beveiliging —
// die zit in RLS. meta.roles bepaalt welke rol een route in de UI mag openen.
import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth.js'

// Login + dashboard laden direct mee (dat is de eerste render); alle andere
// views zijn lazy — Vite splitst ze in eigen chunks die pas laden wanneer de
// route opent. Dat haalt honderden kB uit de startbundel.
import LoginView from '../modules/auth/views/LoginView.vue'
import DashboardView from '../modules/dashboard/views/DashboardView.vue'
const TappuntenListView = () => import('../modules/tappunten/views/TappuntenListView.vue')
const TappuntDetailView = () => import('../modules/tappunten/views/TappuntDetailView.vue')
const BerichtenView = () => import('../modules/berichten/views/BerichtenView.vue')
const AgendaView = () => import('../modules/agenda/views/AgendaView.vue')
const ActiesView = () => import('../modules/acties/views/ActiesView.vue')
const BeloningenView = () => import('../modules/beloningen/views/BeloningenView.vue')
const DealsView = () => import('../modules/deals/views/DealsView.vue')
const TakenView = () => import('../modules/taken/views/TakenView.vue')
const BeheerView = () => import('../modules/beheer/views/BeheerView.vue')
const CalculatorView = () => import('../modules/calculator/views/CalculatorView.vue')
const ProductenView = () => import('../modules/producten/views/ProductenView.vue')
const VandaagView = () => import('../modules/vandaag/views/VandaagView.vue')
const BestellenView = () => import('../modules/bestellen/views/BestellenView.vue')
const AcademyView = () => import('../modules/academy/views/AcademyView.vue')
const AnalyseView = () => import('../modules/analyse/views/AnalyseView.vue')
const TrajectenView = () => import('../modules/trajecten/views/TrajectenView.vue')
const KennisView = () => import('../modules/kennis/views/KennisView.vue')
const ProcesView = () => import('../modules/kennis/views/ProcesView.vue')
const SalesGameView = () => import('../modules/salesgame/views/SalesGameView.vue')
const GeurbibView = () => import('../modules/geurbib/views/GeurbibView.vue')
const MijnPlanView = () => import('../modules/mijnplan/views/MijnPlanView.vue')
const TeamView = () => import('../modules/team/views/TeamView.vue')
const FormulierenView = () => import('../modules/formulieren/views/FormulierenView.vue')
const BestellingenView = () => import('../modules/bestellingen/views/BestellingenView.vue')
const CommunityView = () => import('../modules/community/views/CommunityView.vue')
const MerkView = () => import('../modules/merk/views/MerkView.vue')
const BezoekenView = () => import('../modules/bezoeken/views/BezoekenView.vue')
const RittenView = () => import('../modules/ritten/views/RittenView.vue')

const ALLE_ROLLEN = ['kantoor', 'am', 'partner']

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { publiek: true } },
  { path: '/', name: 'home', component: DashboardView, meta: { roles: ALLE_ROLLEN } },
  { path: '/winkels', name: 'winkels', component: TappuntenListView, meta: { roles: ALLE_ROLLEN } },
  { path: '/winkels/:code', name: 'winkel', component: TappuntDetailView, props: true, meta: { roles: ALLE_ROLLEN } },
  // Rol-simulatie: AM/kantoor bekijkt de partner-zelfservice van één winkel.
  { path: '/winkels/:code/als-partner', name: 'winkel-partner', component: DashboardView, props: r => ({ previewCode: r.params.code }), meta: { roles: ['kantoor', 'am'] } },
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
  { path: '/geuren', name: 'geuren', component: GeurbibView, meta: { roles: ALLE_ROLLEN } },
  { path: '/mijn-plan', name: 'mijnplan', component: MijnPlanView, meta: { roles: ['partner'] } },
  { path: '/community', name: 'community', component: CommunityView, meta: { roles: ALLE_ROLLEN } },
  { path: '/merk', name: 'merk', component: MerkView, meta: { roles: ALLE_ROLLEN } },
  { path: '/team', name: 'team', component: TeamView, meta: { roles: ['kantoor', 'am'] } },
  { path: '/bezoeken', name: 'bezoeken', component: BezoekenView, meta: { roles: ['kantoor', 'am'] } },
  { path: '/ritten', name: 'ritten', component: RittenView, meta: { roles: ['kantoor', 'am'] } },
  { path: '/formulieren', name: 'formulieren', component: FormulierenView, meta: { roles: ['kantoor', 'am'] } },
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
