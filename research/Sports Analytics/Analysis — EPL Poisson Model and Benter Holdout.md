---
type: research
status: answered
author: marc
date: 2026-10-08
tags: [sports-analytics, machine-learning, ml-and-sports-markets, market-analysis, benter, poisson, walk-forward]
---

# Analysis — EPL Poisson Model and Benter Holdout

**TL;DR**
- Walk-forward **Poisson** 1X2 on EPL (train all seasons before each test year) → **2223–2425** OOS predictions in parquet.
- **Benter second stage** fit on **2223–2324**, evaluated on **2425 holdout only** (no leakage).
- **α_model ≈ −0.12** (95% bootstrap **includes 0**): simple Poisson **does not add information** beyond Bet365 closing home price. **Stop** betting raw model edges.
- Holdout log loss: **market 0.588** · Poisson **0.667** · Benter blend **0.594** — blend does **not** beat close on 2425.
- **Edge calibration:** every model−market bucket ≥3pp **underperforms** model probability (winner's curse); flat ROI **−41%** on raw ≥3pp edges in holdout.

**Builds on:** [[Analysis — Premier League Closing-Odds Calibration]] · [[Markets — Model plus Market - Blending and the Benter Test]] · [[Markets — Calibration Beats Accuracy for Betting Models]] · [[Data — Open Sports Datasets Beyond Tennis]]

## Reproduce

```bash
cd analysis && source .venv/bin/activate
python scripts/run_epl_closing_odds_study.py   # if parquet stale
python scripts/run_epl_benter_study.py
```

| Output | Path |
|---|---|
| Per-match OOS preds | `analysis/data/football/epl_poisson_walkforward_predictions.parquet` |
| Benter coefs | `analysis/outputs/tables/epl_benter_coefficients.csv` |
| Edge buckets | `analysis/outputs/tables/epl_home_edge_calibration.csv` |
| Trial log | `analysis/data/trials.csv` |

## Benter (fit 2223–2324, n=760 home outcomes)

| Coef | Value | Bootstrap 2.5% | 50% | 97.5% |
|---|---:|---:|---:|---:|
| α (logit model) | **−0.117** | −0.43 | −0.13 | +0.17 |
| β (logit market) | **1.19** | 0.92 | 1.22 | 1.51 |

Read: market weight >1 is mild **FLB / scale** on home closers in-sample; **model coefficient not significantly positive** — matches Benter go/no-go rule in [[Markets — Model plus Market - Blending and the Benter Test]].

## Holdout 2425 (380 matches) — home win only

| Forecaster | Log loss | Brier |
|---|---:|---:|
| Bet365 close | **0.588** | **0.203** |
| Poisson | 0.667 | 0.236 |
| Benter blend | 0.594 | 0.205 |

Mean CLV (model − close): **−0.16 pp** (model slightly pessimistic vs close).

## Calibration by edge (Poisson − close, holdout, bets with edge ≥3pp)

| Edge bucket | Bets | Model p | Empirical win | Realized − model |
|---|---:|---:|---:|---:|
| 3–6 pp | 34 | 49.6% | 32.4% | **−17.2 pp** |
| 6–10 pp | 34 | 44.5% | 23.5% | −21.0 pp |
| 10–15 pp | 30 | 45.1% | 23.3% | −21.7 pp |
| 15–25 pp | 39 | 49.0% | 20.5% | −28.5 pp |
| 25 pp+ | 20 | 61.2% | 25.0% | −36.2 pp |

Flat 1u ROI (holdout, ≥3pp edge): **−41%** (157 bets). Benter-blend ≥3pp: **−3.9%** (204 bets) — still negative.

## Implications for tennis / Polymarket work

1. **Closing (or Betfair mid) is the prior.** Same pipeline we will use on Markov fair value vs Betfair close before claiming Polymarket fade edge.
2. **Bet only calibrated residuals**, not raw model−market gaps ([[Markets — Calibration Beats Accuracy for Betting Models]]).
3. **Practice project succeeded:** methods work; **this Poisson spec does not find soccer CLV** — expected on EPL closers.

## Pitch in

- [ ] ML: hierarchical Poisson (Egidi-style odds prior inside likelihood) — see [[Markets — Model plus Market - Blending and the Benter Test]].
- [ ] Sports: repeat Benter with **draw / away** or 3-way multinomial logit.
- [ ] Tennis: Markov model + Betfair close on Sackmann holdout season.

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — ML and Sports Markets]]
