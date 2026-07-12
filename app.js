/* MemeRadar — crypto & memecoin tracker
 * Data: CoinGecko (gratis publieke API) + DexScreener (gratis publieke API)
 * Veiligheid: geen externe libraries, geen private keys, kopen alleen via officiële DEX-links.
 */

'use strict';

const CG = 'https://api.coingecko.com/api/v3';
const DS = 'https://api.dexscreener.com';

const state = {
  tab: 'trending',
  chain: 'alle',
  threshold: 10,
  currency: 'usd',
  sortBy: 'mcap',
  onlySignals: false,
  usdToEur: null,
  eurRateAt: 0,
  wallets: { evm: null, sol: null },
  rows: [],            // huidige weergave
  watchlist: loadWatchlist(),
  prevSignals: {},     // key -> 'buy'|'sell'|'hold' (voor alerts)
  timer: null,
  searchQuery: '',
};

/* ---------- helpers ---------- */

const $ = (id) => document.getElementById(id);

function loadWatchlist() {
  try { return JSON.parse(localStorage.getItem('mr_watchlist') || '[]'); }
  catch { return []; }
}

function loadSettings() {
  try {
    const s = JSON.parse(localStorage.getItem('mr_settings') || '{}');
    if (s.threshold > 0) state.threshold = s.threshold;
    if (s.currency) state.currency = s.currency;
    if (s.sortBy) state.sortBy = s.sortBy;
    if (typeof s.onlySignals === 'boolean') state.onlySignals = s.onlySignals;
    if (s.chain) state.chain = s.chain;
  } catch { /* defaults */ }
}
function saveSettings() {
  localStorage.setItem('mr_settings', JSON.stringify({
    threshold: state.threshold, currency: state.currency, sortBy: state.sortBy,
    onlySignals: state.onlySignals, chain: state.chain,
  }));
}
function saveWatchlist() {
  localStorage.setItem('mr_watchlist', JSON.stringify(state.watchlist));
  $('watchCount').textContent = state.watchlist.length || '';
}

function rowKey(r) { return r.source === 'cg' ? `cg:${r.id}` : `dex:${r.chainId}:${r.address}`; }

function inWatchlist(r) { return state.watchlist.some((w) => rowKey(w) === rowKey(r)); }

function fmtPrice(usd) {
  if (usd == null || isNaN(usd)) return '—';
  let v = usd;
  let sym = '$';
  if (state.currency === 'eur' && state.usdToEur) { v = usd * state.usdToEur; sym = '€'; }
  if (v >= 1000) return sym + v.toLocaleString('nl-NL', { maximumFractionDigits: 0 });
  if (v >= 1) return sym + v.toLocaleString('nl-NL', { maximumFractionDigits: 2 });
  if (v >= 0.01) return sym + v.toLocaleString('nl-NL', { maximumFractionDigits: 4 });
  // hele kleine memecoin-prijzen: significante cijfers tonen
  return sym + v.toLocaleString('nl-NL', { maximumSignificantDigits: 4 });
}

function fmtBig(usd) {
  if (usd == null || isNaN(usd)) return '—';
  let v = usd;
  let sym = '$';
  if (state.currency === 'eur' && state.usdToEur) { v = usd * state.usdToEur; sym = '€'; }
  if (v >= 1e12) return sym + (v / 1e12).toFixed(2) + ' bln';
  if (v >= 1e9) return sym + (v / 1e9).toFixed(2) + ' mld';
  if (v >= 1e6) return sym + (v / 1e6).toFixed(2) + ' mln';
  if (v >= 1e3) return sym + (v / 1e3).toFixed(1) + 'k';
  return sym + v.toFixed(0);
}

function fmtPct(p) {
  if (p == null || isNaN(p)) return '<span class="pct-flat">—</span>';
  const cls = p > 0.05 ? 'pct-up' : p < -0.05 ? 'pct-down' : 'pct-flat';
  const arrow = p > 0.05 ? '▲' : p < -0.05 ? '▼' : '';
  const num = p.toLocaleString('nl-NL', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  return `<span class="${cls}">${arrow} ${num}%</span>`;
}

function fmtAge(ms) {
  const min = Math.floor(ms / 60000);
  if (min < 1) return 'net nu';
  if (min < 60) return `${min}m oud`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h}u oud`;
  return `${Math.floor(h / 24)}d oud`;
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

/* ---------- eigen prijsgeheugen ----------
 * On-chain tokens hebben 1u/6u/24u rechtstreeks uit de DEX-data. CoinGecko-coins
 * missen alleen 6u; dat vult de app aan met eigen metingen terwijl hij open staat.
 */

function loadHist() {
  try { return JSON.parse(localStorage.getItem('mr_hist') || '{}'); }
  catch { return {}; }
}
const hist = loadHist();

function recordHistory(rows) {
  const now = Date.now();
  for (const r of rows) {
    if (r.priceUsd == null) continue;
    const k = rowKey(r);
    const arr = hist[k] || [];
    if (!arr.length || now - arr[arr.length - 1][0] > 110000) arr.push([now, r.priceUsd]);
    // 9 uur bewaren is genoeg voor het 8u-frame
    hist[k] = arr.filter(([t]) => now - t < 9.2 * 3600000);
  }
  // verweesde tokens opruimen zodat localStorage niet volloopt
  const keys = Object.keys(hist);
  if (keys.length > 150) {
    keys.sort((a, b) => (hist[a][hist[a].length - 1]?.[0] ?? 0) - (hist[b][hist[b].length - 1]?.[0] ?? 0));
    for (const k of keys.slice(0, keys.length - 150)) delete hist[k];
  }
  try { localStorage.setItem('mr_hist', JSON.stringify(hist)); } catch { /* vol: dan geen geheugen */ }
}

function histChange(key, minutes, cur) {
  const arr = hist[key];
  if (!arr || cur == null) return null;
  const target = Date.now() - minutes * 60000;
  let best = null;
  for (const s of arr) {
    if (!best || Math.abs(s[0] - target) < Math.abs(best[0] - target)) best = s;
  }
  // meting moet redelijk dicht bij het gevraagde moment liggen, anders liegen we
  if (!best || Math.abs(best[0] - target) > minutes * 60000 * 0.35 + 180000) return null;
  return best[1] ? (cur / best[1] - 1) * 100 : null;
}

/* ---------- signaal-logica ----------
 * KOOP  : 24u-verandering >= +drempel (standaard +10%)
 * VERKOOP: 24u-verandering <= −drempel (standaard −10%)
 * HOUD  : daartussen. "STERK" vanaf 2,5x de drempel.
 */
function computeSignal(r) {
  const t = state.threshold;
  const ch = r.change24h;
  if (ch == null || isNaN(ch)) return { type: 'hold', label: 'GEEN DATA', strong: false };
  if (ch >= t) {
    const strong = ch >= t * 2.5;
    let label = strong ? 'STERK KOOP' : 'KOOP';
    // momentum-check: stijger die het laatste uur alweer hard daalt → waarschuwen
    if (r.change1h != null && r.change1h <= -3) label += ' · afkoelend';
    return { type: 'buy', label, strong };
  }
  if (ch <= -t) {
    const strong = ch <= -t * 2.5;
    let label = strong ? 'STERK VERKOOP' : 'VERKOOP';
    if (r.change1h != null && r.change1h >= 3) label += ' · herstelt';
    return { type: 'sell', label, strong };
  }
  return { type: 'hold', label: 'HOUD', strong: false };
}

/* Risico-inschatting voor on-chain tokens (rug-pull-signalen) */
function computeRisk(r) {
  if (r.source === 'cg') {
    return { cls: 'risk-low', label: 'Gevestigd' };
  }
  const liq = r.liquidity ?? 0;
  const ageDays = r.createdAt ? (Date.now() - r.createdAt) / 86400000 : null;
  if (liq < 50000 || (ageDays != null && ageDays < 7)) return { cls: 'risk-high', label: '⚠️ Hoog' };
  if (liq < 250000 || (ageDays != null && ageDays < 30)) return { cls: 'risk-mid', label: 'Gemiddeld' };
  return { cls: 'risk-low', label: 'Laag' };
}

function chartLink(r) {
  if (r.source === 'cg') return `https://www.coingecko.com/en/coins/${encodeURIComponent(r.id)}`;
  return r.url || `https://dexscreener.com/${encodeURIComponent(r.chainId)}/${encodeURIComponent(r.address)}`;
}

/* ---------- data ophalen ---------- */

async function fetchJson(url) {
  const res = await fetch(url, { headers: { accept: 'application/json' } });
  if (res.status === 429) throw Object.assign(new Error('rate-limit (429)'), { rateLimited: true });
  if (!res.ok) throw new Error(`API-fout ${res.status} bij ${new URL(url).host}`);
  return res.json();
}

/* GeckoTerminal heeft een krappe limiet (~30/min). Daarom: verzoeken NIET tegelijk
 * afvuren maar netjes achter elkaar met een kleine pauze, én antwoorden 60s cachen
 * zodat tab-wisselen of auto-verversen niet steeds opnieuw de limiet opvreet. */
const gtCache = new Map(); // url -> { t, data }
const sleep = (ms) => new Promise((res) => setTimeout(res, ms));
// serialiseer GT-verzoeken zonder dat één fout de hele keten vergiftigt:
// de "poort" wordt na elke stap altijd weer resolved (nooit rejected).
let gtGate = Promise.resolve();

async function fetchGtCached(url, maxAgeMs = 90000) {
  const hit = gtCache.get(url);
  if (hit && Date.now() - hit.t < maxAgeMs) return hit.data;

  const myTurn = gtGate;
  let release;
  gtGate = new Promise((res) => { release = res; }); // volgende beller wacht op mij
  try {
    await myTurn; // wacht netjes op de vorige
    const again = gtCache.get(url);
    if (again && Date.now() - again.t < maxAgeMs) return again.data;
    const data = await fetchJson(url); // gooit door naar de aanroeper (bv. 429)
    gtCache.set(url, { t: Date.now(), data });
    await sleep(350); // blijf ruim onder ~30 calls/min
    return data;
  } finally {
    release(); // poort ALTIJD vrijgeven, ook na een fout
  }
}

async function fetchEurRate() {
  try {
    const d = await fetchJson(`${CG}/simple/price?ids=usd-coin&vs_currencies=eur`);
    state.usdToEur = d['usd-coin']?.eur ?? null;
    state.eurRateAt = Date.now();
  } catch { /* oude koers behouden */ }
}
function eurRateStale() {
  return state.usdToEur == null || Date.now() - state.eurRateAt > 10 * 60000;
}

function mapCgCoin(c) {
  return {
    source: 'cg',
    id: c.id,
    symbol: (c.symbol || '').toUpperCase(),
    name: c.name,
    image: c.image,
    priceUsd: c.current_price,
    change1h: c.price_change_percentage_1h_in_currency,
    change6h: null, // niet in de gratis CoinGecko-API; eigen prijsgeheugen vult dit aan
    change24h: c.price_change_percentage_24h,
    volume24h: c.total_volume,
    mcap: c.market_cap,
    liquidity: null,
    createdAt: null,
    chainId: null,
    address: null,
    url: null,
  };
}

/* Quote-tokens met een betrouwbare USD-waardering. Pools tegen een obscuur
 * quote-token kunnen een compleet verkeerde (gemanipuleerde) prijs en
 * liquiditeit rapporteren — die mogen nooit de getoonde prijs bepalen. */
const TRUSTED_QUOTES = new Set([
  'SOL', 'WSOL', 'USDC', 'USDT', 'DAI', 'FDUSD', 'USDBC', 'USD1',
  'WETH', 'ETH', 'WBNB', 'BNB', 'WPOL', 'WMATIC', 'WAVAX', 'AVAX',
]);

function betterPair(a, b) {
  const ta = TRUSTED_QUOTES.has((a.quoteToken?.symbol || '').toUpperCase());
  const tb = TRUSTED_QUOTES.has((b.quoteToken?.symbol || '').toUpperCase());
  if (ta !== tb) return ta;
  const va = a.volume?.h24 ?? 0, vb = b.volume?.h24 ?? 0;
  if (va !== vb) return va > vb; // volume is lastiger te faken dan liquiditeit
  return (a.liquidity?.usd ?? 0) > (b.liquidity?.usd ?? 0);
}

function bestPairPerToken(pairs) {
  // DexScreener geeft meerdere pools per token; kies de meest betrouwbare
  const byToken = new Map();
  for (const p of pairs || []) {
    if (!p?.baseToken?.address) continue;
    const k = `${p.chainId}:${p.baseToken.address}`;
    const cur = byToken.get(k);
    if (!cur || betterPair(p, cur)) byToken.set(k, p);
  }
  return [...byToken.values()];
}

function mapDexPair(p) {
  return {
    source: 'dex',
    id: null,
    symbol: p.baseToken.symbol || '?',
    name: p.baseToken.name || p.baseToken.symbol || 'Onbekend',
    image: p.info?.imageUrl || null,
    priceUsd: p.priceUsd ? parseFloat(p.priceUsd) : null,
    change1h: p.priceChange?.h1 ?? null,
    change6h: p.priceChange?.h6 ?? null,
    change24h: p.priceChange?.h24 ?? null,
    volume24h: p.volume?.h24 ?? null,
    mcap: p.marketCap ?? p.fdv ?? null,
    liquidity: p.liquidity?.usd ?? null,
    createdAt: p.pairCreatedAt ?? null,
    chainId: p.chainId,
    address: p.baseToken.address,
    pairAddress: p.pairAddress ?? null,
    url: p.url,
    buys1h: p.txns?.h1?.buys ?? null,
    sells1h: p.txns?.h1?.sells ?? null,
    buys5m: p.txns?.m5?.buys ?? null,
    sells5m: p.txns?.m5?.sells ?? null,
  };
}

/* Koop/verkoop-druk: aandeel kooptransacties in het laatste uur, met een
 * 5-minuten-pijl die laat zien of de druk aan het kantelen is. */
function pressureCell(r) {
  const b = r.buys1h, s = r.sells1h;
  if (b == null || s == null || b + s === 0) return '<span class="pct-flat">—</span>';
  const pct = (b / (b + s)) * 100;
  const cls = pct >= 55 ? 'pct-up' : pct <= 45 ? 'pct-down' : 'pct-flat';
  let arrow = '';
  if (r.buys5m != null && r.sells5m != null && r.buys5m + r.sells5m >= 5) {
    const pct5 = (r.buys5m / (r.buys5m + r.sells5m)) * 100;
    if (pct5 - pct >= 10) arrow = ' <span class="pct-up">▲</span>';
    else if (pct - pct5 >= 10) arrow = ' <span class="pct-down">▼</span>';
  }
  const title = `laatste uur: ${b} koop / ${s} verkoop · laatste 5 min: ${r.buys5m ?? '?'} koop / ${r.sells5m ?? '?'} verkoop`;
  return `<div class="pressure" title="${escapeHtml(title)}">
    <div class="pressure-bar"><div class="pressure-buy" style="width:${pct.toFixed(0)}%"></div></div>
    <span class="${cls}">${Math.round(pct)}% koop</span>${arrow}
  </div>`;
}

async function loadTop() {
  const d = await fetchJson(`${CG}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&price_change_percentage=1h,24h`);
  return d.map(mapCgCoin);
}

async function loadMeme() {
  const d = await fetchJson(`${CG}/coins/markets?vs_currency=usd&category=meme-token&order=market_cap_desc&per_page=50&page=1&price_change_percentage=1h,24h`);
  return d.map(mapCgCoin);
}

/* ---------- DexScreener-stijl lijsten via GeckoTerminal (gratis, realtime) ---------- */

const GT = 'https://api.geckoterminal.com/api/v2';
// Uitgebreide chain-lijst (GeckoTerminal-id → label + DexScreener-chainId voor links).
// Alleen chains met genoeg memecoin-activiteit; volgorde = populariteit.
const CHAINS = [
  { gt: 'solana',      label: 'Solana',    ds: 'solana' },
  { gt: 'eth',         label: 'Ethereum',  ds: 'ethereum' },
  { gt: 'base',        label: 'Base',      ds: 'base' },
  { gt: 'bsc',         label: 'BNB Chain', ds: 'bsc' },
  { gt: 'arbitrum',    label: 'Arbitrum',  ds: 'arbitrum' },
  { gt: 'polygon_pos', label: 'Polygon',   ds: 'polygon' },
  { gt: 'avax',        label: 'Avalanche', ds: 'avalanche' },
  { gt: 'optimism',    label: 'Optimism',  ds: 'optimism' },
  { gt: 'tron',        label: 'Tron',      ds: 'tron' },
  { gt: 'blast',       label: 'Blast',     ds: 'blast' },
  { gt: 'sui-network', label: 'Sui',       ds: 'sui' },
  { gt: 'ton',         label: 'TON',       ds: 'ton' },
  { gt: 'pulsechain',  label: 'PulseChain',ds: 'pulsechain' },
  { gt: 'hyperevm',    label: 'Hyperliquid', ds: 'hyperliquid' },
];
const GT_NETS = CHAINS.map((c) => c.gt);
const GT_TO_CHAIN = Object.fromEntries(CHAINS.map((c) => [c.gt, c.ds]));

const pf = (v) => { const n = parseFloat(v); return isNaN(n) ? null : n; };

function mapGtPool(p, tokenInfo) {
  const a = p.attributes || {};
  const rel = p.relationships?.base_token?.data?.id || '';
  const us = rel.indexOf('_');
  const gtNet = rel.slice(0, us);
  const address = rel.slice(us + 1);
  const tok = tokenInfo[rel] || {};
  const nameFromPool = (a.name || '').split(' / ')[0].trim();
  const chainId = GT_TO_CHAIN[gtNet] || gtNet;
  return {
    source: 'dex',
    id: null,
    symbol: tok.symbol || nameFromPool || '?',
    name: tok.name || nameFromPool || 'Onbekend',
    image: (tok.image_url && tok.image_url !== 'missing.png') ? tok.image_url : null,
    priceUsd: pf(a.base_token_price_usd),
    change1h: pf(a.price_change_percentage?.h1),
    change6h: pf(a.price_change_percentage?.h6),
    change24h: pf(a.price_change_percentage?.h24),
    volume24h: pf(a.volume_usd?.h24),
    mcap: pf(a.market_cap_usd) ?? pf(a.fdv_usd),
    liquidity: pf(a.reserve_in_usd),
    createdAt: a.pool_created_at ? Date.parse(a.pool_created_at) : null,
    chainId,
    address,
    pairAddress: a.address || null,
    url: `https://dexscreener.com/${encodeURIComponent(chainId)}/${encodeURIComponent(a.address || '')}`,
    buys1h: a.transactions?.h1?.buys ?? null,
    sells1h: a.transactions?.h1?.sells ?? null,
    buys5m: a.transactions?.m5?.buys ?? null,
    sells5m: a.transactions?.m5?.sells ?? null,
  };
}

async function fetchGtList(kind, net, page = 1) {
  const sep = kind.includes('?') ? '&' : '?';
  const d = await fetchGtCached(`${GT}/networks/${net}/${kind}${sep}include=base_token&page=${page}`);
  if (!d) return [];
  const tokenInfo = {};
  for (const t of d.included || []) tokenInfo[t.id] = t.attributes || {};
  return (d.data || []).map((p) => mapGtPool(p, tokenInfo));
}

// "Alle chains" = de 6 actiefste (anders blazen we de gratis limiet op).
// Kies een specifieke chain om ook de andere te zien.
const TOP_NETS = ['solana', 'eth', 'base', 'bsc', 'arbitrum', 'tron'];
function selectedNets() { return state.chain === 'alle' ? TOP_NETS : [state.chain]; }

function dedupeByToken(rows) {
  const m = new Map();
  for (const r of rows) {
    const k = `${r.chainId}:${r.address}`;
    const cur = m.get(k);
    if (!cur || (r.liquidity ?? 0) > (cur.liquidity ?? 0)) m.set(k, r);
  }
  return [...m.values()];
}

async function loadGtTab(kind, pages = 1) {
  const jobs = [];
  for (const n of selectedNets()) {
    for (let p = 1; p <= pages; p++) jobs.push(fetchGtList(kind, n, p));
  }
  // sequentieel (via de gedeelde cache-keten) i.p.v. een burst — spaart de limiet
  const res = await Promise.allSettled(jobs);
  const rows = dedupeByToken(res.flatMap((r) => (r.status === 'fulfilled' ? r.value : [])))
    .filter((r) => (r.liquidity ?? 0) > 1000); // dode/lege pools eruit
  if (!rows.length) {
    if (res.some((r) => r.status === 'rejected' && r.reason?.rateLimited)) {
      const e = new Error('GeckoTerminal-limiet even bereikt');
      e.rateLimited = true;
      throw e;
    }
    if (res.every((r) => r.status === 'rejected')) {
      throw res[0].reason || new Error('on-chain data niet bereikbaar');
    }
  }
  return rows;
}

// DexScreener-fallback (ruimere limiet) als GeckoTerminal 429 geeft
async function loadDexTrending() {
  const chains = state.chain === 'alle' ? ['solana', 'ethereum', 'base', 'bsc'] : [GT_TO_CHAIN[state.chain] || state.chain];
  const res = await Promise.allSettled(
    chains.map((c) => fetchJson(`${DS}/token-boosts/top/v1`).then(() => null).catch(() => null))
  );
  // token-boosts geeft alleen adressen; eenvoudiger is de zoek-endpoint per chain-symbool.
  // We gebruiken de betrouwbaardere latest/dex/search met brede term per chain.
  const all = await Promise.allSettled(
    chains.map((c) => fetchJson(`${DS}/latest/dex/search?q=${encodeURIComponent(c)}`)
      .then((d) => bestPairPerToken(d.pairs).map(mapDexPair).filter((r) => r.chainId === c)))
  );
  return dedupeByToken(all.flatMap((r) => (r.status === 'fulfilled' ? r.value : [])))
    .filter((r) => (r.liquidity ?? 0) > 5000);
}

async function withDexFallback(loader) {
  try {
    const rows = await loader();
    if (rows && rows.length) return rows;
    throw new Error('leeg');
  } catch (e) {
    // bij ELKE GeckoTerminal-hapering (429 of netwerkblokkade): val terug op DexScreener
    try {
      const rows = await loadDexTrending();
      if (rows.length) {
        rows._notice = 'Even druk bij de hoofdbron — nu via DexScreener (kortere lijst). Herstelt vanzelf.';
        return rows;
      }
    } catch { /* ook fallback faalde */ }
    throw e;
  }
}

const loadTrending = () => withDexFallback(() => loadGtTab('trending_pools', 1));
const loadNieuw = () => withDexFallback(() => loadGtTab('new_pools', 1));
// Stijgers: scan de hoogste-volume-pools per chain en houd de plussen over.
// Volume-eis voorkomt dat een +5000% zonder echte handel bovenaan staat.
const loadStijgers = () => withDexFallback(() => loadGtTab('pools?sort=h24_volume_usd_desc', 2)
  .then((rows) => rows.filter((r) => (r.change24h ?? 0) > 0 && (r.volume24h ?? 0) > 10000)));

async function loadSearch() {
  const q = state.searchQuery.trim();
  if (!q) return [];
  const d = await fetchJson(`${DS}/latest/dex/search?q=${encodeURIComponent(q)}`);
  return bestPairPerToken(d.pairs)
    .filter((p) => (p.liquidity?.usd ?? 0) > 1000)
    .map(mapDexPair)
    .slice(0, 50);
}

async function loadWatch() {
  const cgIds = state.watchlist.filter((w) => w.source === 'cg').map((w) => w.id);
  const dexByChain = new Map();
  for (const w of state.watchlist.filter((w) => w.source === 'dex')) {
    if (!dexByChain.has(w.chainId)) dexByChain.set(w.chainId, []);
    dexByChain.get(w.chainId).push(w.address);
  }
  const jobs = [];
  if (cgIds.length) {
    jobs.push(
      fetchJson(`${CG}/coins/markets?vs_currency=usd&ids=${cgIds.map(encodeURIComponent).join(',')}&price_change_percentage=1h,24h`)
        .then((d) => d.map(mapCgCoin))
    );
  }
  for (const [chain, addrs] of dexByChain) {
    for (let i = 0; i < addrs.length; i += 30) {
      const batch = addrs.slice(i, i + 30);
      jobs.push(
        fetchJson(`${DS}/tokens/v1/${encodeURIComponent(chain)}/${batch.map(encodeURIComponent).join(',')}`)
          .then((pairs) => bestPairPerToken(pairs).map(mapDexPair))
      );
    }
  }
  const results = await Promise.allSettled(jobs);
  return results.flatMap((r) => (r.status === 'fulfilled' ? r.value : []));
}

/* ---------- alerts (drempel-doorbraak op watchlist) ---------- */

function checkAlerts(rows) {
  const watchKeys = new Set(state.watchlist.map(rowKey));
  const messages = [];
  for (const r of rows) {
    const key = rowKey(r);
    if (!watchKeys.has(key)) continue;
    const sig = computeSignal(r).type;
    const prev = state.prevSignals[key];
    if (prev && prev !== sig && sig !== 'hold') {
      const txt = sig === 'buy'
        ? `📈 ${r.symbol} is +${state.threshold}% doorbroken (24u: ${r.change24h?.toFixed(1)}%) — KOOP-signaal`
        : `📉 ${r.symbol} is −${state.threshold}% doorbroken (24u: ${r.change24h?.toFixed(1)}%) — VERKOOP-signaal`;
      messages.push(txt);
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('MemeRadar signaal', { body: txt });
      }
    }
    state.prevSignals[key] = sig;
  }
  const box = $('alertBox');
  if (messages.length) {
    box.innerHTML = messages.map(escapeHtml).join('<br>');
    box.classList.remove('hidden');
  }
}

/* ---------- rendering ---------- */

function sortRows(rows) {
  let by = state.sortBy;
  // per tabblad een zinnige standaard, tenzij de gebruiker zelf iets koos
  if (by === 'mcap') {
    if (state.tab === 'nieuw') by = 'age';
    else if (state.tab === 'stijgers') by = 'change';
  }
  return [...rows].sort((a, b) => {
    if (by === 'change') return (b.change24h ?? -Infinity) - (a.change24h ?? -Infinity);
    if (by === 'change1h') return (b.change1h ?? -Infinity) - (a.change1h ?? -Infinity);
    if (by === 'volume') return (b.volume24h ?? 0) - (a.volume24h ?? 0);
    if (by === 'liquidity') return (b.liquidity ?? 0) - (a.liquidity ?? 0);
    if (by === 'age') return (b.createdAt ?? 0) - (a.createdAt ?? 0);
    return (b.mcap ?? 0) - (a.mcap ?? 0);
  });
}

function render() {
  const body = $('coinBody');
  let rows = sortRows(state.rows);
  const empty = $('emptyState');

  if (state.onlySignals) {
    rows = rows.filter((r) => computeSignal(r).type !== 'hold');
    if (!rows.length && state.rows.length) {
      body.innerHTML = '';
      empty.textContent = `Geen enkel token op dit tabblad staat momenteel boven +${state.threshold}% of onder −${state.threshold}% (24u). De markt is rustig — dat is geen storing. Zet het filter uit om alles te zien.`;
      empty.classList.remove('hidden');
      return;
    }
  }

  if (!rows.length) {
    body.innerHTML = '';
    empty.textContent = state.tab === 'watch'
      ? 'Je watchlist is leeg. Klik op de ster ⭐ bij een token om hem te volgen.'
      : state.tab === 'search'
        ? 'Typ een tokennaam en klik op Zoeken.'
        : 'Geen data gevonden.';
    empty.classList.remove('hidden');
    return;
  }
  empty.classList.add('hidden');

  body.innerHTML = rows.map((r) => {
    const sig = computeSignal(r);
    const risk = computeRisk(r);
    const starred = inWatchlist(r);
    const img = r.image
      ? `<img src="${escapeHtml(r.image)}" alt="" loading="lazy" onerror="this.style.visibility='hidden'">`
      : '<img alt="" style="visibility:hidden">';
    const liqOrMcap = r.source === 'dex'
      ? `${fmtBig(r.liquidity)} <span class="token-sub">liq</span>`
      : `${fmtBig(r.mcap)} <span class="token-sub">mcap</span>`;
    const chainTag = r.chainId ? ` · ${escapeHtml(r.chainId)}` : '';
    const ageTag = r.createdAt ? ` · ${fmtAge(Date.now() - r.createdAt)}` : '';
    const rowCls = sig.type === 'buy' ? 'row-buy' : sig.type === 'sell' ? 'row-sell' : '';
    return `<tr class="${rowCls}">
      <td class="c-star"><button class="star-btn ${starred ? 'active' : ''}" data-key="${escapeHtml(rowKey(r))}" title="Watchlist">${starred ? '⭐' : '☆'}</button></td>
      <td class="c-token"><div class="token-cell">${img}<div><div class="token-name">${escapeHtml(r.name)}</div><div class="token-sub">${escapeHtml(r.symbol)}${chainTag}${ageTag}</div></div></div></td>
      <td class="num c-price">${fmtPrice(r.priceUsd)}</td>
      <td class="num" data-label="1u">${fmtPct(r.change1h ?? histChange(rowKey(r), 60, r.priceUsd))}</td>
      <td class="num" data-label="6u">${fmtPct(r.change6h ?? histChange(rowKey(r), 360, r.priceUsd))}</td>
      <td class="num" data-label="24u">${fmtPct(r.change24h)}</td>
      <td data-label="Druk">${pressureCell(r)}</td>
      <td class="num" data-label="Volume">${fmtBig(r.volume24h)}</td>
      <td class="num" data-label="${r.source === 'dex' ? 'Liquiditeit' : 'Mcap'}">${liqOrMcap}</td>
      <td class="c-signal"><span class="signal signal-${sig.type} ${sig.strong ? 'signal-strong' : ''}">${sig.label}</span></td>
      <td data-label="Risico"><span class="risk ${risk.cls}">${risk.label}</span></td>
      <td class="c-actions"><div class="actions">${
        r.source === 'dex'
          ? `<button class="trade-buy" data-key="${escapeHtml(rowKey(r))}" data-side="buy">Koop</button>
             <button class="trade-sell" data-key="${escapeHtml(rowKey(r))}" data-side="sell">Verkoop</button>`
          : `<button class="btn small find-onchain" data-symbol="${escapeHtml(r.symbol)}" title="Zoek dit token on-chain om direct te handelen">Handel</button>`
      }<a class="chart-link" href="${escapeHtml(chartLink(r))}" target="_blank" rel="noopener noreferrer">Grafiek</a>
      </div></td>
    </tr>`;
  }).join('');

  // ster-knoppen koppelen
  body.querySelectorAll('.star-btn').forEach((btn) => {
    btn.addEventListener('click', () => toggleWatch(btn.dataset.key));
  });
  // handel-knoppen: dex-tokens direct in de app, CoinGecko-coins via on-chain zoeken
  body.querySelectorAll('.trade-buy, .trade-sell').forEach((btn) => {
    btn.addEventListener('click', () => window.openSwap?.(btn.dataset.key, btn.dataset.side));
  });
  body.querySelectorAll('.find-onchain').forEach((btn) => {
    btn.addEventListener('click', () => {
      $('searchInput').value = btn.dataset.symbol;
      state.searchQuery = btn.dataset.symbol;
      setTab('search');
    });
  });
}

function toggleWatch(key) {
  const idx = state.watchlist.findIndex((w) => rowKey(w) === key);
  if (idx >= 0) {
    state.watchlist.splice(idx, 1);
  } else {
    const r = state.rows.find((x) => rowKey(x) === key);
    if (r) {
      state.watchlist.push({
        source: r.source, id: r.id, chainId: r.chainId, address: r.address,
        symbol: r.symbol, name: r.name,
      });
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
      }
    }
  }
  saveWatchlist();
  if (state.tab === 'watch') refresh(); else render();
}

/* ---------- refresh-cyclus ---------- */

let refreshSeq = 0;

async function refresh() {
  if (state.tab === 'bot') {
    await renderBotPanel();
    $('lastUpdate').textContent = `Bijgewerkt: ${new Date().toLocaleTimeString('nl-NL')}`;
    return;
  }
  const loaders = { trending: loadTrending, stijgers: loadStijgers, nieuw: loadNieuw, top: loadTop, meme: loadMeme, search: loadSearch, watch: loadWatch };
  const seq = ++refreshSeq;
  $('errorBox').classList.add('hidden');
  $('loading').classList.remove('hidden');
  try {
    if (state.currency === 'eur' && eurRateStale()) await fetchEurRate();
    const rows = await loaders[state.tab]();
    if (seq !== refreshSeq) return; // er is intussen een nieuwere load gestart (bv. tab-wissel)
    state.rows = rows;
    checkAlerts(rows);
    recordHistory(rows);
    // watchlist altijd op de achtergrond bewaken, ook als een ander tabblad open staat
    if (state.tab !== 'watch' && state.watchlist.length) {
      loadWatch().then((wr) => { checkAlerts(wr); recordHistory(wr); }).catch(() => {});
    }
    render();
    if (rows._notice) {
      const nb = $('errorBox');
      nb.textContent = `ℹ️ ${rows._notice}`;
      nb.classList.remove('hidden');
    }
    $('lastUpdate').textContent = `Bijgewerkt: ${new Date().toLocaleTimeString('nl-NL')}`;
  } catch (e) {
    if (seq !== refreshSeq) return;
    const box = $('errorBox');
    box.textContent = e.rateLimited
      ? '⏳ Even te veel opgevraagd bij de gratis databron (limiet per minuut). De app probeert automatisch opnieuw — meestal binnen een minuut weer data. De reeds getoonde tokens blijven staan.'
      : `⚠️ Data ophalen mislukt: ${e.message}. De vorige data blijft staan; probeer het zo opnieuw.`;
    box.classList.remove('hidden');
    // bij een limiet: iets eerder automatisch opnieuw proberen
    if (e.rateLimited) setTimeout(() => { if (state.tab === 'trending' || state.tab === 'stijgers' || state.tab === 'nieuw') refresh(); }, 20000);
  } finally {
    if (seq === refreshSeq) $('loading').classList.add('hidden');
  }
}

function scheduleAutoRefresh() {
  clearInterval(state.timer);
  if ($('autoRefresh').checked) {
    state.timer = setInterval(refresh, 60000);
  }
}

/* ---------- wallet-koppeling (non-custodial, alleen publiek adres) ---------- */

function short(addr) { return addr.slice(0, 6) + '…' + addr.slice(-4); }

const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

async function connectMetamask() {
  const eth = window.ethereum;
  if (!eth) {
    $('walletStatus').textContent = '';
    if (isMobile) {
      // opent deze pagina in de ingebouwde browser van de MetaMask-app
      showError('Je wordt doorgestuurd naar de MetaMask-app… Lukt dat niet: open de MetaMask-app, tik onderin op "Browser" en typ daar dit adres in.');
      window.location.href = `https://metamask.app.link/dapp/${window.location.host}${window.location.pathname}`;
      return;
    }
    showError('MetaMask niet gevonden. Installeer de officiële extensie via metamask.io en herlaad de pagina.');
    return;
  }
  try {
    const accounts = await eth.request({ method: 'eth_requestAccounts' });
    if (accounts?.length) {
      state.wallets.evm = accounts[0];
      $('walletStatus').textContent = `🦊 ${short(accounts[0])} verbonden`;
      $('btnMetamask').textContent = '🦊 Verbonden';
    }
    eth.on?.('accountsChanged', (acc) => {
      state.wallets.evm = acc?.length ? acc[0] : null;
      $('walletStatus').textContent = acc?.length ? `🦊 ${short(acc[0])} verbonden` : '';
      if (!acc?.length) $('btnMetamask').textContent = '🦊 MetaMask';
    });
  } catch (e) {
    if (e?.code !== 4001) showError(`Wallet-verbinding mislukt: ${e.message || e}`);
  }
}

async function connectPhantom() {
  const ph = window.phantom?.solana || (window.solana?.isPhantom ? window.solana : null);
  if (!ph) {
    if (isMobile) {
      // opent deze pagina in de ingebouwde browser van de Phantom-app
      showError('Je wordt doorgestuurd naar de Phantom-app… Lukt dat niet: open de Phantom-app, ga naar het zoek/verken-tabblad en typ daar dit adres in.');
      window.location.href = `https://phantom.app/ul/browse/${encodeURIComponent(window.location.href)}?ref=${encodeURIComponent(window.location.origin)}`;
      return;
    }
    showError('Phantom niet gevonden. Installeer de officiële extensie via phantom.com en herlaad de pagina.');
    return;
  }
  try {
    const resp = await ph.connect();
    const pk = resp.publicKey.toString();
    state.wallets.sol = pk;
    $('walletStatus').textContent = `👻 ${short(pk)} verbonden`;
    $('btnPhantom').textContent = '👻 Verbonden';
  } catch (e) {
    if (e?.code !== 4001) showError(`Wallet-verbinding mislukt: ${e.message || e}`);
  }
}

function showError(msg) {
  const box = $('errorBox');
  box.textContent = `⚠️ ${msg}`;
  box.classList.remove('hidden');
}

/* Stil opnieuw verbinden bij herladen — zonder popup, alleen als de gebruiker
 * de app eerder al toestemming gaf. */
async function reconnectWallets() {
  try {
    const accounts = await window.ethereum?.request({ method: 'eth_accounts' });
    if (accounts?.length) {
      state.wallets.evm = accounts[0];
      $('walletStatus').textContent = `🦊 ${short(accounts[0])} verbonden`;
      $('btnMetamask').textContent = '🦊 Verbonden';
    }
  } catch { /* geen eerdere toestemming */ }
  try {
    const ph = window.phantom?.solana || (window.solana?.isPhantom ? window.solana : null);
    if (ph) {
      const resp = await ph.connect({ onlyIfTrusted: true });
      state.wallets.sol = resp.publicKey.toString();
      $('walletStatus').textContent = `👻 ${short(state.wallets.sol)} verbonden`;
      $('btnPhantom').textContent = '👻 Verbonden';
    }
  } catch { /* geen eerdere toestemming */ }
}

/* ---------- init ---------- */

function setTab(tab) {
  state.tab = tab;
  document.querySelectorAll('.tab').forEach((t) => t.classList.toggle('active', t.dataset.tab === tab));
  $('searchBar').classList.toggle('hidden', tab !== 'search');
  $('tabNote').classList.toggle('hidden', tab !== 'nieuw');
  $('coinTable').classList.toggle('hidden', tab === 'bot');
  $('botPanel').classList.toggle('hidden', tab !== 'bot');
  $('alertBox').classList.add('hidden');
  state.rows = [];
  if (tab !== 'bot') render();
  else $('emptyState').classList.add('hidden');
  if (tab !== 'search' || state.searchQuery) refresh();
}

/* ---------- bot-dashboard (leest bot/status.json die de Python-bot schrijft) ---------- */

/* Trainingskaart: ranglijst van strategieën + voortgang naar het diploma */
function renderTraining(t) {
  if (!t || !t.ranglijst || !t.ranglijst.length) return '';
  const fmtSol = (v) => (v == null ? '—' : `${v >= 0 ? '+' : ''}${Number(v).toFixed(4).replace('.', ',')}`);

  const eisLabels = {
    genoeg_trades: 'Afgeronde trades',
    genoeg_dagen: 'Trainingsdagen',
    winst: 'Winstgevend',
    win_rate: 'Win-rate',
  };
  const eisen = Object.entries(t.eisen || {}).map(([k, e]) => {
    const nu = k === 'winst' ? fmtSol(e.nu) + ' SOL' : (e.nu ?? 0) + (k === 'win_rate' ? '%' : '');
    const doel = k === 'winst' ? '> 0' : '≥ ' + e.nodig + (k === 'win_rate' ? '%' : '');
    return `<div class="eis ${e.ok ? 'eis-ok' : ''}">
      <span class="eis-check">${e.ok ? '✓' : '·'}</span>
      <span class="eis-naam">${eisLabels[k] || k}</span>
      <span class="eis-waarde">${escapeHtml(String(nu))} <span class="token-sub">/ ${escapeHtml(doel)}</span></span>
    </div>`;
  }).join('');

  const rows = t.ranglijst.map((r, i) => {
    const cls = r.total_sol > 0 ? 'pct-up' : r.total_sol < 0 ? 'pct-down' : 'pct-flat';
    const regels = Object.entries(r.regels || {}).map(([k, v]) => {
      const kort = { koop_drempel_pct: 'koop +', stop_loss_pct: 'SL ', take_profit_pct: 'TP ', trailing_pct: 'trail ' }[k];
      return kort ? kort + v + '%' : '';
    }).filter(Boolean).join(' · ');
    return `<div class="train-row ${i === 0 ? 'train-champ' : ''}">
      <span class="train-rank">${i === 0 ? '🏆' : i + 1}</span>
      <span class="train-name">${escapeHtml(r.naam)}<span class="token-sub"> ${escapeHtml(regels)}</span></span>
      <span class="train-stats token-sub">${r.closed_trades} trades · win ${r.win_rate == null ? '—' : r.win_rate + '%'} · ${r.open_posities} open</span>
      <span class="train-sol ${cls}">${fmtSol(r.total_sol)} SOL</span>
    </div>`;
  }).join('');

  return `
    ${t.geslaagd ? `<div class="grad-banner">🎓 <strong>Training voltooid!</strong> Beste strategie: <strong>${escapeHtml(t.kampioen)}</strong> — voldoet aan alle slagingseisen. Wil je hiermee echt gaan handelen, vraag dan aan Claude om deze strategie over te nemen en volg de stappen in de README (bewust en met klein geld).</div>` : ''}
    <div class="bot-card train-card">
      <h3>🎓 Training — dag ${t.dagen_bezig ?? 0} <span class="token-sub">5 strategieën strijden met nepgeld; de beste telt</span></h3>
      <div class="eisen-grid">${eisen}</div>
      <div class="train-list">${rows}</div>
      <p class="token-sub">Eerlijk: winst in de training garandeert géén winst in het echt — de markt verandert.
      Maar zo zie je zwart-op-wit welke aanpak het beste standhoudt vóór er ook maar één echte euro op het spel staat.</p>
    </div>`;
}

async function renderBotPanel() {
  const panel = $('botPanel');
  let s;
  let isDemo = false;
  try {
    const res = await fetch('bot/status.json', { cache: 'no-store' });
    if (!res.ok) throw new Error();
    s = await res.json();
  } catch {
    // geen bot verbonden (bv. online versie): toon het dashboard met VOORBEELD-data,
    // met een duidelijke banner, zodat het ontwerp overal zichtbaar is.
    isDemo = true;
    s = {
      watching: [{ symbol: 'BONK', change24h: 6.2 }, { symbol: 'WIF', change24h: -2.1 }],
      mode: 'paper', wallet: 'voorbeeld', sol_balance: 1.184, day_spent_sol: 0.15,
      stats: { realized_sol: 0.142, unrealized_sol: 0.042, total_sol: 0.184, wins: 4, losses: 1, closed_trades: 5, win_rate: 80, best_pct: 31.4, worst_pct: -9.8 },
      positions: [
        { symbol: 'POPCAT', entry_price: 0.82, current_price: 0.95, sol_spent: 0.05, pnl_pct: 15.9, opened_at: '' },
        { symbol: 'MEW', entry_price: 0.0071, current_price: 0.0068, sol_spent: 0.05, pnl_pct: -4.2, opened_at: '' },
      ],
      trades: [
        { time: '2026-01-01 11:10:00', side: 'KOOP', symbol: 'BONK', sol: 0.05, reason: '24u +12,0% ≥ +10%', profit_sol: null },
        { time: '2026-01-01 11:55:00', side: 'VERKOOP', symbol: 'BONK', sol: 0.0657, reason: 'take-profit +31,4%', pnl_pct: 31.4, profit_sol: 0.0157 },
        { time: '2026-01-01 12:48:00', side: 'VERKOOP', symbol: 'WIF', sol: 0.0549, reason: 'resultaat +9,8%', pnl_pct: 9.8, profit_sol: 0.0049 },
        { time: '2026-01-01 13:15:00', side: 'VERKOOP', symbol: 'SLERF', sol: 0.0451, reason: 'stop-loss −9,8%', pnl_pct: -9.8, profit_sol: -0.0049 },
      ],
      settings: { koop_drempel_pct: 10, verkoop_drempel_pct: 10, stop_loss_pct: 10, take_profit_pct: 25, per_trade_sol: 0.05, max_posities: 3, max_dag_budget_sol: 0.25 },
      training: {
        dagen_bezig: 4, kampioen: 'Trailing', geslaagd: false,
        eisen: {
          genoeg_trades: { nodig: 20, nu: 11, ok: false },
          genoeg_dagen: { nodig: 7, nu: 4, ok: false },
          winst: { nodig: 0, nu: 0.031, ok: true },
          win_rate: { nodig: 50, nu: 64, ok: true },
        },
        ranglijst: [
          { naam: 'Trailing', regels: { koop_drempel_pct: 10, stop_loss_pct: 10, trailing_pct: 10 }, total_sol: 0.031, win_rate: 64, closed_trades: 11, open_posities: 1 },
          { naam: 'Jouw regel', regels: { koop_drempel_pct: 10, stop_loss_pct: 10, take_profit_pct: 25 }, total_sol: 0.018, win_rate: 55, closed_trades: 9, open_posities: 2 },
          { naam: 'Voorzichtig', regels: { koop_drempel_pct: 10, stop_loss_pct: 5, take_profit_pct: 15 }, total_sol: 0.006, win_rate: 50, closed_trades: 14, open_posities: 1 },
          { naam: 'Streng', regels: { koop_drempel_pct: 20, stop_loss_pct: 10, take_profit_pct: 30 }, total_sol: 0.002, win_rate: 67, closed_trades: 3, open_posities: 0 },
          { naam: 'Gevoelig', regels: { koop_drempel_pct: 5, stop_loss_pct: 8, take_profit_pct: 20 }, total_sol: -0.012, win_rate: 38, closed_trades: 16, open_posities: 2 },
        ],
      },
      error: null, updated_at: '',
    };
  }

  const updated = new Date(String(s.updated_at).replace(' ', 'T'));
  const stale = isNaN(updated) || (Date.now() - updated.getTime()) > 5 * 60000;
  const live = s.mode === 'live';
  const cfg = s.settings || {};

  const posRows = (s.positions || []).map((p) => {
    const pnl = p.pnl_pct;
    const cls = pnl == null ? 'pct-flat' : pnl >= 0 ? 'pct-up' : 'pct-down';
    return `<tr>
      <td>${escapeHtml(p.symbol)}</td>
      <td class="num">${fmtPrice(p.entry_price)}</td>
      <td class="num">${p.current_price ? fmtPrice(p.current_price) : '—'}</td>
      <td class="num"><span class="${cls}">${pnl == null ? '—' : (pnl >= 0 ? '+' : '') + pnl.toFixed(1).replace('.', ',') + '%'}</span></td>
      <td>${escapeHtml(p.opened_at || '')}</td>
    </tr>`;
  }).join('');

  const tradeRows = (s.trades || []).slice().reverse().map((t) => `<tr>
    <td>${escapeHtml(t.time)}</td>
    <td><span class="signal ${t.side === 'KOOP' ? 'signal-buy' : 'signal-sell'}">${escapeHtml(t.side)}</span></td>
    <td>${escapeHtml(t.symbol)}</td>
    <td class="num">${Number(t.sol).toFixed(4).replace('.', ',')} SOL</td>
    <td>${escapeHtml(t.reason)}</td>
    <td>${t.tx ? `<a class="chart-link" href="https://solscan.io/tx/${encodeURIComponent(t.tx)}" target="_blank" rel="noopener noreferrer">tx</a>` : '—'}</td>
  </tr>`).join('');

  const st2 = s.stats || {};
  const total = st2.total_sol ?? 0;
  const totCls = total > 0.0000001 ? 'reward-up' : total < -0.0000001 ? 'reward-down' : 'reward-flat';
  const sign = total > 0 ? '+' : '';
  const fmtSol = (v) => (v == null ? '—' : `${v >= 0 ? '+' : ''}${Number(v).toFixed(4).replace('.', ',')}`);
  const winRate = st2.win_rate;
  const closed = st2.closed_trades ?? 0;
  const posCards = (s.positions || []).map((p) => {
    const pnl = p.pnl_pct;
    const up = pnl != null && pnl >= 0;
    const cls = pnl == null ? 'pct-flat' : up ? 'pct-up' : 'pct-down';
    const barW = pnl == null ? 0 : Math.min(100, Math.abs(pnl));
    return `<div class="pos-card ${up ? 'pos-up' : (pnl != null ? 'pos-down' : '')}">
      <div class="pos-top"><span class="pos-sym">${escapeHtml(p.symbol)}</span>
        <span class="${cls} pos-pnl">${pnl == null ? '—' : (up ? '+' : '') + pnl.toFixed(1).replace('.', ',') + '%'}</span></div>
      <div class="pos-bar"><div class="pos-bar-fill ${up ? 'up' : 'down'}" style="width:${barW}%"></div></div>
      <div class="pos-meta">instap ${fmtPrice(p.entry_price)} → nu ${p.current_price ? fmtPrice(p.current_price) : '—'}</div>
    </div>`;
  }).join('');

  const tradeCards = (s.trades || []).slice().reverse().map((t) => {
    const isSell = t.side === 'VERKOOP';
    const profit = t.profit_sol;
    const pcls = profit == null ? '' : profit >= 0 ? 'pct-up' : 'pct-down';
    return `<div class="trade-row">
      <span class="trade-badge ${isSell ? 'tb-sell' : 'tb-buy'}">${isSell ? '↓ verkoop' : '↑ koop'}</span>
      <span class="trade-sym">${escapeHtml(t.symbol)}</span>
      <span class="trade-reason">${escapeHtml(t.reason)}</span>
      ${profit != null ? `<span class="${pcls} trade-profit">${fmtSol(profit)} SOL</span>` : '<span class="trade-profit token-sub"></span>'}
      <span class="trade-time token-sub">${escapeHtml((t.time || '').slice(11, 16))}</span>
      ${t.tx ? `<a class="chart-link" href="https://solscan.io/tx/${encodeURIComponent(t.tx)}" target="_blank" rel="noopener noreferrer">tx</a>` : ''}
    </div>`;
  }).join('');

  panel.innerHTML = `
    ${isDemo ? `<div class="demo-banner">👁️ <strong>Voorbeeldweergave</strong> — dit is hoe je dashboard eruitziet. Je échte beloningen en trades verschijnen hier zodra je de bot op je eigen computer start (zie de uitleg onderaan).</div>` : ''}
    <div class="reward-hero ${totCls}">
      <div class="reward-label">💰 Totale beloning ${isDemo ? '(voorbeeld)' : live ? '(echt geld)' : '(oefenen)'}</div>
      <div class="reward-big">${sign}${Number(total).toFixed(4).replace('.', ',')} <span class="reward-unit">SOL</span></div>
      <div class="reward-split">
        <span>Gerealiseerd: <strong class="${(st2.realized_sol ?? 0) >= 0 ? 'pct-up' : 'pct-down'}">${fmtSol(st2.realized_sol)} SOL</strong></span>
        <span>Open posities: <strong class="${(st2.unrealized_sol ?? 0) >= 0 ? 'pct-up' : 'pct-down'}">${fmtSol(st2.unrealized_sol)} SOL</strong></span>
      </div>
    </div>

    <div class="stat-tiles">
      <div class="stat-tile">
        <div class="stat-num">${winRate == null ? '—' : Math.round(winRate) + '%'}</div>
        <div class="stat-lbl">Win-rate</div>
        <div class="stat-ring" style="--pct:${winRate ?? 0}"></div>
      </div>
      <div class="stat-tile">
        <div class="stat-num pct-up">${st2.wins ?? 0}</div>
        <div class="stat-lbl">Winst-trades</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num pct-down">${st2.losses ?? 0}</div>
        <div class="stat-lbl">Verlies-trades</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num pct-up">${st2.best_pct == null ? '—' : '+' + Math.round(st2.best_pct) + '%'}</div>
        <div class="stat-lbl">Beste trade</div>
      </div>
      <div class="stat-tile">
        <div class="stat-num">${closed}</div>
        <div class="stat-lbl">Afgerond</div>
      </div>
    </div>

    ${renderTraining(s.training)}

    <div class="bot-grid">
      <div class="bot-card status-card">
        <div class="status-head">
          <span class="mode-pill ${live ? 'mode-live' : 'mode-paper'}">${live ? '🔴 LIVE' : '🟢 OEFENEN'}</span>
          <span class="run-pill ${stale ? 'run-stopped' : 'run-active'}">${stale ? '⏸ gestopt?' : '▶ actief'}</span>
          <span class="status-bal">${s.sol_balance == null ? '?' : Number(s.sol_balance).toFixed(3).replace('.', ',')} SOL${live ? '' : ' nepgeld'}</span>
        </div>
        <div class="rules-row">
          <span class="rule-chip">koop ≥ +${cfg.koop_drempel_pct}%</span>
          <span class="rule-chip">verkoop ≤ −${cfg.verkoop_drempel_pct}%</span>
          <span class="rule-chip">stop-loss ${cfg.stop_loss_pct}%</span>
          <span class="rule-chip">take-profit ${cfg.take_profit_pct}%</span>
          <span class="rule-chip">max ${cfg.max_posities} posities</span>
          <span class="rule-chip">${cfg.per_trade_sol} SOL/trade</span>
        </div>
        <div class="budget-line">Vandaag besteed: ${Number(s.day_spent_sol || 0).toFixed(3).replace('.', ',')} / ${cfg.max_dag_budget_sol ?? '?'} SOL
          <div class="budget-bar"><div class="budget-fill" style="width:${Math.min(100, (s.day_spent_sol || 0) / (cfg.max_dag_budget_sol || 1) * 100)}%"></div></div>
        </div>
        ${s.error ? `<p class="pct-down status-err">${escapeHtml(s.error)}</p>` : ''}
        <p class="token-sub">Wallet ${escapeHtml((s.wallet || '').slice(0, 6))}…${escapeHtml((s.wallet || '').slice(-4))} · bijgewerkt ${escapeHtml((s.updated_at || '').slice(11, 19))}</p>
      </div>

      <div class="bot-card">
        <h3>👀 Bot volgt nu</h3>
        ${(s.watching || []).length ? `<div class="watch-chips">${(s.watching || []).map((w) => {
          const ch = w.change24h;
          const cls = ch == null ? 'pct-flat' : ch >= 0 ? 'pct-up' : 'pct-down';
          const chTxt = ch == null ? '?' : (ch >= 0 ? '+' : '') + ch.toFixed(1).replace('.', ',') + '%';
          return `<span class="watch-chip">${escapeHtml(w.symbol)} <span class="${cls}">${chTxt}</span></span>`;
        }).join('')}</div>
        <p class="token-sub">De bot koopt pas boven +${cfg.koop_drempel_pct}%. Blijft alles daaronder, dan wacht hij bewust — dat is de strategie, geen storing.</p>` : '<p class="token-sub">Nog geen marktdata (eerste ronde loopt of bot gestopt).</p>'}
      </div>

      <div class="bot-card">
        <h3>📊 Open posities (${(s.positions || []).length})</h3>
        ${posCards ? `<div class="pos-grid">${posCards}</div>` : '<p class="token-sub">Geen open posities — de bot wacht op een koopsignaal.</p>'}
      </div>

      <div class="bot-card">
        <h3>🧾 Trade-geschiedenis</h3>
        ${tradeCards ? `<div class="trade-list">${tradeCards}</div>` : '<p class="token-sub">Nog geen trades.</p>'}
      </div>
      ${isDemo ? `<div class="bot-card">
        <h3>🤖 Start je eigen bot voor échte data</h3>
        <p>Bovenstaande cijfers zijn een voorbeeld. De bot draait op je eigen computer (veilig, met je eigen aparte wallet). Starten op je Mac:</p>
        <pre>cd ~/Claude/memecoin-tracker/bot\npython3 bot.py</pre>
        <p>Hij start in <strong>oefenmodus</strong> (nepgeld, echte prijzen). Open daarna de app via <code>localhost:8790</code> en dit dashboard vult zich met je échte beloningen.</p>
      </div>` : ''}
    </div>`;
}

function init() {
  // Zelfherstel: als de browser een oude HTML-versie uit zijn cache toont terwijl
  // dit script nieuwer is, missen er elementen en zou alles vastlopen. Eén keer
  // geforceerd vers laden lost elke oude-cache-situatie automatisch op.
  const required = ['onlySignals', 'tabNote', 'botPanel', 'swapModal', 'chainSel'];
  if (required.some((id) => !document.getElementById(id))) {
    if (!sessionStorage.getItem('mr_healed')) {
      sessionStorage.setItem('mr_healed', '1');
      Promise.allSettled([
        fetch(location.pathname, { cache: 'reload' }),
        fetch('app.js?v=17', { cache: 'reload' }),
        fetch('swap.js?v=17', { cache: 'reload' }),
        fetch('style.css?v=17', { cache: 'reload' }),
      ]).then(() => location.reload());
      return;
    }
  } else {
    sessionStorage.removeItem('mr_healed');
  }

  loadSettings();
  // chain-opties genereren uit de volledige lijst
  const sel = $('chainSel');
  for (const c of CHAINS) {
    const o = document.createElement('option');
    o.value = c.gt; o.textContent = c.label;
    sel.appendChild(o);
  }
  $('threshold').value = state.threshold;
  $('currency').value = state.currency;
  $('sortBy').value = state.sortBy;
  $('onlySignals').checked = state.onlySignals;
  sel.value = state.chain;
  sel.addEventListener('change', () => {
    state.chain = sel.value;
    saveSettings();
    // chain-keuze raakt alle on-chain tabbladen
    if (['trending', 'stijgers', 'nieuw'].includes(state.tab)) refresh();
  });
  saveWatchlist(); // teller bijwerken

  document.querySelectorAll('.tab').forEach((t) =>
    t.addEventListener('click', () => setTab(t.dataset.tab))
  );

  $('threshold').addEventListener('change', () => {
    const v = parseFloat($('threshold').value);
    state.threshold = (isNaN(v) || v <= 0) ? 10 : v;
    $('threshold').value = state.threshold;
    saveSettings();
    render();
  });

  $('currency').addEventListener('change', async () => {
    state.currency = $('currency').value;
    saveSettings();
    if (state.currency === 'eur' && eurRateStale()) await fetchEurRate();
    render();
  });

  $('sortBy').addEventListener('change', () => { state.sortBy = $('sortBy').value; saveSettings(); render(); });
  $('onlySignals').addEventListener('change', () => { state.onlySignals = $('onlySignals').checked; saveSettings(); render(); });
  $('autoRefresh').addEventListener('change', scheduleAutoRefresh);
  $('btnRefresh').addEventListener('click', refresh);

  $('btnSearch').addEventListener('click', () => {
    state.searchQuery = $('searchInput').value;
    refresh();
  });
  $('searchInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { state.searchQuery = $('searchInput').value; refresh(); }
  });

  $('btnMetamask').addEventListener('click', connectMetamask);
  $('btnPhantom').addEventListener('click', connectPhantom);

  // rate-limit sparen: niet verversen terwijl het venster onzichtbaar is
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) clearInterval(state.timer);
    else { scheduleAutoRefresh(); refresh(); }
  });

  scheduleAutoRefresh();
  reconnectWallets();
  refresh();

  // Ruim elke eerder geïnstalleerde service worker + cache op. Die veroorzaakten
  // dat oude/kapotte versies op het apparaat bleven plakken. Een trading-app moet
  // altijd vers laden — dus geen enkele cachelaag meer.
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations()
      .then((regs) => regs.forEach((r) => r.unregister()))
      .catch(() => {});
  }
  if (window.caches && caches.keys) {
    caches.keys().then((keys) => keys.forEach((k) => caches.delete(k))).catch(() => {});
  }
}

init();
