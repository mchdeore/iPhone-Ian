---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, ml-and-sports-markets, conformal-prediction, uncertainty, kelly]
---

# Markets — Conformal Prediction and Edge Uncertainty

**TL;DR**
- Conformal prediction wraps any model and gives intervals with a **distribution-free, finite-sample coverage guarantee**.
- That's the uncertainty Kelly sizing needs ([[Markets — Kelly Sizing Under Model Uncertainty]]). But a 2026 preprint warns that plugging interval width straight into Kelly's denominator **adds variance that costs compound growth**. Smooth the width before using it.
- Most useful as a **bet filter**: bet only when the whole interval is on one side of the market price.

## The guarantee

Split conformal: hold out a calibration set, compute nonconformity scores (e.g. |y − p̂|), and take the (1 − α) quantile as the interval half-width. New predictions then have ≥ 1 − α coverage under exchangeability [1].

**For binary outcomes**, use conformal *on the probability* via a calibration-set approach (e.g. Venn-Abers or conformal calibration), or conformalise a regression target such as the price change over N minutes from [[Markets — Model plus Market - Blending and the Benter Test]].

## Conformal Kelly (2026 preprint)

- Proposes the conformal interval width as the **scale in fractional Kelly** [2].
- Caveat from the same paper: Kelly needs a full return distribution, while an interval gives one number. A noisy scale enters the sizing nonlinearly and "its estimation variance is charged directly to compound growth". Intervals that adapt sharply make *poor* Kelly denominators [2].
- Practical reading: use **slowly varying** (e.g. per score-state bucket) interval widths for sizing, not per-bet adaptive ones.

## Three uses, from safest

1. **Filter:** bet only when the conformal interval for fair value excludes the market price (after fees).
2. **Size cap:** stake ∝ distance from the market to the *near* edge of the interval, not the point estimate.
3. **Monitor:** coverage on live bets should match 1 − α. A drop signals **distribution shift** (new season, surface change, venue behaviour change), so stop and recalibrate.

## Caveat: exchangeability

In-play tennis points within a match aren't exchangeable, and seasons drift. Use **match-level** calibration splits and recent windows, or adaptive conformal methods. Check empirical coverage by month.

## Pitch in

- [ ] ML: add split-conformal intervals to the backtest; compare (a) no filter, (b) the interval-excludes-market filter, (c) Conformal-Kelly sizing.

## Sources

1. [Shafer & Vovk — A tutorial on conformal prediction (arXiv 0706.3188)](https://arxiv.org/pdf/0706.3188) `[Benchmark]`
2. [Conformal Kelly (arXiv 2608.01494)](https://arxiv.org/pdf/2608.01494) `[Benchmark]` (preprint)
3. [Kelly betting as Bayesian model evaluation (arXiv 2602.09982)](https://arxiv.org/html/2602.09982v1) `[Benchmark]`
4. [Metel — Kelly with uncertain probabilities (arXiv 1701.02814)](https://ar5iv.arxiv.org/html/1701.02814) `[Benchmark]`
