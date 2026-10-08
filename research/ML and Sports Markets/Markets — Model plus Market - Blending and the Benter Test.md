---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, machine-learning, ml-and-sports-markets, model-blending, benter, market-prior, residual-modeling, logistic-regression]
---

# Markets — Model plus Market: Blending and the Benter Test

**TL;DR**
- Don't try to beat the market *instead of* using it. **Use it as the prior and model what it misses.**
- Benter's second-stage logit does this: regress outcomes on logit(model) and logit(market). If the model's coefficient is significant, it adds information; the blended probability is what you bet.
- For the tennis fade, go one step further and **target the market's overreaction directly** as the residual.

**Builds on:** [[Markets — Calibration Beats Accuracy for Betting Models]] (shrink toward the market) and [[Markets — Efficiency and Biases in Sports and Prediction Markets]].

## The Benter second stage

**logit(p_final) = α · logit(p_model) + β · logit(p_market)**, fitted on held-out outcomes.

- In Benter's 1994 horse-racing work (2,313 races), the fundamental model alone had pseudo-R² .1016, about the same as a tipster tally (.1014). Combined with the public odds, the model **added +.0090** while the tipster added +.0002. A model can look no better alone yet still carry real *extra* information. `[Community]` (secondary source; check the original paper)
- What the test tells you:
  - α ≈ 0: the model adds nothing over the market. Stop.
  - α > 0, β > 0: bet on p_final, not p_model.
  - β > 1 or < 1: the market itself is mis-scaled (FLB-type bias). Worth knowing on its own.

## Other blending methods

- **Hierarchical Bayesian** (Egidi, Pauli & Torelli 2018, football): scoring rates are convex combinations of historical-data parameters and odds-implied parameters inside the model. `[Benchmark]`
- **Shrinking toward climatology or market** also improves calibration and reliability, as seen in football shot models where blending beat Platt scaling. `[Benchmark]`

## The residual model for tennis in-play

Instead of predicting the match winner, predict **where the market will be (or the outcome) relative to its current price**:

- **Target:** y = outcome − p_market(t), or the price change over the next N minutes.
- **Features:** p_market(t); the Markov fair value from the score; *market − Markov* (the overreaction gap); time since the break; pressure-point flags and clutch profile ([[Tennis — Player and Matchup Modeling]]); fatigue signals from the tennis checklist; book imbalance.
- **Why:** the model only has to learn *when the market is wrong*, which is a much smaller and better-posed problem than tennis win probability from scratch. It plugs straight into the Benter test.

## Pitch in

- [ ] ML: run the Benter test on the Markov model against Betfair closing odds over the backtest set; post α, β and the confidence intervals.
- [ ] Sports: list candidate residual features from the player-modeling note that are available live.

## Sources

- [Benter's second-stage test explained](https://oddspapi.io/blog/?p=3174) `[Community]`
- [Egidi et al. — combining historical data and odds (arXiv 1802.08848)](https://arxiv.org/pdf/1802.08848) · [Statistical Modelling 18(5-6)](https://statmod.org/smij/Vol18/Iss5-6/Egidi/Abstract.html) · [Probabilistic shot-success model (arXiv 2101.02104)](https://arxiv.org/pdf/2101.02104) `[Benchmark]`

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — Machine Learning]] · [[State of — ML and Sports Markets]]
