---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, ml-and-sports-markets, arbitrage, polymarket, kalshi, betfair, price-discovery]
---

# Markets — Cross-Venue Prices: Polymarket, Kalshi and Betfair

**TL;DR**
- The same event trades at different prices on different venues. Visible gaps are ~1–5¢ on flagship markets, often **0.5–1.5¢ after fees**.
- These are rarely free money: **resolution-rule mismatches** and capital lock-up dominate.
- The real value for us is **price discovery**. Betfair (sharp, deep) acts as the fair-value reference, and Polymarket's lag behind it after a break is the measurable form of the overreaction.

**Builds on:** [[Markets — Efficiency and Biases in Sports and Prediction Markets]] (consensus as fair value) and [[Markets — Resolution and Oracle Risk on Polymarket (UMA)]].

## Gaps and why they persist

- Gross 1–5¢, net 0.5–1.5¢ after Kalshi's per-contract fee cap and Polymarket's fees (practitioner estimate) [1].
- Persistence: capital split across venues, settlement rails taking hours to days, and **contract mapping being genuinely hard** [1].
- Example: 4 Mar 2026, "US Recession in 2026": Kalshi 34¢ vs the closest Polymarket equivalent 39¢; the lock-up until settlement cuts the annualised return [2].
- One tool reports 2–25 point gaps due to different participant pools (vendor claim) [3].

## Why "arb" isn't riskless

- **Different resolution sources:** Kalshi lists named source agencies filed with the CFTC; Polymarket uses UMA and "consensus of credible reporting" [4][5].
- **Different timing windows** mean one venue can resolve YES and the other NO [5].
- **Event halts:** Kalshi halted a contract and settled at the last traded price before the event, per its rules [6].

## Using cross-venue data for the tennis fade

- **Lead-lag study:** after each break, cross-correlate Betfair and Polymarket mid-price changes. If Betfair leads by seconds and Polymarket overshoots more, that gap *is* the edge. Estimate the half-life ([[Markets — Backtesting Without Fooling Yourself]]).
- **Fair-value anchor:** use the Betfair mid (minus commission) as p_market in the Benter blend ([[Markets — Model plus Market - Blending and the Benter Test]]) even when trading on Polymarket.
- **Access check:** each member must check which venues they can legally use ([[Markets — Legal Status of Prediction Markets (US and Canada, Oct 2026)]]). Reading public prices is fine everywhere; trading isn't.

## Pitch in

- [ ] ML: matched-contract mapper for tennis (player names, match IDs) across Betfair and Polymarket; log both books every second during 10 matches.
- [ ] Sports: compare the resolution rules for retirements on each venue.

## Sources

1. [Tech Insider — prediction market arbitrage](https://tech-insider.org/prediction-markets/prediction-market-arbitrage/) `[Community]`
2. [SimpleFunctions — cross-venue edge detection](https://simplefunctions.dev/technicals/cross-venue-edge-detection-kalshi-polymarket) `[Community]`
3. [SimpleFunctions — Kalshi vs Polymarket](https://simplefunctions.dev/compare/kalshi-vs-polymarket) `[Community]` (vendor)
4. [DeFi Rate — how Kalshi and Polymarket settle](https://defirate.com/?p=5575) `[Community]`
5. [Prediction markets can't agree on the truth](https://michaellwy.substack.com/p/prediction-markets-cant-agree-on) · [Orrery — resolution rules](https://orrery.me/learn/polymarket-vs-kalshi-resolution-rules) `[Community]`
6. [Finance Magnates — Iran contract split](https://financemagnates.com/cryptocurrency/us-military-action-against-iran-exposes-split-between-polymarket-and-kalshi-models) `[Community]`
