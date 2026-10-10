---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, machine-learning, ml-and-sports-markets, calibration, brier, log-loss, model-selection, betting]
---

# Markets — Calibration Beats Accuracy for Betting Models

**TL;DR**
- For betting, choose models by **calibration** (are the 60% calls right 60% of the time?), not accuracy.
- Walsh & Joshi (2024, NBA): calibration-selected models averaged **+34.7% ROI** vs **−35.2%** for accuracy-selected.
- Calibration also needs measuring **where you actually bet**: on games where your model disagrees with the market. That's exactly where models are worst calibrated.

**Builds on:** [[Tennis — In-Play Market Research]] (the Markov/Elo fair-value model). This note says how to *grade* it.

## Why accuracy misleads

- Accuracy only asks whether the favourite won. Betting pays on **price vs probability**: a 55% call against a 50% price is a bet; a 90% call against a 92% price isn't.
- **Walsh & Joshi (Machine Learning with Applications 16, 2024):** trained on several NBA seasons, bet one season at published odds. Calibration-based selection averaged +34.69% ROI vs −35.17% for accuracy-based selection (best case +36.93% vs +5.56%). One season of one sport, and bet sizing wasn't checked, so treat this as directional. `[Benchmark]`

## What to measure

| Metric | What it tells you |
|---|---|
| **Log loss** | Strictly proper; punishes confident misses hard. The primary metric. |
| **Brier score** (+ its reliability/resolution split) | Proper and intuitive. The reliability term *is* calibration error. |
| **Reliability diagram / ECE** | Visual check by probability bin. Use ≥10 bins with enough samples each. |
| **Calibration vs market** | Same diagram, but bin by *model − market* edge. This is the new piece below. |

## Calibration where it matters

- You only bet when model ≠ market. That subset is biased toward the model's **errors**: a winner's-curse selection effect.
- Plot outcome frequency against model probability **only for bets placed**, and bin by edge size. If big-edge bets win less often than the model claims, the "edge" is mostly model error. **Shrink toward the market** ([[Markets — Model plus Market - Blending and the Benter Test]]).
- For in-play tennis, also bin by **score state** (e.g. right after a break). The fade lives in exactly that state, and the i.i.d.-points assumption is weakest there.

## Recalibration toolbox

- **Platt / logistic** on logit(p). **Isotonic** when you have lots of data. **Temperature scaling** for neural nets. **Beta calibration** for probabilities squeezed near 0 or 1.
- Fit the calibrator on a held-out period that comes *after* model training (time-ordered, see [[Markets — Backtesting Without Fooling Yourself]]).

## Pitch in

- [x] ML: reliability-by-edge table on EPL holdout (Poisson − close) → [[Analysis — EPL Poisson Model and Benter Holdout]].
- [ ] ML: same plots for tennis backtest.
- [ ] Sports: pick the score states that matter (post-break, set point, tiebreak) for state-conditional calibration.

## Sources

- [Walsh & Joshi — Bath research portal](https://researchportal.bath.ac.uk/en/publications/machine-learning-for-sports-betting-should-model-selection-be-bas/) · [ML in sports betting review (arXiv 2410.21484)](https://arxiv.org/pdf/2410.21484) `[Benchmark]`

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — Machine Learning]] · [[State of — ML and Sports Markets]]
