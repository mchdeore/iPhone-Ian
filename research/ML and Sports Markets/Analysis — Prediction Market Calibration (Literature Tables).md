---
type: research
status: answered
author: marc
date: 2026-10-08
tags: [sports-analytics, machine-learning, ml-and-sports-markets, market-analysis, polymarket, kalshi, calibration]
---

# Analysis — Prediction Market Calibration (Literature Tables)

**TL;DR**
- Vault had **qualitative** bias notes; this note pins **numbers** from recent large-sample papers and stores them in `literature/market_benchmarks.parquet` for side-by-side compares with our own runs.
- **Politics** on Polymarket/Kalshi: prices **compressed toward 50%** (logistic recalibration slope ≈ **1.45** on Polymarket politics mean) — do **not** read 70¢ as 70% for politics.
- **Sports** on prediction markets: near **calibrated** at short horizons; **trade-size** distortion that hits politics on Kalshi is **~null** for sports (Δ slope ≈ **0.07**, CI crosses zero).
- **Tennis fade anchor** unchanged: Brown in-play mispricing **~5.3%** average, **~10×** pre-match; break → set **~70–75%**.

**Builds on:** [[Markets — Efficiency and Biases in Sports and Prediction Markets]] · [[Tennis — In-Play Market Research]]

## Pandas registry

| dataset_id | File | Purpose |
|---|---|---|
| `literature_market_benchmarks` | `analysis/data/literature/market_benchmarks.parquet` | Paper benchmarks keyed by `benchmark_id` |
| `epl_b365_closing_matches` | `analysis/data/football/epl_b365_closing_matches.parquet` | Our reproduced sports-book calibration ([[Analysis — Premier League Closing-Odds Calibration]]) |

```bash
python analysis/scripts/compare_datasets.py --list
```

## Benchmark table (curated from sources)

| benchmark_id | Domain | Metric | Value | Notes |
|---|---|---|---|---|
| brown_2014_inplay_mispricing_avg | tennis in-play | avg price vs fair | **5.3%** | ~10× pre-match |
| brown_2014_break_to_set_conversion | tennis in-play | break → set win | **70–75%** | fade structural prior |
| walsh_joshi_2024_roi_calibration_vs_accuracy | NBA betting | ROI calibration vs accuracy | **+34.7%** vs **−35.2%** | model *selection* not sizing |
| arxiv_2602_politics_calibration_slope | PM politics | recalibration slope | **1.45** | >1 ⇒ underconfident / compressed |
| arxiv_2602_sports_trade_size_gap | PM sports | large−small trade Δ slope | **0.07** [−0.07, 0.26] | unlike politics whales on Kalshi |
| reichenbach_2026_polymarket_sports_vs_books | Polymarket sports | vs book accuracy | **≈ pro books** | live distortions still possible |

## What this means for our graph / strategy

1. **Polymarket tennis in-play** — treat [[Markets — Cross-Venue Prices - Polymarket, Kalshi and Betfair]] as mandatory: sports *category* may be calibrated on average, but **live** paths can overshoot (Reichenbach 2026; Brown 2014 for tennis specifically).
2. **Politics-style “pull toward 50%”** — do **not** import into tennis without measuring ([[Markets — Efficiency and Biases in Sports and Prediction Markets]] already warned on this).
3. **Next empirical node** — break-event study linking Brown overshoot to Polymarket CLOB history (checklist in [[Tennis — In-Play Market Research]] §6).

## Reproduce / extend literature rows

Edit `analysis/markets_research/literature_benchmarks.py`, then:

```bash
python analysis/scripts/run_epl_closing_odds_study.py
```

(That script rewrites the literature parquet even if you skip football download.)

## Sources

- [Decomposing Crowd Wisdom (arXiv 2602.19520)](https://arxiv.org/abs/2602.19520) · [Code snapshot notes](https://github.com/namanhzz/prediction-market-calibration) `[Benchmark]`
- [When Can Prediction Market Prices Be Trusted? (SSRN 7552098)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7552098) `[Benchmark]`
- Brown 2014 · Walsh & Joshi 2024 — see vault notes above `[Benchmark]`

## Related

- **Summary:** [[State of — ML and Sports Markets]] · [[State of — Sports Analytics]]
