---
type: research
status: answered
author: marc
date: 2026-10-08
tags: [sports-analytics, machine-learning, ml-and-sports-markets, market-analysis, calibration, football-data, datasets]
---

# Analysis — Premier League Closing-Odds Calibration

**TL;DR**
- First **reproduced** numbers in-repo: 3,800 EPL matches (2015–16 → 2024–25), Bet365 **closing** 1X2, stored as parquet.
- Closing line is **well calibrated** overall (log loss ≈ 0.557 on expanded 1X2 rows). Longshot **underdogs** win **slightly more** than priced (+0.17 pp) — weak reverse favourite-longshot, not a free lunch.
- Heavy favourites (80–90% implied) **underpriced** in this sample (+5 pp empirical vs implied) — check sample size (177 rows) before betting on it.

**Builds on:** [[Data — Open Sports Datasets Beyond Tennis]] · [[Markets — Calibration Beats Accuracy for Betting Models]] · [[Markets — Efficiency and Biases in Sports and Prediction Markets]]

## How to refresh

From repo root (see `analysis/README.md`):

```bash
cd analysis && source .venv/bin/activate
python scripts/run_epl_closing_odds_study.py
```

**Registered tables:** `analysis/data/catalog.parquet` → dataset id `epl_b365_closing_matches`

## Global scores (reproduced 2026-10-08)

| Metric | Value |
|---|---|
| Matches | 3,800 |
| Expanded outcome rows (H/D/A) | 11,400 |
| Log loss | 0.557 |
| Brier | 0.188 |

## Favourite vs underdog (closing line, per match)

| Bucket | n | Mean implied | Empirical win rate | Gap (emp − implied) |
|---|---:|---:|---:|---:|
| Closing favorite | 3,822 | 54.4% | 55.4% | +1.0 pp |
| Closing underdog (not longshot) | 1,553 | 27.8% | 27.8% | ~0 |
| Closing underdog **longshot** (<25% implied) | 2,392 | 16.0% | 16.1% | +0.2 pp |

Interpretation: classic **longshot bias** (longshots win *less* than priced) is **not** visible on EPL closers here. That matches “sharp closing line is hard to beat,” and it’s why this dataset is for **method practice** (calibration, Benter, Kelly) not for claiming a soccer edge.

## Reliability by implied-probability bin

| Bin | n | Mean implied | Empirical | Gap |
|---|---:|---:|---:|---:|
| 0.0–0.1 | 550 | 7.3% | 6.7% | −0.6 pp |
| 0.1–0.2 | 1,917 | 15.7% | 15.9% | +0.2 pp |
| 0.2–0.3 | 4,155 | 25.7% | 25.1% | −0.6 pp |
| 0.4–0.5 | 1,161 | 45.0% | 43.8% | −1.3 pp |
| 0.6–0.7 | 603 | 64.8% | 68.7% | +3.9 pp |
| 0.8–0.9 | 177 | 83.7% | 88.7% | +5.0 pp |

Full CSV: `analysis/outputs/tables/epl_b365_reliability_by_bin.csv`  
Figure: `analysis/outputs/figures/epl_b365_calibration_curve.png`

## Pitch in

- [ ] Sports: run the same pipeline on **Betfair closing** or Pinnacle if we add a source column.
- [x] ML: Poisson walk-forward + Benter holdout **2425** → [[Analysis — EPL Poisson Model and Benter Holdout]].
- [ ] Tennis: mirror script once Sackmann + Polymarket history land ([[Tennis — In-Play Market Research]] checklist §6).

## Related

- **Literature table (no download):** [[Analysis — Prediction Market Calibration (Literature Tables)]]
- **Summary:** [[State of — Sports Analytics]] · [[State of — ML and Sports Markets]]
