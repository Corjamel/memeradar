/* swap.js — direct kopen/verkopen in de app (non-custodial)
 *
 * Solana : offerte + transactie via Jupiter Swap API, ondertekenen met Phantom
 * EVM    : offerte + transactie via ParaSwap API, ondertekenen met MetaMask
 *
 * Veiligheid: de app bouwt alleen de transactie; ondertekenen en versturen doet
 * de wallet van de gebruiker. Phantom simuleert elke transactie vóór ondertekening,
 * MetaMask toont de tokenbewegingen. Er worden geen extra kosten toegevoegd.
 */

'use strict';

const JUP_QUOTE_BASES = ['https://lite-api.jup.ag/swap/v1', 'https://quote-api.jup.ag/v6'];
const SOL_MINT = 'So11111111111111111111111111111111111111112';
const SOL_RPC = 'https://solana-rpc.publicnode.com';
const JUP_TOKENS_V2 = 'https://lite-api.jup.ag/tokens/v2/search?query=';
const PARASWAP = 'https://api.paraswap.io';
const ETH_NATIVE = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE';

const EVM_CHAINS = {
  ethereum:  { id: 1,     hex: '0x1',    native: 'ETH',  explorer: 'https://etherscan.io/tx/' },
  bsc:       { id: 56,    hex: '0x38',   native: 'BNB',  explorer: 'https://bscscan.com/tx/' },
  polygon:   { id: 137,   hex: '0x89',   native: 'POL',  explorer: 'https://polygonscan.com/tx/' },
  base:      { id: 8453,  hex: '0x2105', native: 'ETH',  explorer: 'https://basescan.org/tx/' },
  arbitrum:  { id: 42161, hex: '0xa4b1', native: 'ETH',  explorer: 'https://arbiscan.io/tx/' },
  optimism:  { id: 10,    hex: '0xa',    native: 'ETH',  explorer: 'https://optimistic.etherscan.io/tx/' },
  avalanche: { id: 43114, hex: '0xa86a', native: 'AVAX', explorer: 'https://snowtrace.io/tx/' },
};

const swap = {
  row: null,          // token-rij uit de tabel
  side: 'buy',        // 'buy' | 'sell'
  decimals: null,     // decimalen van het token
  quote: null,        // laatste geldige offerte
  quoteSeq: 0,
  busy: false,
  debounce: null,
};

const decimalsCache = new Map();

/* ---------- eenheden: exact rekenen met BigInt (geen zwevendekomma-fouten) ---------- */

function toBaseUnits(amountStr, decimals) {
  const s = String(amountStr).trim().replace(',', '.');
  if (!/^\d*\.?\d*$/.test(s) || s === '' || s === '.') return null;
  const [int, frac = ''] = s.split('.');
  const fracPadded = (frac + '0'.repeat(decimals)).slice(0, decimals);
  try {
    const v = BigInt(int || '0') * (10n ** BigInt(decimals)) + BigInt(fracPadded || '0');
    return v > 0n ? v : null;
  } catch { return null; }
}

function fromBaseUnits(raw, decimals, maxFrac = 6) {
  const v = BigInt(raw);
  const div = 10n ** BigInt(decimals);
  const int = v / div;
  const frac = (v % div).toString().padStart(decimals, '0').slice(0, maxFrac).replace(/0+$/, '');
  return frac ? `${int},${frac}` : int.toString();
}

/* ---------- token-decimalen opvragen ---------- */

async function getSolDecimals(mint) {
  const key = `sol:${mint}`;
  if (decimalsCache.has(key)) return decimalsCache.get(key);
  let dec = null;
  try {
    const res = await fetch(SOL_RPC, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'getTokenSupply', params: [mint] }),
    });
    const d = await res.json();
    if (typeof d?.result?.value?.decimals === 'number') dec = d.result.value.decimals;
  } catch { /* probeer fallback */ }
  if (dec == null) {
    const res = await fetch(JUP_TOKENS_V2 + encodeURIComponent(mint));
    const d = await res.json();
    const hit = Array.isArray(d) ? d.find((t) => t.id === mint) : null;
    if (typeof hit?.decimals === 'number') dec = hit.decimals;
  }
  if (dec == null) throw new Error('kon token-decimalen niet opvragen');
  decimalsCache.set(key, dec);
  return dec;
}

async function getEvmDecimals(chain, token) {
  const key = `${chain}:${token}`;
  if (decimalsCache.has(key)) return decimalsCache.get(key);
  // decimals() — standaard ERC-20 selector 0x313ce567, uitgelezen via de wallet-RPC
  const r = await window.ethereum.request({
    method: 'eth_call',
    params: [{ to: token, data: '0x313ce567' }, 'latest'],
  });
  const dec = parseInt(r, 16);
  if (isNaN(dec) || dec > 36) throw new Error('kon token-decimalen niet uitlezen');
  decimalsCache.set(key, dec);
  return dec;
}

/* ---------- offertes ---------- */

async function jupQuote(inputMint, outputMint, amountRaw, slippageBps) {
  let lastErr;
  for (const base of JUP_QUOTE_BASES) {
    try {
      const url = `${base}/quote?inputMint=${inputMint}&outputMint=${outputMint}` +
        `&amount=${amountRaw}&slippageBps=${slippageBps}&restrictIntermediateTokens=true`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Jupiter ${res.status}`);
      const q = await res.json();
      if (!q.outAmount) throw new Error(q.error || 'geen route gevonden');
      return { base, q };
    } catch (e) { lastErr = e; }
  }
  throw lastErr;
}

async function paraswapQuote(chain, srcToken, srcDec, destToken, destDec, amountRaw) {
  const net = EVM_CHAINS[chain].id;
  const url = `${PARASWAP}/prices/?srcToken=${srcToken}&destToken=${destToken}` +
    `&amount=${amountRaw}&srcDecimals=${srcDec}&destDecimals=${destDec}&side=SELL&network=${net}`;
  const res = await fetch(url);
  const d = await res.json();
  if (!res.ok || !d.priceRoute) throw new Error(d.error || `ParaSwap ${res.status}`);
  return d.priceRoute;
}

/* ---------- UI-elementen ---------- */

const S = (id) => document.getElementById(id);

function nativeSymbol(row) {
  return row.chainId === 'solana' ? 'SOL' : (EVM_CHAINS[row.chainId]?.native ?? '?');
}

function setStatus(msg, kind = '') {
  const el = S('swapStatus');
  el.className = `swap-status ${kind}`;
  el.innerHTML = msg;
}

function setConfirmEnabled(on) { S('swapConfirm').disabled = !on; }

/* ---------- modal openen/sluiten ---------- */

window.openSwap = async function openSwap(key, side) {
  const row = state.rows.find((r) => rowKey(r) === key);
  if (!row || row.source !== 'dex') return;
  if (row.chainId !== 'solana' && !EVM_CHAINS[row.chainId]) {
    showError(`Direct handelen wordt (nog) niet ondersteund op ${row.chainId}. Gebruik de Grafiek-knop.`);
    return;
  }
  swap.row = row; swap.side = side; swap.quote = null; swap.decimals = null; swap.busy = false;

  S('swapTitle').textContent = `${side === 'buy' ? 'Koop' : 'Verkoop'} ${row.symbol}`;
  S('swapTitle').className = side === 'buy' ? 'buy-title' : 'sell-title';
  let drukTxt = '';
  if (row.buys1h != null && row.sells1h != null && row.buys1h + row.sells1h > 0) {
    const pct = Math.round((row.buys1h / (row.buys1h + row.sells1h)) * 100);
    drukTxt = ` · druk 1u: ${pct}% koop`;
  }
  S('swapTokenInfo').textContent =
    `${row.name} · ${row.chainId} · prijs ${fmtPrice(row.priceUsd)} · liquiditeit ${fmtBig(row.liquidity)}${drukTxt}`;
  S('swapAmount').value = '';
  S('swapUnit').textContent = side === 'buy' ? nativeSymbol(row) : row.symbol;
  S('swapQuote').innerHTML = '';
  S('swapImpactWarn').classList.add('hidden');
  setStatus('');
  setConfirmEnabled(false);
  updateWalletWarn();
  S('swapModal').classList.remove('hidden');
  S('swapAmount').focus();

  // risico-herinnering bij verse of illiquide tokens
  const risk = computeRisk(row);
  S('swapRisk').textContent = risk.cls === 'risk-high'
    ? '⚠️ Hoog risico: weinig liquiditeit of zeer nieuw token. Grote kans op rug-pull of extreme slippage.'
    : '';

  try {
    swap.decimals = row.chainId === 'solana'
      ? await getSolDecimals(row.address)
      : null; // EVM: pas uitlezen na netwerk-switch, bij offerte
  } catch { /* wordt opnieuw geprobeerd bij offerte */ }
};

function closeSwap() {
  S('swapModal').classList.add('hidden');
  clearTimeout(swap.debounce);
  swap.row = null; swap.quote = null;
}

function walletFor(row) {
  return row.chainId === 'solana' ? state.wallets.sol : state.wallets.evm;
}

function updateWalletWarn() {
  const warn = S('swapWalletWarn');
  if (!swap.row) return;
  if (walletFor(swap.row)) { warn.classList.add('hidden'); return; }
  const isSol = swap.row.chainId === 'solana';
  warn.innerHTML = `Verbind eerst je ${isSol ? 'Phantom' : 'MetaMask'}-wallet om te kunnen handelen. `;
  const btn = document.createElement('button');
  btn.className = 'btn small';
  btn.textContent = isSol ? '👻 Verbind Phantom' : '🦊 Verbind MetaMask';
  btn.addEventListener('click', async () => {
    if (isSol) await connectPhantom(); else await connectMetamask();
    updateWalletWarn();
    maybeQuote();
  });
  warn.appendChild(btn);
  warn.classList.remove('hidden');
}

/* ---------- offerte ophalen (debounced bij typen) ---------- */

function slippageBps() { return Math.round(parseFloat(S('swapSlippage').value) * 100); }

function maybeQuote() {
  clearTimeout(swap.debounce);
  swap.debounce = setTimeout(fetchQuote, 600);
}

async function fetchQuote() {
  if (!swap.row || swap.busy) return;
  const seq = ++swap.quoteSeq;
  const row = swap.row;
  swap.quote = null;
  setConfirmEnabled(false);
  S('swapImpactWarn').classList.add('hidden');

  const amountStr = S('swapAmount').value;
  if (!amountStr.trim()) { S('swapQuote').innerHTML = ''; setStatus(''); return; }
  setStatus('Offerte ophalen…');

  try {
    if (row.chainId === 'solana') {
      if (swap.decimals == null) swap.decimals = await getSolDecimals(row.address);
      const inDec = swap.side === 'buy' ? 9 : swap.decimals;
      const outDec = swap.side === 'buy' ? swap.decimals : 9;
      const amountRaw = toBaseUnits(amountStr, inDec);
      if (amountRaw == null) { setStatus('Ongeldig bedrag', 'err'); return; }
      const inputMint = swap.side === 'buy' ? SOL_MINT : row.address;
      const outputMint = swap.side === 'buy' ? row.address : SOL_MINT;
      const { base, q } = await jupQuote(inputMint, outputMint, amountRaw.toString(), slippageBps());
      if (seq !== swap.quoteSeq) return;
      swap.quote = { kind: 'sol', base, q, outDec };
      const outSym = swap.side === 'buy' ? row.symbol : 'SOL';
      const impact = parseFloat(q.priceImpactPct || '0') * 100;
      renderQuote([
        ['Je ontvangt (verwacht)', `≈ ${fromBaseUnits(q.outAmount, outDec)} ${outSym}`],
        ['Minimaal (na slippage)', `${fromBaseUnits(q.otherAmountThreshold, outDec)} ${outSym}`],
        ['Prijsimpact', `${impact.toFixed(2).replace('.', ',')}%`],
        ['Route', 'Jupiter (beste route over Solana-DEX\'en)'],
      ], impact);
    } else {
      const wallet = state.wallets.evm;
      if (!wallet) { setStatus('Verbind eerst MetaMask (hierboven).', 'err'); return; }
      await ensureChain(row.chainId);
      const tokenDec = await getEvmDecimals(row.chainId, row.address);
      if (seq !== swap.quoteSeq) return;
      swap.decimals = tokenDec;
      const src = swap.side === 'buy' ? ETH_NATIVE : row.address;
      const dst = swap.side === 'buy' ? row.address : ETH_NATIVE;
      const srcDec = swap.side === 'buy' ? 18 : tokenDec;
      const dstDec = swap.side === 'buy' ? tokenDec : 18;
      const amountRaw = toBaseUnits(amountStr, srcDec);
      if (amountRaw == null) { setStatus('Ongeldig bedrag', 'err'); return; }
      const pr = await paraswapQuote(row.chainId, src, srcDec, dst, dstDec, amountRaw.toString());
      if (seq !== swap.quoteSeq) return;
      swap.quote = { kind: 'evm', pr, srcDec, dstDec, amountRaw };
      const outSym = swap.side === 'buy' ? row.symbol : EVM_CHAINS[row.chainId].native;
      const slip = slippageBps();
      const minOut = (BigInt(pr.destAmount) * BigInt(10000 - slip)) / 10000n;
      const srcUSD = parseFloat(pr.srcUSD), destUSD = parseFloat(pr.destUSD);
      const impact = (srcUSD > 0 && destUSD > 0) ? Math.max(0, (1 - destUSD / srcUSD) * 100) : 0;
      renderQuote([
        ['Je ontvangt (verwacht)', `≈ ${fromBaseUnits(pr.destAmount, dstDec)} ${outSym}`],
        ['Minimaal (na slippage)', `${fromBaseUnits(minOut, dstDec)} ${outSym}`],
        ['Waarde', `$${srcUSD.toFixed(2)} → $${destUSD.toFixed(2)} (excl. gas ≈ $${parseFloat(pr.gasCostUSD || '0').toFixed(2)})`],
        ['Route', 'ParaSwap (beste route over DEX\'en)'],
      ], impact);
    }
    setStatus('');
    setConfirmEnabled(!!walletFor(row));
  } catch (e) {
    if (seq !== swap.quoteSeq) return;
    setStatus(`Offerte mislukt: ${escapeHtml(e.message || String(e))}`, 'err');
  }
}

function renderQuote(pairs, impactPct) {
  S('swapQuote').innerHTML = pairs
    .map(([k, v]) => `<div class="q-row"><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`)
    .join('');
  if (impactPct >= 5) {
    const w = S('swapImpactWarn');
    w.textContent = `⚠️ Hoge prijsimpact (${impactPct.toFixed(1).replace('.', ',')}%): jouw order beweegt de prijs flink. Overweeg een kleiner bedrag.`;
    w.classList.remove('hidden');
  }
}

/* ---------- uitvoeren ---------- */

async function ensureChain(chain) {
  const target = EVM_CHAINS[chain];
  const current = await window.ethereum.request({ method: 'eth_chainId' });
  if (current === target.hex) return;
  try {
    await window.ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: target.hex }],
    });
  } catch (e) {
    if (e?.code === 4902) throw new Error(`voeg het ${chain}-netwerk eerst toe in MetaMask`);
    throw e;
  }
}

async function waitForReceipt(txHash, timeoutMs = 180000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    const r = await window.ethereum.request({ method: 'eth_getTransactionReceipt', params: [txHash] });
    if (r) {
      if (r.status === '0x0') throw new Error('transactie is on-chain mislukt (reverted)');
      return r;
    }
    await new Promise((res) => setTimeout(res, 3000));
  }
  throw new Error('wachten op bevestiging duurde te lang — controleer je wallet');
}

async function executeSwap() {
  if (!swap.quote || swap.busy || !swap.row) return;
  const row = swap.row;
  swap.busy = true;
  setConfirmEnabled(false);

  try {
    if (swap.quote.kind === 'sol') {
      const ph = window.phantom?.solana || (window.solana?.isPhantom ? window.solana : null);
      if (!ph) throw new Error('Phantom niet gevonden');
      setStatus('Transactie bouwen via Jupiter…');
      const res = await fetch(`${swap.quote.base}/swap`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          quoteResponse: swap.quote.q,
          userPublicKey: state.wallets.sol,
          wrapAndUnwrapSol: true,
          dynamicComputeUnitLimit: true,
        }),
      });
      const d = await res.json();
      if (!res.ok || !d.swapTransaction) throw new Error(d.error || 'transactie bouwen mislukt');
      const bytes = Uint8Array.from(atob(d.swapTransaction), (c) => c.charCodeAt(0));
      const vtx = solanaWeb3.VersionedTransaction.deserialize(bytes);
      setStatus('✍️ Bevestig de transactie in Phantom — controleer daar wat je ontvangt…');
      const { signature } = await ph.signAndSendTransaction(vtx);
      setStatus(
        `✅ Verstuurd! <a href="https://solscan.io/tx/${encodeURIComponent(signature)}" target="_blank" rel="noopener noreferrer">Bekijk op Solscan</a>`,
        'ok'
      );
    } else {
      const { pr, srcDec, dstDec, amountRaw } = swap.quote;
      const wallet = state.wallets.evm;
      await ensureChain(row.chainId);

      // verkoop van een ERC-20: eerst (exacte) goedkeuring als de allowance te laag is
      if (swap.side === 'sell') {
        const spender = pr.tokenTransferProxy;
        const allowData = '0xdd62ed3e' + wallet.slice(2).toLowerCase().padStart(64, '0') +
          spender.slice(2).toLowerCase().padStart(64, '0');
        const allowHex = await window.ethereum.request({
          method: 'eth_call', params: [{ to: row.address, data: allowData }, 'latest'],
        });
        if (BigInt(allowHex) < amountRaw) {
          setStatus('Stap 1/2 — ✍️ keur in MetaMask het exacte verkoopbedrag goed…');
          const approveData = '0x095ea7b3' + spender.slice(2).toLowerCase().padStart(64, '0') +
            amountRaw.toString(16).padStart(64, '0');
          const approveTx = await window.ethereum.request({
            method: 'eth_sendTransaction',
            params: [{ from: wallet, to: row.address, data: approveData }],
          });
          setStatus('Stap 1/2 — wachten tot de goedkeuring on-chain bevestigd is…');
          await waitForReceipt(approveTx);
        }
      }

      setStatus(`${swap.side === 'sell' ? 'Stap 2/2 — ' : ''}Transactie bouwen via ParaSwap…`);
      const net = EVM_CHAINS[row.chainId].id;
      const body = {
        srcToken: swap.side === 'buy' ? ETH_NATIVE : row.address,
        destToken: swap.side === 'buy' ? row.address : ETH_NATIVE,
        srcAmount: amountRaw.toString(),
        srcDecimals: srcDec,
        destDecimals: dstDec,
        priceRoute: pr,
        userAddress: wallet,
        slippage: slippageBps(),
      };
      const res = await fetch(`${PARASWAP}/transactions/${net}`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      });
      const tx = await res.json();
      if (!res.ok || !tx.to) throw new Error(tx.error || 'transactie bouwen mislukt');
      setStatus('✍️ Bevestig de transactie in MetaMask — controleer daar de tokenbewegingen…');
      const txHash = await window.ethereum.request({
        method: 'eth_sendTransaction',
        params: [{
          from: wallet,
          to: tx.to,
          data: tx.data,
          value: '0x' + BigInt(tx.value || '0').toString(16),
        }],
      });
      setStatus('Wachten op on-chain bevestiging…');
      await waitForReceipt(txHash);
      setStatus(
        `✅ Bevestigd! <a href="${EVM_CHAINS[row.chainId].explorer}${encodeURIComponent(txHash)}" target="_blank" rel="noopener noreferrer">Bekijk op explorer</a>`,
        'ok'
      );
    }
  } catch (e) {
    const cancelled = e?.code === 4001 || /reject|denied|cancell?ed/i.test(e?.message || '');
    setStatus(cancelled ? 'Geannuleerd — er is niets verstuurd.' : `⚠️ ${escapeHtml(e.message || String(e))}`, cancelled ? '' : 'err');
  } finally {
    swap.busy = false;
    setConfirmEnabled(!!swap.quote);
  }
}

/* ---------- events ---------- */

if (S('swapModal')) { // ontbreekt alleen bij een verouderde HTML-cache; app.js herstelt die
  S('swapClose').addEventListener('click', closeSwap);
  S('swapModal').addEventListener('click', (e) => { if (e.target === S('swapModal')) closeSwap(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeSwap(); });
  S('swapAmount').addEventListener('input', maybeQuote);
  S('swapSlippage').addEventListener('change', maybeQuote);
  S('swapConfirm').addEventListener('click', executeSwap);
}
