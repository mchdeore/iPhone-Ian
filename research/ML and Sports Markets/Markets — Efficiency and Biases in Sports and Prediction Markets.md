---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, machine-learning, ml-and-sports-markets, market-efficiency, favourite-longshot-bias, prediction-markets, calibration, behavioral-finance]
---

# Markets — Efficiency and Biases in Sports and Prediction Markets

**TL;DR**
- Markets are good but not perfect, and the known flaws are **structural**: the favourite-longshot bias, in-play overreaction, and market-to-market differences.
- 2026 evidence: **Polymarket and Kalshi prices aren't face-value probabilities**. Biases depend on the platform and **grow with time to expiry**, and taker-accepted prices are more biased.
- Edges survive where the flow is retail-heavy and in-play, and where the bias is behavioural rather than informational.

**Builds on:** [[Tennis — In-Play Market Research]] §1 (Brown 2014: in-play mispricing ~10× pre-match, 5.3% average, driven by break overreaction).

## Documented biases

| Bias | Evidence | Relevance to tennis fade |
|---|---|---|
| **Favourite-longshot** (longshots overpriced) | Long documented in racing and sports betting. In prediction markets it **worsens with time to expiry** and persists in high-volume markets. On Polymarket, low-probability contracts resolve true less often than priced (small sample). `[Benchmark]` | After a break the *breaker* becomes the favourite and the broken player the longshot. FLB partly *works against* fading by buying the longshot. **The two effects need separating.** |
| **In-play overreaction** | Brown 2014: single breaks are over-priced, and the effect vanishes within minutes. `[Benchmark]` | The core edge. |
| **Underconfidence in political markets** | Prices pulled toward 50% (arXiv 2602.19520). `[Benchmark]` | Shows bias *direction* differs by category; don't assume sports behaves like politics. |
| **Taker vs maker prices** | Bias is more pronounced in taker-accepted prices; Kalshi's trade-size effect doesn't replicate on Polymarket (microstructure). `[Benchmark]` | Another reason to be the maker ([[Markets — Polymarket Order Book, Fees and Execution]]). |
| **Consensus beats single books** | Kaunitz et al.: the average of all books' odds is a good fair-value estimate; outliers versus the consensus were profitable. `[Documented]` | Use the Betfair/Pinnacle consensus as a fair-value check on Polymarket prices. |

## Where edges survive (and where they don't)

- **Survive:** behavioural over- and under-reaction, retail-heavy venues, thin in-play books, long-dated longshots (if you're selling them).
- **Don't survive:** anything a faster feed explains (that's latency, not an edge), anything sharp books already price (Betfair main markets), and edges smaller than fee + spread.
- **Open research question (from the tennis checklist):** is Polymarket's retail in-play tennis flow *less* efficient than Betfair's? Test: compare price paths after breaks on matched matches on both venues.

## Pitch in

- [ ] Sports/ML: build a break-event study. For every break in matched matches, align Polymarket and Betfair price paths from −60 s to +600 s and measure overshoot and decay half-life.
- [ ] ML: measure FLB on resolved Polymarket tennis markets using our own data (calibration curve by price bin).

## Sources

- [Calibration of Kalshi and Polymarket (arXiv 2602.19520)](https://arxiv.org/html/2602.19520v1) `[Benchmark]` · [AutoML critique incl. Polymarket curve (arXiv 2608.07303)](https://arxiv.org/pdf/2608.07303) `[Benchmark]`
- [Longshot bias glossary](https://pm.wiki/tr/data/glossary/longshot-bias) · [Prediction markets vs forecasters](https://sportsgameodds.com/blog/prediction-markets-beat-professional-forecasters) `[Community]`
- [MIT Tech Review — Kaunitz et al.](https://www.technologyreview.com/2017/10/19/67760/the-secret-betting-strategy-that-beats-online-bookmakers/) `[Documented]`
