---
type: summary
status: living
author: marc
date: 2026-10-07
updated: 2026-10-07
tags: [ml-and-sports-markets, machine-learning, sports-analytics, state-of]
---

# State of — ML and Sports Markets

> Living summary of everything tagged #ml-and-sports-markets. **Update this when you add or change a note here**, then bump `updated`.

## Current best answers

- **Grade models by calibration, not accuracy:** +34.7% vs −35.2% ROI in one NBA study. Measure calibration **on the bets you actually place**, binned by edge → [[Markets — Calibration Beats Accuracy for Betting Models]].
- **Use the market as a prior.** The Benter second-stage logit tests whether our model adds information; for the fade, model the **overreaction residual** directly → [[Markets — Model plus Market - Blending and the Benter Test]].
- **Sizing:** Kelly over-bets with estimated p. Shrink by uncertainty (Baker & McHale, tested on tennis), cap per match. Conformal intervals work as a **filter** first and a sizing scale second → [[Markets — Kelly Sizing Under Model Uncertainty]], [[Markets — Conformal Prediction and Edge Uncertainty]].
- **Execution on Polymarket:** taker fees peak at a 50¢ price, makers pay nothing plus rebates. So **be the maker**, but pull quotes at every point end (adverse selection). Use binary Avellaneda–Stoikov with a terminal penalty and spread ∝ point importance → [[Markets — Polymarket Order Book, Fees and Execution]], [[Markets — Market Making in Binary Contracts (Avellaneda-Stoikov)]].
- **Monetise by trading the reversion, not holding to settlement.** Start with threshold rules; RL only in a simulator (BBE-style) → [[Markets — In-Play Entry, Exit and Sequential Decisions]].
- **Honest backtests:** point-in-time features, walk-forward with an embargo, log every trial (Deflated Sharpe/PBO), CLV as the early signal → [[Markets — Backtesting Without Fooling Yourself]].
- **Game-theory frame:** the fade is exploitative play against a market leak, so deviate from "market = fair" only with evidence → [[Game Theory — GTO vs Exploitative Play (Poker and Markets)]].

## Decisions made

- Betfair mid acts as the fair-value anchor even when trading on Polymarket → [[Markets — Cross-Venue Prices - Polymarket, Kalshi and Betfair]].
- Read fee parameters live from each market; never hard-code them.
- Public data + paper trading first; real money only where legal for that member.

## Where sources disagree or we're unsure

- Polymarket sports maker rebate: 25% (docs) vs 20% (secondary). Fee schedules change.
- **Legal:** US circuit courts are split; Polymarket is barred in Ontario and self-restricted in AB/BC/QC → [[Markets — Legal Status of Prediction Markets (US and Canada, Oct 2026)]].
- Resolution risk on retirements and walkovers varies by market → [[Markets — Resolution and Oracle Risk on Polymarket (UMA)]].

## Open questions

- Is there enough depth in live tennis books for a meaningful stake?
- What's the overreaction half-life? (It sets the exit timer.)
- Does the Markov model pass the Benter test against Betfair closing odds?

## Next actions

- [ ] Book recorder for live Polymarket tennis → spread and depth stats.
- [ ] Break event study (with Sports Analytics).
- [ ] Backtester with `trials.csv`, a DSR/PBO script and bootstrap-Kelly.
- [ ] Benter test → go/no-go.

## Changelog

- 2026-10-07: first version.
