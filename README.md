# Ordinals Minter

A web service that inscribes an arbitrary file onto the Bitcoin blockchain as an Ordinal
inscription, and takes payment for it in ETH.

Written in February and March of 2023 — the Ordinals protocol was released on 21 January 2023, so
this was built during the first weeks the protocol existed, against `ord` as it stood at the time.
We are publishing it as a record of that work.

---

## Table of contents

- [What Ordinals actually are](#what-ordinals-actually-are)
  - [Ordinal theory: numbering the satoshis](#ordinal-theory-numbering-the-satoshis)
  - [Rarity](#rarity)
  - [Inscriptions: what Taproot made possible](#inscriptions-what-taproot-made-possible)
  - [The inscription envelope](#the-inscription-envelope)
  - [Commit and reveal](#commit-and-reveal)
  - [Inscription IDs and numbers](#inscription-ids-and-numbers)
  - [What an inscription costs, and why](#what-an-inscription-costs-and-why)
  - [Size limits](#size-limits)
  - [Cardinal sats, postage, and why a wallet must be ordinal-aware](#cardinal-sats-postage-and-why-a-wallet-must-be-ordinal-aware)
  - [What is built on top: BRC-20, recursion, Runes](#what-is-built-on-top-brc-20-recursion-runes)
- [What this service does](#what-this-service-does)
  - [Order lifecycle](#order-lifecycle)
  - [Architecture](#architecture)
  - [Pricing](#pricing)
- [Running it](#running-it)
- [Layout](#layout)
- [Status and known limitations](#status-and-known-limitations)

---

## What Ordinals actually are

Ordinals are two separate ideas that are usually spoken of as one. The first is a numbering scheme
for satoshis. The second is a way of attaching content to a numbered satoshi. Neither is a change to
Bitcoin. There is no new opcode, no soft fork, no sidechain and no token contract. Everything below
is built out of rules that already existed, which is the whole point of the design.

### Ordinal theory: numbering the satoshis

Ordinal theory assigns every satoshi a serial number, in the order it was mined. The first satoshi of
the genesis block's coinbase is `0`, the next is `1`, and so on up to the 2,100,000,000,000,000th and
last satoshi that will ever exist. The number is not stored anywhere on chain. It is *derived* — any
two people who run the same rules over the same block history arrive at the same numbers, which is
what makes the scheme trustless rather than a registry someone maintains.

Satoshis are then tracked through transactions **first-in-first-out**. The input sats of a
transaction are laid end to end in input order, and the output sats are taken off the front of that
sequence in output order. Sats paid as fees are appended to the coinbase output of the block that
mines them, after the subsidy. That FIFO rule is the entire transfer algorithm, and it is the reason
an index has to be built by replaying the chain: a UTXO does not carry its sat ranges, they have to
be computed.

The same satoshi can be written four ways, and each notation exposes something different:

| Notation | Example | What it shows |
|---|---|---|
| Integer | `2099994106992659` | the ordinal number itself |
| Decimal | `3891094.16797` | block height, then offset of the sat within that block |
| Degree | `1°0′0″0‴` | cycle, then index in halving epoch, in difficulty period, in block |
| Name | `satoshi` | the number encoded in base 26 using `a`–`z` |
| Percentile | `99.99971949060254%` | position in the total supply |

Degree notation `A°B′C″D‴` repays a second look, because it is where ordinal theory encodes Bitcoin's
own periodicity. `B` is the block's index within the 210,000-block halving epoch, `C` its index
within the 2,016-block difficulty adjustment period, and `A` counts *cycles* — the interval after
which a halving and a difficulty adjustment fall on the same block again. Since 210,000 and 2,016
share a factor, that alignment recurs every six halvings, or roughly every 24 years. A satoshi whose
degree notation reads `1°0′0″0‴` is the first sat of a block that begins a halving epoch and a
difficulty period at once.

### Rarity

The periodicity above defines a rarity ladder directly. Nothing is minted or allocated; a sat is rare
because of where in the chain's structure it was mined.

| Tier | Definition | How many will ever exist |
|---|---|---|
| Common | any sat that is not the first of its block | ~2.1 quadrillion |
| Uncommon | the first sat of each block | ~6,929,999 |
| Rare | the first sat of each difficulty adjustment period | ~3,437 |
| Epic | the first sat of each halving epoch | 32 |
| Legendary | the first sat of each cycle | 5 |
| Mythic | the first sat of the genesis block | 1 |

### Inscriptions: what Taproot made possible

An inscription is content — an image, a text file, a PDF, anything — committed to the chain and bound
to one specific satoshi. Three earlier consensus changes are what make it practical:

1. **SegWit's witness discount.** Witness bytes are charged 1 weight unit each, while non-witness
   bytes are charged 4. A block is 4,000,000 weight units. So data placed in the witness costs a
   quarter of what the same data costs in a script or an `OP_RETURN`.
2. **Taproot's script-path spend** (BIP 341). A Taproot output commits to a Merkle tree of scripts.
   Only the leaf you actually use is revealed when you spend, and it is revealed *in the witness* —
   where the discount applies.
3. **Tapscript's removal of the 520-byte push limit** (BIP 342). Legacy script caps a single stack
   element at 520 bytes. Tapscript lifts that for witness elements, so content can be pushed in
   large chunks rather than being fragmented across an unworkable number of pushes.

Put together: a Taproot script-path spend is the cheapest large data carrier Bitcoin has, and it is
the one Ordinals uses.

### The inscription envelope

Content is embedded in a tapscript in a construction that is deliberately dead code:

```
OP_FALSE
OP_IF
  OP_PUSH "ord"          # protocol identifier
  OP_PUSH 0x01           # tag 1: content type
  OP_PUSH "image/png"
  OP_PUSH 0x00           # tag 0: body follows
  OP_PUSH <...bytes...>  # content, in chunks of at most 520 bytes
  OP_PUSH <...bytes...>
OP_ENDIF
```

`OP_FALSE OP_IF ... OP_ENDIF` is a branch that never executes. The script is valid, the interpreter
skips the whole block, and the bytes inside are therefore unconstrained — they are data riding inside
a script, not a program. Everything an indexer needs is in there, tagged:

| Tag | Field | Purpose |
|---|---|---|
| `0` | body | the content itself, in one or more pushes |
| `1` | content type | a MIME type, so the content can be rendered |
| `2` | pointer | which sat in the outputs to inscribe, if not the first |
| `3` | parent | provenance: the parent inscription, proving a collection's authorship |
| `5` | metadata | arbitrary CBOR-encoded metadata |
| `7` | metaprotocol | names a protocol layered on top of the inscription |
| `9` | content encoding | e.g. `gzip`, for compressed bodies |
| `11` | delegate | render another inscription's content instead of carrying its own |

Even-numbered tags are the ones an indexer must understand; odd-numbered tags may be ignored safely.
That split is how the format was made forward-compatible without a coordinated upgrade.

### Commit and reveal

Inscribing takes two transactions, and the split is not incidental — it is what keeps the content out
of the chain until the moment it is paid for.

**Commit.** Build the envelope script, put it in a Taproot script tree, and derive the output key
`Q = P + tG`, where `t = H_TapTweak(P ‖ merkle_root)`. Send funds to that output. The content is
committed to, cryptographically, but nothing about it is visible: on chain this is an ordinary
Taproot payment, indistinguishable from any other.

**Reveal.** Spend that output via the script path. The witness must now contain the leaf script
itself — envelope and content included — plus a control block carrying the internal key `P` and the
Merkle path proving the leaf belonged to the committed tree. The content becomes public at this
moment, and the inscription is assigned to the **first satoshi of the first output of the reveal
transaction** (unless tag 2 moves it).

Because the assignment is to a sat rather than to an address or an output, the inscription then
travels by ordinal theory's FIFO rule like any other property of that sat. Transferring an
inscription is just spending the sat that carries it.

### Inscription IDs and numbers

An inscription is identified by the reveal transaction's ID, then `i`, then the index of the
inscription within that transaction:

```
b7c33f003f32efd21be6fc905501067f8117fbee4274ff7902661359b4cf73cbi0
```

Separately, indexers assign sequential **inscription numbers** in the order inscriptions appear in
the chain. Numbers are an indexer's convention rather than part of the commitment, which is why
"cursed" inscriptions — ones produced by malformed or ambiguous envelopes — were given negative
numbers rather than being discarded outright.

### What an inscription costs, and why

Cost is `fee_rate × vsize`, in satoshis, where `vsize = weight / 4`. Content sits in the witness at
1 weight unit per byte, so **one byte of content adds roughly 0.25 vbytes**, plus per-transaction
overhead spread across both the commit and the reveal.

That ratio is visible in this repository. When `ord` cannot be reached for an exact quote,
[`app/ordwrapper.py`](app/ordwrapper.py) falls back to:

```python
sat_price = int(filesize_bytes / 3.7 * fee_rate)
```

The divisor is 3.7 rather than 4 precisely because the witness discount applies to the content while
the two transactions' inputs, outputs and control block do not benefit from it to the same degree.
The exact quote is obtained the honest way instead, by asking `ord` to build the real transactions
and report their fees without broadcasting:

```
ord wallet inscribe --dry-run --fee-rate <sat/vB> <file>
```

### Size limits

An inscription is bounded by Bitcoin's 4,000,000 weight unit block limit, but in practice by a
stricter relay rule: `MAX_STANDARD_TX_WEIGHT` is 400,000 weight units, so a transaction above
roughly 390 kB of content will not be relayed by default-configured nodes and must be handed
directly to a miner. This is the reason the service offers lossless image optimisation before
inscribing ([`app/compress.py`](app/compress.py)) — on the chain, bytes are the price.

### Cardinal sats, postage, and why a wallet must be ordinal-aware

A wallet that does not understand ordinal theory will eventually pay a rare or inscribed satoshi to a
miner as part of a fee, because to such a wallet every sat is interchangeable. Ordinal-aware wallets
therefore partition their balance:

- **cardinal** sats carry no inscription and no rarity, and are the only ones safe to spend on fees
  and change;
- everything else is held back.

This service reads exactly that figure — `ord wallet balance` returns a `cardinal` field — and reports
the remaining spendable balance to a Telegram alerts channel after each mint, so the hot wallet is
never silently drained below the cost of the next inscription.

Relatedly, an inscription needs a satoshi to live on, and that output still has to clear the dust
limit. `ord` sends a **postage** of 10,000 sats with the inscription by default: the inscription is on
the first sat, and the remaining 9,999 simply make the output economically spendable.

### What is built on top: BRC-20, recursion, Runes

- **BRC-20** is not a smart contract. It is JSON text inscribed as ordinary inscriptions
  (`{"p":"brc-20","op":"mint",...}`), with balances computed entirely by off-chain indexers agreeing
  to read those inscriptions the same way. Bitcoin validates that the inscriptions exist; it knows
  nothing of the balances.
- **Recursive inscriptions** use the `/content/<inscription_id>` endpoint to let one inscription
  reference another, so a collection can inscribe a rendering library once and have thousands of
  pieces call into it rather than each carrying a copy.
- **Runes** is a different protocol by the same author, and worth distinguishing clearly: it is a
  UTXO-based fungible token scheme whose messages ("runestones") are encoded in `OP_RETURN` outputs
  rather than in witness envelopes. It deliberately leaves no junk UTXOs behind and needs no
  off-chain state to be correct, which is exactly where BRC-20 struggles.

---

## What this service does

The user pays in **ETH**, and receives an inscription on **Bitcoin**. There is no bridge and no
wrapped asset: the two chains are joined by this service verifying an Ethereum payment before
committing its own Bitcoin funds to an inscription. That asymmetry is the interesting part of the
design and the source of most of its edge cases.

### Order lifecycle

1. The browser connects MetaMask and is forced onto Ethereum mainnet (`wallet_switchEthereumChain`,
   `chainId` `0x1`).
2. The user selects a file and a fee rate. Live fee rates come from `mempool.space`, cached for a
   minute, with a hardcoded fallback so the page still prices correctly when that API is unreachable.
3. The backend quotes a price by asking `ord` for a dry-run inscription of a temporary file of the
   same size, converts sats → USD → ETH → wei through Binance spot prices, and adds a service fee.
4. The user optionally enables image optimisation, which re-quotes against the compressed size.
5. MetaMask sends the payment. The resulting transaction hash, sender address and value are posted
   to the backend together with the file, and an order row is created with status `CHECKING_PAYMENT`.
6. A background worker verifies the payment on Ethereum, and only then inscribes.
7. The order page refreshes itself every 30 seconds via a `<meta http-equiv="refresh">` tag until
   the inscription exists, then links to the reveal transaction on `mempool.space` and the
   inscription on `ordinals.com`.

### Architecture

```
browser (MetaMask)                     FastAPI (main.py)                 huey worker (app/tasks.py)
      │                                       │                                    │
      ├─ GET /api/estimate_price ────────────▶│──▶ ord wallet inscribe --dry-run   │
      │                                       │                                    │
      ├─ POST /api/files (compress preview) ─▶│──▶ Pillow                          │
      │                                       │                                    │
      ├─ eth_sendTransaction ──▶ Ethereum     │                                    │
      │                                       │                                    │
      └─ POST /api/orders (file + tx_hash) ──▶│──▶ SQLite ──▶ enqueue ────────────▶│
                                              │                                    ├─ web3: verify tx
                                              │                                    ├─ re-quote price
                                              │                                    ├─ ord wallet inscribe
                                              │                                    └─ Telegram alert
```

Payment verification in [`app/tasks.py`](app/tasks.py) checks, in order, that the transaction was
mined, that its `from` matches the address the order claims, that its `to` is our receiving address,
and that its value covers the current re-quoted price. Each failure gets its own terminal status
(`ERROR_WRONG_FROM_ADDR`, `ERROR_WRONG_TO_ADDR`, `ERROR_SMALL_WEI`) rather than a generic failure, so
a stuck order can be diagnosed from the database alone.

The re-quote matters. Bitcoin fee rates, BTC/USD and ETH/USD all move between the moment a price is
shown and the moment the payment confirms. The worker therefore prices the inscription *again* at
execution time and compares, allowing a 3 USD tolerance so ordinary volatility does not reject an
honest payment while an underpayment still does.

Verification is retried with exponential backoff — 10 attempts, starting at 15 seconds, multiplied by
1.15 each time — because an Ethereum transaction is not visible to an RPC node the instant MetaMask
returns its hash.

`ord` maintains an index of sat ranges across the UTXO set, and that index has to be current before
inscribing or quoting. A periodic task re-runs `ord index` every 15 minutes, and the wrapper re-runs
it before each dry-run quote.

### Pricing

```
inscription cost (sat)  ──Binance BTCUSDT──▶  USD  ──Binance ETHUSDT──▶  ETH  ──×10^18──▶  wei
service fee (USD)       =  10% of inscription cost  +  5 USD flat
```

Spot prices are cached for an hour. All arithmetic uses `decimal.Decimal` rather than floats, which
is not a stylistic preference: wei is an integer of 18 decimal places, and IEEE-754 doubles carry
about 15–17 significant digits, so a float pipeline silently corrupts the low-order wei of any
transaction it touches.

---

## Running it

Requires Python 3.10 or newer (the code uses `list[str]` annotations), plus a Bitcoin Core node and
[`ord`](https://github.com/ordinals/ord) on the same machine with a funded, ordinal-aware wallet.

```sh
pip install -r requirements.txt

cat > .env <<'EOF'
TG_BOT_TOKEN=<telegram bot token>
TG_ALERTS_CHANNEL=<chat id for alerts>
SERVER_PORT=1337
EOF

python main.py     # API and web UI
make worker        # background payment-verification and minting worker
```

`app/settings.py` holds the Ethereum receiving address, the Ethereum RPC URL and the 5 MB upload
cap. The node path and wallet name that `ord` is invoked with are constructor defaults in
`app/ordwrapper.py`; the fee rate is chosen per order in the browser.

There are no secrets in this repository. The Telegram bot token and alerts channel are read from the
environment and were never committed. The Ethereum addresses in the source are receiving addresses,
which are public by nature and were served to every visitor of the site.

## Layout

| Path | Contents |
|---|---|
| [`main.py`](main.py) | FastAPI app: pages, price quoting, upload, order creation |
| [`app/ordwrapper.py`](app/ordwrapper.py) | `ord` CLI wrapper — inscribe, dry-run quote, balance, index; plus a mock for offline development |
| [`app/tasks.py`](app/tasks.py) | huey worker: Ethereum payment verification, re-quote, inscription, periodic re-index |
| [`app/database.py`](app/database.py) | SQLModel `MintOrder` and the SQLite session |
| [`app/compress.py`](app/compress.py) | Pillow image optimisation |
| [`app/shared/currencies.py`](app/shared/currencies.py) | sat ⇄ USD ⇄ ETH ⇄ wei, against Binance spot |
| [`app/shared/mempool.py`](app/shared/mempool.py) | recommended fee rates from `mempool.space`, with fallback |
| [`app/shared/telegram.py`](app/shared/telegram.py) | operational alerts |
| [`templates/`](templates), [`assets/`](assets) | Jinja2 pages, MetaMask integration, styles |

## Status and known limitations

This is a working prototype from the first weeks of the Ordinals protocol, published as a record of
that work rather than as maintained software. What we would change before running it again:

- **`ord`'s CLI has changed** since early 2023. The command shapes in `app/ordwrapper.py` are pinned
  to the version of the day and would need revisiting.
- **Price estimation writes a temporary file of the requested size** one byte at a time in order to
  dry-run it. Correct, and needlessly slow; the same figure can be computed from the envelope's
  weight directly.
- **A single-worker huey queue over SQLite** was chosen so that two mints could never race for the
  same UTXOs. It bounds throughput to one inscription at a time.
- **`ERROR_SMALL_WEI` is terminal.** An underpaying order is rejected but not refunded automatically.
- **Order status is not authenticated.** Anyone holding an order UUID can view it, and the first
  POST to an order sets the receiving BTC address.
- **`MIN_WEI_VALUE` and `FEE_RATE` in `app/settings.py` are dead.** Both are imported and never
  read; the real floor is the re-quote comparison in `app/tasks.py` and the real fee rate comes from
  the order. They should be deleted rather than left to imply a check that does not happen.
