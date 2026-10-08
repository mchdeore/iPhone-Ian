---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, machine-learning, ml-and-sports-markets, backtesting, overfitting, deflated-sharpe, walk-forward, data-sources, leakage]
---

# Markets — Backtesting Without Fooling Yourself

**TL;DR**
- Most profitable backtests come from leakage or from trying many things.
- Use **point-in-time features**, **walk-forward with a purge/embargo**, a **realistic fill model**, and log **every** variant you try, so the result can be deflated (Deflated Sharpe, PBO).
- Use **closing-line value** as the early signal, because bet counts are small.

**Builds on:** [[Tennis — In-Play Market Research]] §3 and §6C (data pipeline). This note covers the *evaluation* rules for it.

## Data sources

| Source | What | Notes |
|---|---|---|
| **Sackmann (tennis_atp/wta, pointbypoint, Match Charting)** | Results, point-by-point, shot-by-shot | Free; the tennis notes call it the backtest fuel. `[Documented]` |
| **Betfair historic data** | Exchange prices, including in-play | **BASIC tier is free**; finer tiers are paid. Read files with `betfairutil` or the official workbook. Tennis coverage needs checking in the catalogue. `[Documented]` |
| **Polymarket `prices-history`** | Price series per token | Data API v2: `interval=max` covers the whole market life at 12-hour buckets; `start/end` windows cap at **15 days** at finer buckets; results are paginated. The CLOB endpoint uses different parameters, so check the spec. `[Documented]` |
| **Our own book recorder** | Full depth, not just prices | The only way to backtest maker fills; see [[Markets — Polymarket Order Book, Fees and Execution]]. |

**Historic prices ≠ fills.** A last-traded price says nothing about whether *your* size would have filled.

## Leakage checklist (tennis-specific)

- [ ] Elo / serve stats computed **only from matches before** the one being bet.
- [ ] In-play: the model sees the score **as of the feed timestamp plus latency**, not the true point time.
- [ ] Odds snapshot taken **before** the decision time, never the bar's close.
- [ ] No survivorship bias: include retirements, walkovers and voided markets.
- [ ] Features that only exist after the fact (final serve %, total points) removed.

## Validation design

- **Walk-forward:** train on months 1–k, test on month k+1, roll forward. Add a **purge/embargo** around boundaries, since matches in the same tournament are correlated. `[Documented]`
- **Multiple-testing correction:** keep a log of every model, feature set and threshold tried. Then:
  - **Deflated Sharpe Ratio** corrects the best result for the number of trials and for non-normal returns. `[Benchmark]`
  - **Probability of Backtest Overfitting (CSCV)** measures how often the in-sample winner ends up below median out of sample; it needs the full trial-by-trial return matrix. `[Benchmark]`
- **Final holdout:** one untouched season, run once.

## Metrics

- **CLV (closing-line value):** did we beat the price at close (or N minutes after entry, for in-play)? It needs far fewer bets than ROI to show skill. For in-play, use "price 5 minutes after entry".
- **ROI and drawdown** come from Kelly-sized bankroll simulation ([[Markets — Kelly Sizing Under Model Uncertainty]]).
- **Calibration by edge bucket** ([[Markets — Calibration Beats Accuracy for Betting Models]]).

## Pitch in

- [ ] ML: create `trials.csv`, which every backtest run appends to (config hash, metrics). Add a DSR/PBO script.
- [ ] Sports: check whether Betfair BASIC includes tennis in-play markets; note the file layout here.

## Sources

- [Deflated Sharpe Ratio (SSRN 2460551)](https://papers.ssrn.com/abstract=2460551) · [Probability of Backtest Overfitting (SSRN 2326253)](https://papers.ssrn.com/abstract=2326253) `[Benchmark]` · [Walk-forward optimisation](https://en.wikipedia.org/wiki/Walk_forward_optimization) `[Documented]`
- [Betfair historic data workbook](https://github.com/betfair/historic-data-workbook) · [betfairutil](https://pypi.org/project/betfairutil) · [Polymarket prices-history](https://docs.polymarket.com/api-reference/markets/get-prices-history.md) · [Polymarket timeseries](https://docs.polymarket.com/developers/CLOB/timeseries.md) `[Documented]`

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — Machine Learning]] · [[State of — ML and Sports Markets]]
