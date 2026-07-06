# 🚀 MemeRadar — Crypto & Memecoin Tracker

Realtime tracker voor alle grote crypto's én memecoins, met automatische koop/verkoop-signalen.

## Starten

Open Terminal en voer uit:

```bash
cd ~/Claude/memecoin-tracker
python3 -m http.server 8765
```

Open daarna in je browser: **http://localhost:8765**

> De app moet via `http://localhost` draaien (niet als los bestand openen), anders kunnen
> MetaMask en Phantom geen verbinding maken.

## Wat kan de app?

- **🔥 Trending** — de écht trending pools on-chain (GeckoTerminal, geen betaalde promotie),
  realtime over Solana/Ethereum/Base/BSC, met chain-filter
- **🆕 Nieuw** — gloednieuwe pools (minuten oud) — hoogste risico, duidelijk gemarkeerd
- **🔎 Zoeken** — zoek elk on-chain token op naam of symbool
- **📈 Top Crypto** — top-50 coins op marktkapitalisatie (CoinGecko)
- **🐸 Memecoins** — top-50 memecoins (CoinGecko meme-categorie)
- **⭐ Watchlist** — volg je eigen tokens; de watchlist wordt élke minuut op de
  achtergrond bewaakt (ook als je op een ander tabblad kijkt) en bij het doorbreken
  van de drempel krijg je een melding in de app én (optioneel) een browsernotificatie
- Instellingen (drempel, valuta, sortering) en je watchlist worden lokaal onthouden

## Tijdframes (1u / 6u / 24u)

De tabel toont de verandering over 1 uur, 6 uur en 24 uur — rechtstreeks uit de
API-data, dus direct gevuld. Alleen de 6u-kolom bij CoinGecko-coins (Top Crypto/
Memecoins) zit niet in de gratis API; die vult de app aan met een eigen prijsgeheugen
dat opbouwt terwijl de app open staat. Een "—" betekent "nog geen betrouwbare
meting" — de app gokt nooit.

## Signalen

- **KOOP** zodra de 24-uurs stijging **≥ +10%** is
- **VERKOOP** zodra de 24-uurs daling **≤ −10%** is
- **STERK KOOP / STERK VERKOOP** vanaf 2,5× de drempel (±25%)
- **Momentum-check**: stijgt een token op 24u maar daalt hij het laatste uur hard,
  dan staat er "KOOP · afkoelend" — en andersom "VERKOOP · herstelt"
- Daartussen: **HOUD**
- De drempel (standaard 10%) is bovenin aan te passen

## Wallet koppelen & direct handelen (in de app)

- Klik op **🦊 MetaMask** (Ethereum/Base/BSC/Arbitrum/Polygon/Optimism/Avalanche) of
  **👻 Phantom** (Solana) om je wallet te koppelen — de app leest **alleen je publieke adres**.
- Klik bij een on-chain token op **Koop** of **Verkoop**: je ziet direct een live offerte
  (verwachte opbrengst, minimum na slippage, prijsimpact) en bevestigt met één klik in je
  eigen wallet. Geen externe websites nodig.
- Routes: **Jupiter** (Solana) en **ParaSwap** (EVM-chains) — de officiële swap-aggregators,
  zonder extra kosten vanuit deze app.
- Bij verkoop van een EVM-token keur je eerst het **exacte** verkoopbedrag goed (geen
  onbeperkte allowance — bewust veiliger).
- Phantom simuleert elke transactie vóór ondertekening; MetaMask toont de tokenbewegingen.
  Controleer dat scherm altijd — annuleren kan altijd, dan gebeurt er niets.
- De Solana-library (@solana/web3.js 1.95.8) is lokaal opgeslagen in `vendor/` en vastgepind
  (sha256 `a759deca1b65df140e8dda5ad8645c19579536bf822e5c0c7e4adb7793a5bd08`) — geen CDN
  tijdens gebruik.

## Veiligheid (bewuste keuzes)

1. **Non-custodial**: de app vraagt nooit om je seed phrase of privésleutel en kan
   nooit zelfstandig transacties uitvoeren — jouw wallet ondertekent alles.
2. **Minimale afhankelijkheden**: alleen de officiële, lokaal vastgepinde Solana-library;
   verder 100% eigen code, geen trackers.
3. **Handel op contractadres**, nooit op naam — zo koop je nooit per ongeluk een
   nep-token met dezelfde naam.
4. **Manipulatiebestendige prijzen**: per token wordt de pool gekozen met een vertrouwd
   quote-token (SOL/USDC/USDT/ETH…) en het hoogste echte volume; pools met opgeblazen
   nep-liquiditeit worden genegeerd.
5. **Rug-pull-risico-indicator**: on-chain tokens met weinig liquiditeit (< $50k) of
   jonger dan 7 dagen krijgen ⚠️ Hoog risico, ook in het handelsvenster.
6. **Eerlijke data**: bron en tijdstip van elke update staan in beeld; bij API-fouten
   zie je een duidelijke melding in plaats van verouderde cijfers.

## 🤖 Automatische bot

De bot handelt zelfstandig op Solana volgens jouw 10%-regel. Starten:

```bash
cd ~/Claude/memecoin-tracker/bot
python3 bot.py
```

Volg alles live in de app op het tabblad **🤖 Bot** (status, posities, resultaat per trade).

**Zo is hij veilig gebouwd:**

1. **Eigen aparte wallet** — bij de eerste start maakt de bot `bot/wallet.json` aan
   (alleen op jouw computer, bestandsrechten 600). Dit is nooit je hoofdwallet: je stort
   er bewust een klein bedrag op, en meer kan de bot dus nooit verliezen.
   Maak een backup van dit bestand en deel het met niemand.
2. **Oefenmodus standaard** — `mode: "paper"` handelt met nepgeld tegen echte prijzen.
   Laat hem zo minstens een week draaien voor je ook maar overweegt live te gaan.
3. **Live gaan is een dubbele bewuste keuze** — zet in `bot/config.json` zowel
   `"mode": "live"` als `"ik_begrijp_het_risico": true`. Anders weigert de bot.
4. **Harde limieten** — per trade (0,05 SOL), per dag (0,25 SOL), max 3 posities,
   stop-loss −10%, take-profit +25%, 2 uur cooldown per token. Alles instelbaar.
5. **Strenge koopfilters** — minimaal $100k liquiditeit, $250k dagvolume, 7 dagen oud,
   max 2% prijsimpact, en expliciet niet-geverifieerde tokens worden nooit gekocht.
6. **Betrouwbare data** — prijzen komen van Jupiter (geaggregeerd en geverifieerd, niet
   te manipuleren met één nep-pool), met DexScreener als reserve.
7. **Alleen jouw lijst** — de bot handelt standaard alleen in tokens die jij in
   `config.json` zet (standaard BONK en WIF). `auto_scan` staat bewust uit.

**Strategie** (instelbaar): koop bij 24u ≥ +10%, verkoop bij 24u ≤ −10%, of eerder bij
stop-loss/take-profit ten opzichte van je instapprijs. Stoppen: `Ctrl+C` — open posities
blijven staan en worden bij herstart weer bewaakt.

⚠️ **Eerlijk**: een momentum-strategie als deze kán verliezen, zeker in een zigzag-markt
(hoog kopen, laag verkopen). De limieten begrenzen de schade per dag, maar geen enkele
bot voorspelt de markt. Test lang in paper-modus en beoordeel het resultaat zelf.

## Databronnen

- [CoinGecko API](https://www.coingecko.com/en/api) — gratis, max ~30 calls/min
- [DexScreener API](https://dexscreener.com) — gratis, 60–300 calls/min

⚠️ **Disclaimer**: dit is een hulpmiddel, geen financieel advies. Memecoins zijn extreem
risicovol — je kunt je volledige inleg verliezen.
