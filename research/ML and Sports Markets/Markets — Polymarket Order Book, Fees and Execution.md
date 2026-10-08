---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, machine-learning, cybersecurity, ml-and-sports-markets, polymarket, clob, market-microstructure, fees, execution, maker-taker]
---

# Markets — Polymarket Order Book, Fees and Execution

**TL;DR**
- Since 2026 Polymarket sports markets charge **taker fees that peak at a 50¢ price**. Makers pay nothing and get rebates.
- The tennis fade trades around mid-prices right after a break, which is exactly where taker fees are highest. So **post limit orders (maker) at fair value** rather than hitting the book.
- The catch is **adverse selection**: in-play, faster traders (courtsiders, faster feeds) pick off stale quotes.

**Builds on:** [[Betting Apps — Behavioral and Automation Detection]] §6 (the API is the sanctioned route) and [[Tennis — In-Play Market Research]] (the strategy).

## Mechanics

- Each outcome is a token on a **central limit order book**. The book is public with no auth. It returns `tick_size` (0.1 / 0.01 / 0.001 / 0.0001 per market), `min_order_size` (often 5) and `neg_risk`. `[Documented]`
- **Order types:** GTC and GTD (resting limit orders), FOK and FAK (immediate). Prices must be multiples of the tick. `[Documented]`
- Orders are signed with EIP-712. The API is the documented bot and market-maker path. Polymarket geo-blocks by jurisdiction, so check eligibility for each member's location before anyone trades. `[Documented]`

## Fees (2026, and they change, so read them live)

- Sports fees began on **18 Feb 2026** (NCAAB and Serie A first) and **Fee Structure V2** took effect on **30 Mar 2026**. Fees are **taker-only**, follow a **price curve** (highest at 0.50, near zero at the extremes), and are taken in shares on buys and USDC on sells. `[Documented]`
- **Maker rebates** for sports are listed at 25% of taker fees in the docs; another summary says 20%. A **taker rebate tier** program started 28 May 2026. `[Documented]` (conflicting figures)
- **Polymarket US** (the separate CFTC-regulated exchange) has its own schedule: sports takers ~5% at peak under the 1 Jul 2026 schedule, makers free. `[Community]`
- **Action:** read `feesEnabled` and the fee parameters from each market object at runtime. Never hard-code them.

## What this means for the tennis fade

| Choice | Pros | Cons |
|---|---|---|
| **Take** (FOK/FAK) right after a break | Guaranteed fill while the overreaction is live | Peak taker fee at mid-prices; crossing the spread |
| **Make** (GTC at model fair value ± margin) | No fee, plus rebate; earn the spread | May not fill; **adverse selection**: you get filled exactly when someone knows more (a point already played) |

- Feed latency: official in-play feeds run ~5–30 s behind live, and broadcast another 20–45 s ([[Betting Apps — Behavioral and Automation Detection]] §5). Quotes must be pulled **instantly** on any point event, and a resting maker needs a feed at least as fast as the takers'.
- Hybrid: rest maker orders when the market is calm, and only take when edge − fee − spread > threshold.

## Liquidity reality check

- Depth limits stake size. Before modelling ROI, pull the book for 20+ live tennis matches and log spread and depth at the top 3 levels over the match. That decides whether the strategy is worth more than pocket money.

## Pitch in

- [ ] ML: write a book recorder (websocket or polling) for live tennis markets to parquet; post spread and depth statistics here.
- [ ] Security: review key management for the signing wallet (hardware wallet or vault; never in the repo or vault).

## Sources

- [Polymarket — fees](https://docs.polymarket.com/trading/fees) · [maker rebates](https://docs.polymarket.com/polymarket-learn/trading/maker-rebates-program) · [taker rebates](https://docs.polymarket.com/trading/taker-rebates.md) · [order book](https://docs.polymarket.com/trading/orderbook) · [create orders](https://docs.polymarket.com/trading/orders/create) `[Documented]`
- [Pine Analytics — fee rollout](https://pineanalytics.substack.com/p/polymarket-fee-rollout) · [River Markets — Polymarket US fees](https://www.rivermarkets.com/insights/polymarket-us-fees.html) `[Community]`

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — Machine Learning]] · [[State of — Cybersecurity]] · [[State of — ML and Sports Markets]]
