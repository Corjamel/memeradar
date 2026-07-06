#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MemeRadar-bot — automatisch handelen op Solana volgens de 10%-regel.

Veiligheidsontwerp:
  * De bot gebruikt een EIGEN wallet (bot/wallet.json) — nooit je hoofdwallet.
    Stort er alleen een klein bedrag op dat je volledig kunt missen.
  * Standaard 'paper'-modus: echte prijzen, nepgeld. Live handelen vereist twee
    bewuste stappen in config.json (mode="live" én ik_begrijp_het_risico=true).
  * Harde limieten: bedrag per trade, dagbudget, max posities, stop-loss,
    take-profit, minimale liquiditeit/volume/leeftijd, maximale prijsimpact.
  * Alle trades worden gelogd; de app toont live de status (tabblad 🤖 Bot).

Strategie (instelbaar in config.json):
  KOOP    als 24u-verandering >= +10% (en alle risicofilters slagen)
  VERKOOP als 24u-verandering <= -10%, of stop-loss/take-profit t.o.v. instap.
"""

import base64
import json
import os
import signal
import sys
import time
import urllib.request
import urllib.error
from datetime import date

from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")
# de sleutel staat bewust BUITEN de map die de webserver serveert
WALLET_DIR = os.path.expanduser("~/.memeradar")
WALLET_PATH = os.path.join(WALLET_DIR, "wallet.json")
_OLD_WALLET = os.path.join(HERE, "wallet.json")
STATE_PATH = os.path.join(HERE, "state.json")
STATUS_PATH = os.path.join(HERE, "status.json")
PID_PATH = os.path.join(HERE, "bot.pid")

RPC = "https://solana-rpc.publicnode.com"
JUP = "https://lite-api.jup.ag/swap/v1"
JUP_TOKENS = "https://lite-api.jup.ag/tokens/v2/search?query="
DEX = "https://api.dexscreener.com"
SOL_MINT = "So11111111111111111111111111111111111111112"
LAMPORTS = 1_000_000_000

TRUSTED_QUOTES = {
    "SOL", "WSOL", "USDC", "USDT", "DAI", "FDUSD", "USD1",
}

running = True


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------- HTTP zonder externe libraries ----------

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) MemeRadarBot/1.0"


def http_json(url, payload=None, tries=3):
    last = None
    for _ in range(tries):
        try:
            if payload is not None:
                req = urllib.request.Request(
                    url, data=json.dumps(payload).encode(),
                    headers={"content-type": "application/json", "user-agent": UA})
            else:
                req = urllib.request.Request(
                    url, headers={"accept": "application/json", "user-agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001 — netwerk mag nooit de bot doden
            last = e
            time.sleep(2)
    raise RuntimeError(f"HTTP mislukt voor {url.split('?')[0]}: {last}")


def rpc(method, params):
    d = http_json(RPC, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    if "error" in d:
        raise RuntimeError(f"RPC {method}: {d['error']}")
    return d["result"]


# ---------- wallet ----------

def load_or_create_wallet():
    os.makedirs(WALLET_DIR, mode=0o700, exist_ok=True)
    if os.path.exists(_OLD_WALLET) and not os.path.exists(WALLET_PATH):
        os.rename(_OLD_WALLET, WALLET_PATH)  # migratie: weg uit de servermap
    if os.path.exists(WALLET_PATH):
        with open(WALLET_PATH) as f:
            kp = Keypair.from_bytes(bytes(json.load(f)))
        return kp, False
    kp = Keypair()
    with open(WALLET_PATH, "w") as f:
        json.dump(list(bytes(kp)), f)
    os.chmod(WALLET_PATH, 0o600)
    return kp, True


def sol_balance(pubkey):
    return rpc("getBalance", [str(pubkey)])["value"] / LAMPORTS


def token_balance_raw(pubkey, mint):
    res = rpc("getTokenAccountsByOwner",
              [str(pubkey), {"mint": mint}, {"encoding": "jsonParsed"}])
    total = 0
    for acc in res["value"]:
        total += int(acc["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"])
    return total


# ---------- marktdata (DexScreener, met vertrouwde-pool-keuze) ----------

def best_pair(pairs):
    def key(p):
        trusted = (p.get("quoteToken", {}).get("symbol", "").upper() in TRUSTED_QUOTES)
        vol = (p.get("volume") or {}).get("h24") or 0
        liq = (p.get("liquidity") or {}).get("usd") or 0
        return (1 if trusted else 0, vol, liq)
    pairs = [p for p in pairs if p.get("chainId") == "solana"]
    return max(pairs, key=key) if pairs else None


def fetch_market_jup(mints):
    """Primaire bron: Jupiter tokens v2 — geverifieerde geaggregeerde prijzen,
    niet te manipuleren met één nep-pool."""
    out = {}
    for i in range(0, len(mints), 20):
        batch = mints[i:i + 20]
        toks = http_json(f"{JUP_TOKENS}{','.join(batch)}")
        for t in toks or []:
            if t.get("id") not in batch:
                continue
            s24 = t.get("stats24h") or {}
            age = None
            created = (t.get("firstPool") or {}).get("createdAt")
            if created:
                try:
                    age = (time.time() - time.mktime(
                        time.strptime(created, "%Y-%m-%dT%H:%M:%SZ"))) / 86400
                except ValueError:
                    pass
            out[t["id"]] = {
                "symbol": t.get("symbol", "?"),
                "price": float(t.get("usdPrice") or 0),
                "change24h": s24.get("priceChange"),
                "liquidity": t.get("liquidity") or 0,
                "volume24h": (s24.get("buyVolume") or 0) + (s24.get("sellVolume") or 0),
                "age_days": age,
                "verified": t.get("isVerified"),
                "organic": t.get("organicScoreLabel"),
            }
    if not out:
        raise RuntimeError("geen tokendata van Jupiter")
    return out


def fetch_market_dex(mints):
    """Reservebron: DexScreener (beste pool met vertrouwd quote-token)."""
    out = {}
    for i in range(0, len(mints), 30):
        batch = mints[i:i + 30]
        pairs = http_json(f"{DEX}/tokens/v1/solana/{','.join(batch)}")
        by_mint = {}
        for p in pairs or []:
            m = p.get("baseToken", {}).get("address")
            if m in batch:
                by_mint.setdefault(m, []).append(p)
        for m, ps in by_mint.items():
            p = best_pair(ps)
            if not p:
                continue
            out[m] = {
                "symbol": p["baseToken"].get("symbol", "?"),
                "price": float(p.get("priceUsd") or 0),
                "change24h": ((p.get("priceChange") or {}).get("h24")),
                "liquidity": ((p.get("liquidity") or {}).get("usd") or 0),
                "volume24h": ((p.get("volume") or {}).get("h24") or 0),
                "age_days": ((time.time() * 1000 - p["pairCreatedAt"]) / 86400000
                             if p.get("pairCreatedAt") else None),
                "verified": None,
                "organic": None,
            }
    return out


def fetch_market(mints):
    try:
        return fetch_market_jup(mints)
    except Exception as e:  # noqa: BLE001
        log(f"Jupiter-tokendata mislukt ({e}) — terugvallen op DexScreener")
        return fetch_market_dex(mints)


def auto_scan_mints(cfg):
    """Optioneel: boosted Solana-tokens die aan de risicofilters voldoen."""
    boosts = http_json(f"{DEX}/token-boosts/top/v1")
    mints = [b["tokenAddress"] for b in boosts
             if b.get("chainId") == "solana" and b.get("tokenAddress")][:20]
    market = fetch_market(mints)
    ok = [m for m, d in market.items() if passes_filters(d, cfg, from_scan=True)]
    return ok[:10]


def passes_filters(d, cfg, from_scan=False):
    if d["liquidity"] < cfg["min_liquiditeit_usd"]:
        return False
    if d["volume24h"] < cfg["min_volume_24u_usd"]:
        return False
    if d["age_days"] is not None and d["age_days"] < cfg["min_leeftijd_dagen"]:
        return False
    # expliciet niet-geverifieerd token nooit kopen (instelbaar)
    if cfg.get("alleen_geverifieerde_tokens", True) and d.get("verified") is False:
        return False
    # zelf gevonden (auto-scan) tokens: strengere eisen dan je eigen lijst
    if from_scan and (d.get("verified") is not True or d.get("organic") == "low"):
        return False
    return True


# ---------- uitvoering (Jupiter) ----------

def jup_quote(input_mint, output_mint, amount_raw, slippage_bps):
    q = http_json(f"{JUP}/quote?inputMint={input_mint}&outputMint={output_mint}"
                  f"&amount={amount_raw}&slippageBps={slippage_bps}"
                  f"&restrictIntermediateTokens=true")
    if not q.get("outAmount"):
        raise RuntimeError(q.get("error", "geen route"))
    return q


def execute_swap(kp, quote):
    d = http_json(f"{JUP}/swap", {
        "quoteResponse": quote,
        "userPublicKey": str(kp.pubkey()),
        "wrapAndUnwrapSol": True,
        "dynamicComputeUnitLimit": True,
    })
    if not d.get("swapTransaction"):
        raise RuntimeError(d.get("error", "swap bouwen mislukt"))
    raw = base64.b64decode(d["swapTransaction"])
    tx = VersionedTransaction.from_bytes(raw)
    signed = VersionedTransaction(tx.message, [kp])
    sig = rpc("sendTransaction", [
        base64.b64encode(bytes(signed)).decode(),
        {"encoding": "base64", "skipPreflight": False, "maxRetries": 3},
    ])
    # wachten op bevestiging
    for _ in range(40):
        st = rpc("getSignatureStatuses", [[sig]])["value"][0]
        if st and st.get("err"):
            raise RuntimeError(f"transactie mislukt on-chain: {st['err']}")
        if st and st.get("confirmationStatus") in ("confirmed", "finalized"):
            return sig
        time.sleep(3)
    raise RuntimeError("bevestiging duurde te lang — controleer solscan.io")


# ---------- staat ----------

def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"positions": {}, "trades": [], "day": "", "day_spent_sol": 0.0,
            "paper_sol": None, "cooldown": {}}


def save_state(st):
    with open(STATE_PATH, "w") as f:
        json.dump(st, f, indent=1)


def write_status(cfg, st, kp, market, balance, error=None):
    positions = []
    for mint, pos in st["positions"].items():
        cur = market.get(mint, {}).get("price")
        pnl = ((cur / pos["entry_price"]) - 1) * 100 if cur and pos["entry_price"] else None
        positions.append({**pos, "mint": mint, "current_price": cur, "pnl_pct": pnl})
    watching = [{"symbol": d["symbol"], "change24h": d["change24h"], "price": d["price"]}
                for d in market.values()]

    # beloningen: gerealiseerde winst en prestaties uit alle afgeronde verkopen
    sells = [t for t in st["trades"] if t["side"] == "VERKOOP" and t.get("profit_sol") is not None]
    realized_sol = sum(t["profit_sol"] for t in sells)
    wins = sum(1 for t in sells if t["profit_sol"] > 0)
    losses = sum(1 for t in sells if t["profit_sol"] <= 0)
    win_rate = (wins / len(sells) * 100) if sells else None
    best = max((t["pnl_pct"] for t in sells if t.get("pnl_pct") is not None), default=None)
    worst = min((t["pnl_pct"] for t in sells if t.get("pnl_pct") is not None), default=None)
    unrealized_sol = sum((p["current_price"] / p["entry_price"] - 1) * p["sol_spent"]
                         for p in positions
                         if p.get("current_price") and p.get("entry_price"))
    stats = {
        "realized_sol": round(realized_sol, 6),
        "unrealized_sol": round(unrealized_sol, 6),
        "total_sol": round(realized_sol + unrealized_sol, 6),
        "wins": wins, "losses": losses, "closed_trades": len(sells),
        "win_rate": round(win_rate, 0) if win_rate is not None else None,
        "best_pct": best, "worst_pct": worst,
    }

    with open(STATUS_PATH, "w") as f:
        json.dump({
            "watching": watching,
            "mode": cfg["mode"],
            "wallet": str(kp.pubkey()),
            "sol_balance": balance,
            "day_spent_sol": st["day_spent_sol"],
            "stats": stats,
            "positions": positions,
            "trades": st["trades"][-20:],
            "settings": {k: cfg[k] for k in (
                "koop_drempel_pct", "verkoop_drempel_pct", "stop_loss_pct",
                "take_profit_pct", "per_trade_sol", "max_posities",
                "max_dag_budget_sol")},
            "error": error,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=1)


def record_trade(st, side, mint, symbol, sol_amount, price, reason, sig=None,
                 pnl_pct=None, profit_sol=None):
    st["trades"].append({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"), "side": side, "mint": mint,
        "symbol": symbol, "sol": round(sol_amount, 6), "price": price,
        "reason": reason, "tx": sig,
        "pnl_pct": round(pnl_pct, 1) if pnl_pct is not None else None,
        "profit_sol": round(profit_sol, 6) if profit_sol is not None else None,
    })
    log(f"{side} {symbol}: {sol_amount:.4f} SOL @ ${price:.10g} — {reason}"
        + (f" (tx {sig[:16]}…)" if sig else ""))


# ---------- handelslogica ----------

def try_buy(cfg, st, kp, mint, d, live):
    price = d["price"]
    per_trade = cfg["per_trade_sol"]
    reason = f"24u {d['change24h']:+.1f}% ≥ +{cfg['koop_drempel_pct']}%"
    if live:
        quote = jup_quote(SOL_MINT, mint, int(per_trade * LAMPORTS), cfg["slippage_bps"])
        impact = float(quote.get("priceImpactPct") or 0) * 100
        if impact > cfg["max_prijsimpact_pct"]:
            log(f"koop {d['symbol']} overgeslagen: prijsimpact {impact:.2f}% te hoog")
            return
        sig = execute_swap(kp, quote)
        amount_raw = token_balance_raw(kp.pubkey(), mint)
    else:
        sig = None
        amount_raw = int(per_trade * LAMPORTS / price) if price else 0
        st["paper_sol"] -= per_trade
    st["positions"][mint] = {
        "symbol": d["symbol"], "entry_price": price, "sol_spent": per_trade,
        "amount_raw": amount_raw, "opened_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    st["day_spent_sol"] += per_trade
    st["cooldown"][mint] = time.time()
    record_trade(st, "KOOP", mint, d["symbol"], per_trade, price, reason, sig)


def try_sell(cfg, st, kp, mint, pos, d, reason, live):
    price = d["price"]
    if live:
        amount = token_balance_raw(kp.pubkey(), mint)
        if amount <= 0:
            log(f"verkoop {pos['symbol']}: geen saldo gevonden, positie gesloten")
            del st["positions"][mint]
            return
        quote = jup_quote(mint, SOL_MINT, amount, cfg["slippage_bps"])
        sig = execute_swap(kp, quote)
        got_sol = int(quote["outAmount"]) / LAMPORTS
    else:
        sig = None
        got_sol = pos["sol_spent"] * (price / pos["entry_price"]) if pos["entry_price"] else 0
        st["paper_sol"] += got_sol
    pnl = ((price / pos["entry_price"]) - 1) * 100 if pos["entry_price"] else 0
    profit_sol = got_sol - pos["sol_spent"]  # netto beloning van deze trade
    del st["positions"][mint]
    st["cooldown"][mint] = time.time()
    record_trade(st, "VERKOOP", mint, pos["symbol"], got_sol, price,
                 f"{reason} (resultaat {pnl:+.1f}%)", sig,
                 pnl_pct=pnl, profit_sol=profit_sol)


def tick(cfg, st, kp, live):
    today = str(date.today())
    if st["day"] != today:
        st["day"], st["day_spent_sol"] = today, 0.0

    mints = list(dict.fromkeys(cfg["tokens"]))
    if cfg.get("auto_scan"):
        try:
            mints += [m for m in auto_scan_mints(cfg) if m not in mints]
        except Exception as e:  # noqa: BLE001
            log(f"auto-scan mislukt: {e}")
    mints += [m for m in st["positions"] if m not in mints]  # posities altijd volgen
    if not mints:
        log("geen tokens geconfigureerd — vul 'tokens' in config.json")
        return {}

    market = fetch_market(mints)

    # 1) verkopen: drempel / stop-loss / take-profit
    for mint, pos in list(st["positions"].items()):
        d = market.get(mint)
        if not d or not d["price"]:
            continue
        pnl = ((d["price"] / pos["entry_price"]) - 1) * 100 if pos["entry_price"] else 0
        ch = d["change24h"]
        if pnl <= -cfg["stop_loss_pct"]:
            try_sell(cfg, st, kp, mint, pos, d, f"stop-loss {pnl:+.1f}%", live)
        elif pnl >= cfg["take_profit_pct"]:
            try_sell(cfg, st, kp, mint, pos, d, f"take-profit {pnl:+.1f}%", live)
        elif ch is not None and ch <= -cfg["verkoop_drempel_pct"]:
            try_sell(cfg, st, kp, mint, pos, d,
                     f"24u {ch:+.1f}% ≤ −{cfg['verkoop_drempel_pct']}%", live)

    # 2) kopen: 10%-regel + alle risicofilters
    for mint in mints:
        d = market.get(mint)
        if not d or mint in st["positions"] or not d["price"]:
            continue
        ch = d["change24h"]
        if ch is None or ch < cfg["koop_drempel_pct"]:
            continue
        if not passes_filters(d, cfg):
            continue
        if len(st["positions"]) >= cfg["max_posities"]:
            continue
        if st["day_spent_sol"] + cfg["per_trade_sol"] > cfg["max_dag_budget_sol"]:
            log("dagbudget bereikt — geen nieuwe aankopen vandaag")
            break
        cd = st["cooldown"].get(mint, 0)
        if time.time() - cd < cfg["cooldown_minuten"] * 60:
            continue
        if live:
            bal = sol_balance(kp.pubkey())
            if bal < cfg["per_trade_sol"] + 0.01:  # reserve voor transactiekosten
                log(f"te weinig SOL ({bal:.4f}) voor een trade van {cfg['per_trade_sol']}")
                break
        elif st["paper_sol"] < cfg["per_trade_sol"]:
            log("papiersaldo op")
            break
        try_buy(cfg, st, kp, mint, d, live)

    return market


# ---------- main ----------

def ensure_single_instance():
    """Twee bots tegelijk = dubbel handelen en botsende bestanden. Nooit doen."""
    if os.path.exists(PID_PATH):
        try:
            with open(PID_PATH) as f:
                old = int(f.read().strip())
            os.kill(old, 0)  # bestaat dit proces nog?
            print(f"⛔ Er draait al een bot (pid {old}). Stop die eerst (Ctrl+C in dat venster),\n"
                  f"   of verwijder bot/bot.pid als je zeker weet dat hij niet meer draait.")
            sys.exit(1)
        except (ValueError, ProcessLookupError, PermissionError):
            pass  # verweesd pid-bestand: overschrijven
    with open(PID_PATH, "w") as f:
        f.write(str(os.getpid()))


def main():
    global running
    ensure_single_instance()
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    live = cfg.get("mode") == "live"
    if live and not cfg.get("ik_begrijp_het_risico"):
        print("⛔ mode is 'live' maar 'ik_begrijp_het_risico' staat niet op true.\n"
              "   Lees eerst de README, test in paper-modus, en pas dan config.json aan.")
        sys.exit(1)

    kp, created = load_or_create_wallet()
    st = load_state()
    if st["paper_sol"] is None:
        st["paper_sol"] = cfg.get("paper_start_sol", 1.0)

    print("=" * 64)
    print(f"  MemeRadar-bot — modus: {'🔴 LIVE (echt geld!)' if live else '🟢 PAPER (oefenen, nepgeld)'}")
    print(f"  Bot-wallet: {kp.pubkey()}")
    if created:
        print("  ➜ NIEUWE wallet aangemaakt (bot/wallet.json — maak hier een backup van).")
    if live:
        bal = sol_balance(kp.pubkey())
        print(f"  Saldo: {bal:.4f} SOL")
        if bal == 0:
            print("  ➜ Stort een KLEIN bedrag SOL op het adres hierboven om te handelen.")
        print("  ⚠️  Alleen geld gebruiken dat je volledig kunt missen.")
    else:
        print(f"  Papiersaldo: {st['paper_sol']:.4f} SOL (nepgeld)")
    print(f"  Regels: koop ≥ +{cfg['koop_drempel_pct']}% | verkoop ≤ −{cfg['verkoop_drempel_pct']}% "
          f"| SL {cfg['stop_loss_pct']}% | TP {cfg['take_profit_pct']}%")
    print(f"  Limieten: {cfg['per_trade_sol']} SOL/trade | {cfg['max_dag_budget_sol']} SOL/dag "
          f"| max {cfg['max_posities']} posities")
    print("  Stoppen: Ctrl+C")
    print("=" * 64)

    def stop(_sig, _frm):
        global running
        running = False
        log("stoppen… (open posities blijven staan; bij herstart gaat de bewaking verder)")
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    while running:
        err = None
        market = {}
        try:
            market = tick(cfg, st, kp, live)
        except Exception as e:  # noqa: BLE001 — één mislukte ronde mag de bot niet stoppen
            err = str(e)
            log(f"⚠️ ronde mislukt: {e}")
        try:
            bal = sol_balance(kp.pubkey()) if live else st["paper_sol"]
        except Exception:  # noqa: BLE001
            bal = None
        save_state(st)
        write_status(cfg, st, kp, market, bal, err)
        if market and not err:
            summary = " · ".join(
                f"{d['symbol']} {d['change24h']:+.1f}%" for d in market.values()
                if d.get("change24h") is not None)
            log(f"volgt: {summary}  (koop ≥ +{cfg['koop_drempel_pct']}%, "
                f"verkoop ≤ −{cfg['verkoop_drempel_pct']}%) — "
                f"{len(st['positions'])} positie(s) open")
        for _ in range(cfg.get("interval_seconden", 60)):
            if not running:
                break
            time.sleep(1)

    save_state(st)
    try:
        os.remove(PID_PATH)
    except OSError:
        pass
    log("gestopt.")


if __name__ == "__main__":
    main()
