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

def new_portfolio(cfg):
    return {"positions": {}, "trades": [], "day_spent_sol": 0.0,
            "paper_sol": cfg.get("paper_start_sol", 1.0), "cooldown": {}}


def load_state(cfg):
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            st = json.load(f)
        if "variants" in st:
            # nieuwe varianten uit de config toevoegen zonder bestaande voortgang te wissen
            for v in cfg.get("training", {}).get("varianten", []):
                st["variants"].setdefault(v["naam"], new_portfolio(cfg))
            return st
    # vers begin (of oud formaat): elke strategievariant krijgt een eigen
    # nepgeld-portefeuille zodat ze eerlijk vergeleken kunnen worden
    variants = {v["naam"]: new_portfolio(cfg)
                for v in cfg.get("training", {}).get("varianten", [])} \
        or {"standaard": new_portfolio(cfg)}
    return {"day": "", "training_start": time.strftime("%Y-%m-%d"),
            "variants": variants}


def save_state(st):
    with open(STATE_PATH, "w") as f:
        json.dump(st, f, indent=1)


def portfolio_stats(port, market):
    """Prestaties van één portefeuille: posities, beloning, win-rate."""
    positions = []
    for mint, pos in port["positions"].items():
        cur = market.get(mint, {}).get("price")
        pnl = ((cur / pos["entry_price"]) - 1) * 100 if cur and pos["entry_price"] else None
        positions.append({**pos, "mint": mint, "current_price": cur, "pnl_pct": pnl})
    sells = [t for t in port["trades"] if t["side"] == "VERKOOP" and t.get("profit_sol") is not None]
    realized = sum(t["profit_sol"] for t in sells)
    wins = sum(1 for t in sells if t["profit_sol"] > 0)
    losses = sum(1 for t in sells if t["profit_sol"] <= 0)
    unrealized = sum((p["current_price"] / p["entry_price"] - 1) * p["sol_spent"]
                     for p in positions
                     if p.get("current_price") and p.get("entry_price"))
    return positions, {
        "realized_sol": round(realized, 6),
        "unrealized_sol": round(unrealized, 6),
        "total_sol": round(realized + unrealized, 6),
        "wins": wins, "losses": losses, "closed_trades": len(sells),
        "win_rate": round(wins / len(sells) * 100) if sells else None,
        "best_pct": max((t["pnl_pct"] for t in sells if t.get("pnl_pct") is not None), default=None),
        "worst_pct": min((t["pnl_pct"] for t in sells if t.get("pnl_pct") is not None), default=None),
    }


def training_report(cfg, st, market):
    """Ranglijst van alle varianten + toets aan de slagingseisen."""
    eisen = cfg.get("training", {}).get("slagingseisen", {})
    rows = []
    for naam, port in st["variants"].items():
        _, s = portfolio_stats(port, market)
        rules = next((v for v in cfg.get("training", {}).get("varianten", [])
                      if v["naam"] == naam), {})
        rows.append({"naam": naam, "regels": {k: v for k, v in rules.items() if k != "naam"},
                     **s, "open_posities": len(port["positions"])})
    rows.sort(key=lambda r: r["total_sol"], reverse=True)
    champion = rows[0] if rows else None

    dagen = 0
    if st.get("training_start"):
        try:
            dagen = (date.today() - date.fromisoformat(st["training_start"])).days
        except ValueError:
            pass

    checks = {}
    geslaagd = False
    if champion:
        checks = {
            "genoeg_trades": {"nodig": eisen.get("min_trades", 20),
                              "nu": champion["closed_trades"],
                              "ok": champion["closed_trades"] >= eisen.get("min_trades", 20)},
            "genoeg_dagen": {"nodig": eisen.get("min_dagen", 7), "nu": dagen,
                             "ok": dagen >= eisen.get("min_dagen", 7)},
            "winst": {"nodig": 0, "nu": champion["total_sol"],
                      "ok": champion["total_sol"] > 0},
            "win_rate": {"nodig": eisen.get("min_winrate_pct", 50),
                         "nu": champion["win_rate"],
                         "ok": (champion["win_rate"] or 0) >= eisen.get("min_winrate_pct", 50)},
        }
        geslaagd = all(c["ok"] for c in checks.values())
    return {"ranglijst": rows, "kampioen": champion["naam"] if champion else None,
            "dagen_bezig": dagen, "eisen": checks, "geslaagd": geslaagd}


def write_status(cfg, st, kp, market, balance, error=None):
    watching = [{"symbol": d["symbol"], "change24h": d["change24h"], "price": d["price"]}
                for d in market.values()]

    training = None
    variants = cfg.get("training", {}).get("varianten", [])
    if cfg["mode"] != "live" and variants:
        training = training_report(cfg, st, market)
        lead_name = training["kampioen"]
    else:
        lead_name = next(iter(st["variants"]))
    # het hoofddashboard (beloningskaart) toont de best presterende strategie
    lead = st["variants"].get(lead_name) or next(iter(st["variants"].values()))
    positions, stats = portfolio_stats(lead, market)

    with open(STATUS_PATH, "w") as f:
        json.dump({
            "watching": watching,
            "mode": cfg["mode"],
            "wallet": str(kp.pubkey()),
            "sol_balance": balance if cfg["mode"] == "live" else lead.get("paper_sol"),
            "day_spent_sol": lead.get("day_spent_sol", 0),
            "stats": stats,
            "positions": positions,
            "trades": lead["trades"][-20:],
            "training": training,
            "settings": {k: cfg[k] for k in (
                "koop_drempel_pct", "verkoop_drempel_pct", "stop_loss_pct",
                "take_profit_pct", "per_trade_sol", "max_posities",
                "max_dag_budget_sol")},
            "error": error,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=1)
    if training and training["geslaagd"]:
        log(f"🎓 TRAINING GESLAAGD — beste strategie: {training['kampioen']}")


def record_trade(st, side, mint, symbol, sol_amount, price, reason, sig=None,
                 pnl_pct=None, profit_sol=None, tag=""):
    st["trades"].append({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"), "side": side, "mint": mint,
        "symbol": symbol, "sol": round(sol_amount, 6), "price": price,
        "reason": reason, "tx": sig,
        "pnl_pct": round(pnl_pct, 1) if pnl_pct is not None else None,
        "profit_sol": round(profit_sol, 6) if profit_sol is not None else None,
    })
    pre = f"[{tag}] " if tag else ""
    log(f"{pre}{side} {symbol}: {sol_amount:.4f} SOL @ ${price:.10g} — {reason}"
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
    record_trade(st, "KOOP", mint, d["symbol"], per_trade, price, reason, sig,
                 tag=cfg.get("_variant", ""))


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
                 pnl_pct=pnl, profit_sol=profit_sol, tag=cfg.get("_variant", ""))


def effective_cfg(cfg, variant):
    """Basisconfig + de regels van één strategievariant."""
    eff = dict(cfg)
    eff.update({k: v for k, v in variant.items() if k != "naam"})
    eff["_variant"] = variant.get("naam", "")
    return eff


def run_rules(eff, port, kp, market, live):
    """Voer de koop/verkoop-regels van één strategie uit op één portefeuille."""
    # 1) verkopen: trailing / stop-loss / take-profit / drempel
    for mint, pos in list(port["positions"].items()):
        d = market.get(mint)
        if not d or not d["price"]:
            continue
        price = d["price"]
        pnl = ((price / pos["entry_price"]) - 1) * 100 if pos["entry_price"] else 0
        ch = d["change24h"]
        # piek bijhouden voor de trailing stop
        pos["peak_price"] = max(pos.get("peak_price", pos["entry_price"]), price)
        trail = eff.get("trailing_pct")
        drop_from_peak = ((price / pos["peak_price"]) - 1) * 100 if pos["peak_price"] else 0
        if trail and drop_from_peak <= -trail and pnl > 0:
            try_sell(eff, port, kp, mint, pos, d,
                     f"trailing-stop {drop_from_peak:+.1f}% vanaf piek", live)
        elif pnl <= -eff["stop_loss_pct"]:
            try_sell(eff, port, kp, mint, pos, d, f"stop-loss {pnl:+.1f}%", live)
        elif not trail and pnl >= eff["take_profit_pct"]:
            try_sell(eff, port, kp, mint, pos, d, f"take-profit {pnl:+.1f}%", live)
        elif ch is not None and ch <= -eff["verkoop_drempel_pct"]:
            try_sell(eff, port, kp, mint, pos, d,
                     f"24u {ch:+.1f}% ≤ −{eff['verkoop_drempel_pct']}%", live)

    # 2) kopen: drempel + alle risicofilters
    for mint, d in market.items():
        if mint in port["positions"] or not d["price"]:
            continue
        ch = d["change24h"]
        if ch is None or ch < eff["koop_drempel_pct"]:
            continue
        if not passes_filters(d, eff):
            continue
        if len(port["positions"]) >= eff["max_posities"]:
            continue
        if port["day_spent_sol"] + eff["per_trade_sol"] > eff["max_dag_budget_sol"]:
            break
        if time.time() - port["cooldown"].get(mint, 0) < eff["cooldown_minuten"] * 60:
            continue
        if live:
            bal = sol_balance(kp.pubkey())
            if bal < eff["per_trade_sol"] + 0.01:  # reserve voor transactiekosten
                log(f"te weinig SOL ({bal:.4f}) voor een trade van {eff['per_trade_sol']}")
                break
        elif port["paper_sol"] < eff["per_trade_sol"]:
            break
        try_buy(eff, port, kp, mint, d, live)


def tick(cfg, st, kp, live):
    today = str(date.today())
    if st["day"] != today:
        st["day"] = today
        for port in st["variants"].values():
            port["day_spent_sol"] = 0.0

    mints = list(dict.fromkeys(cfg["tokens"]))
    if cfg.get("auto_scan"):
        try:
            mints += [m for m in auto_scan_mints(cfg) if m not in mints]
        except Exception as e:  # noqa: BLE001
            log(f"auto-scan mislukt: {e}")
    for port in st["variants"].values():
        mints += [m for m in port["positions"] if m not in mints]  # posities altijd volgen
    if not mints:
        log("geen tokens geconfigureerd — vul 'tokens' in config.json")
        return {}

    market = fetch_market(mints)

    variants = cfg.get("training", {}).get("varianten", [])
    if live or not variants:
        # live (of zonder training): alleen de basisregels, op de eerste portefeuille
        name = next(iter(st["variants"]))
        base = dict(cfg)
        base["_variant"] = ""
        run_rules(base, st["variants"][name], kp, market, live)
    else:
        # training: elke variant handelt met eigen nepgeld op dezelfde marktdata
        for v in variants:
            port = st["variants"].setdefault(v["naam"], new_portfolio(cfg))
            run_rules(effective_cfg(cfg, v), port, kp, market, live=False)

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
    st = load_state(cfg)

    variants = cfg.get("training", {}).get("varianten", [])
    print("=" * 64)
    print(f"  MemeRadar-bot — modus: {'🔴 LIVE (echt geld!)' if live else '🟢 PAPER (oefenen, nepgeld)'}")
    print(f"  Bot-wallet: {kp.pubkey()}")
    if created:
        print("  ➜ NIEUWE wallet aangemaakt — maak een backup van ~/.memeradar/wallet.json")
    if live:
        bal = sol_balance(kp.pubkey())
        print(f"  Saldo: {bal:.4f} SOL")
        if bal == 0:
            print("  ➜ Stort een KLEIN bedrag SOL op het adres hierboven om te handelen.")
        print("  ⚠️  Alleen geld gebruiken dat je volledig kunt missen.")
        print(f"  Regels: koop ≥ +{cfg['koop_drempel_pct']}% | verkoop ≤ −{cfg['verkoop_drempel_pct']}% "
              f"| SL {cfg['stop_loss_pct']}% | TP {cfg['take_profit_pct']}%")
    elif variants:
        print(f"  🎓 TRAINING: {len(variants)} strategieën strijden met elk "
              f"{cfg.get('paper_start_sol', 1.0)} SOL nepgeld:")
        for v in variants:
            trail = f"trailing {v['trailing_pct']}%" if v.get("trailing_pct") else f"TP {v.get('take_profit_pct', cfg['take_profit_pct'])}%"
            print(f"     • {v['naam']}: koop +{v.get('koop_drempel_pct', cfg['koop_drempel_pct'])}% | "
                  f"SL {v.get('stop_loss_pct', cfg['stop_loss_pct'])}% | {trail}")
        e = cfg.get("training", {}).get("slagingseisen", {})
        print(f"  Geslaagd bij: ≥{e.get('min_trades', 20)} trades, ≥{e.get('min_dagen', 7)} dagen, "
              f"winst, win-rate ≥{e.get('min_winrate_pct', 50)}%")
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
            bal = sol_balance(kp.pubkey()) if live else None
        except Exception:  # noqa: BLE001
            bal = None
        save_state(st)
        write_status(cfg, st, kp, market, bal, err)
        if market and not err:
            top = sorted(market.values(), key=lambda d: -(d.get("change24h") or -999))[:4]
            summary = " · ".join(
                f"{d['symbol']} {d['change24h']:+.1f}%" for d in top
                if d.get("change24h") is not None)
            open_tot = sum(len(p["positions"]) for p in st["variants"].values())
            log(f"volgt {len(market)} tokens (top: {summary}) — "
                f"{open_tot} positie(s) open over {len(st['variants'])} strategieën")
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
