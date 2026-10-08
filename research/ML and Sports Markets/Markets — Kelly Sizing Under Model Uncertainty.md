---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, machine-learning, ml-and-sports-markets, kelly, bankroll, position-sizing, uncertainty, risk]
---

# Markets — Kelly Sizing Under Model Uncertainty

**TL;DR**
- Kelly sizing maximises long-run growth *if* your probability is right. Plug in an **estimated** probability and you systematically **over-bet**.
- Baker & McHale (2013, tested on **tennis** betting) show stakes should be **shrunk** by an amount that depends on your uncertainty.
- Fixed half-Kelly is the crude version. Better: size from the model's own uncertainty, e.g. a posterior or bootstrap spread on the edge.

**Builds on:** [[Markets — Calibration Beats Accuracy for Betting Models]]. Calibration gives an honest p; this note turns p into a stake.

## The formula

For decimal odds *d* (net odds b = d − 1), win probability *p*, q = 1 − p:

**f\* = (b·p − q) / b**, the fraction of bankroll to stake.

On a prediction-market share bought at price *c* (pays $1): b = (1 − c)/c, so f\* = (p − c)/(1 − c).

## Why estimated p over-bets

- Errors don't cancel. Bets where you *over*-estimated p look the most attractive and get the biggest stakes. Plug-in Kelly does worse out of sample than in sample (Metel 2017). `[Benchmark]`
- **Baker & McHale (Decision Analysis 10(3), 2013):** shrink the Kelly stake under parameter uncertainty. The shrunken versions beat raw Kelly in simulation and on tennis data, and they give a quick approximate shrinkage factor. (The exact form isn't reproduced here; read the paper before implementing.) `[Benchmark]`
- The robust result: **more uncertainty → bet further below Kelly**, with the fraction *varying* by bet rather than a fixed ½. `[Community]`

## A practical recipe

1. Get a **distribution** for p on each bet: a Bayesian posterior, or a bootstrap over training data, or an ensemble spread.
2. Compute f\* for each draw; stake the **mean of the f\* draws** (negative draws count as 0 bets). Or take a low quantile, if you're cautious.
3. **Cap** each bet at ≤2–5% of bankroll and cap total exposure per match. In-play tennis bets on the same match are correlated.
4. Simulate bankroll paths in the backtest: report median growth, the 5th-percentile drawdown, and the probability of ruin.

Rule of thumb (a heuristic, not from the paper): if the edge estimate's standard error is about equal to the edge itself, a stake near ½ Kelly is in the right range. If the SE is twice the edge, don't bet.

## Interplay with account limits

On sportsbooks, aggressive sizing speeds up limiting ([[Betting — Account-Level Behavior Models]]). On Polymarket the limit is **book depth**: f\* is capped by what fills without moving the price ([[Markets — Polymarket Order Book, Fees and Execution]]).

## Pitch in

- [ ] ML: add bootstrap-Kelly to the backtester; compare full, ½, and uncertainty-scaled Kelly on the same bets.
- [ ] Sports: decide the bankroll and the per-match exposure caps as a group.

## Sources

- [Baker & McHale — Optimal betting under parameter uncertainty (IDEAS)](https://ideas.repec.org/a/inm/ordeca/v10y2013i3p189-199.html) · [Salford repository](https://salford-repository.worktribe.com/output/1410355/optimal-betting-under-parameter-uncertainty-improving-the-kelly-criterion) `[Benchmark]`
- [Metel — Kelly betting with uncertainty (arXiv 1701.02814)](https://arxiv.org/pdf/1701.02814) `[Benchmark]` · [Kelly criterion (Wikipedia)](https://en.wikipedia.org/wiki/Kelly_criterion) · [Never Go Full Kelly](https://www.lesswrong.com/posts/TNWnK9g2EeRnQA8Dg/never-go-full-kelly) `[Community]`

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — Machine Learning]] · [[State of — ML and Sports Markets]]
