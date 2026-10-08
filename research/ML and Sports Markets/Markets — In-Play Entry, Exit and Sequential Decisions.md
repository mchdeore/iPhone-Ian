---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, machine-learning, robotics, ml-and-sports-markets, optimal-stopping, reinforcement-learning, in-play, trading, agent-based-simulation]
---

# Markets — In-Play Entry, Exit and Sequential Decisions

**TL;DR**
- The fade is a **sequential** decision: enter after a break, then either hold to settlement or **exit when the overreaction reverts** ("vanishes within minutes", Brown 2014).
- Exiting on reversion captures the edge without carrying match-result risk.
- Start with **threshold rules plus optimal-stopping logic**. Use RL only inside a simulator, e.g. an agent-based exchange like the Bristol Betting Exchange. This is the bridge between the two new groups.

**Builds on:** [[Markets — Model plus Market - Blending and the Benter Test]] (gives the gap signal) and [[RL — Where RL Helps a Gantry Robot (and Where It Doesn't)]] (the same "rules first, RL where it pays" logic).

## Two ways to monetise the fade

| Mode | P&L driver | Risk |
|---|---|---|
| **Hold to settlement** | Model fair value vs entry price | Full match variance; capital locked up |
| **Trade the reversion** | Price snaps back toward fair value within minutes | Smaller per-trade P&L; fees on both legs; depends on liquidity at exit |

The tennis research says the mispricing *decays within minutes*. That argues for trading the reversion, with an optional hold if the gap persists.

## Decision structure

- **State:** market price, Markov fair value, gap = market − fair, time since break, score, book depth, position.
- **Actions:** enter (size via [[Markets — Kelly Sizing Under Model Uncertainty]]), hold, exit, add.
- **Baseline policy (rules):** enter when the gap exceeds fee + spread + margin; exit when the gap is below ε, or after T seconds, or on the next break against you. Tune ε, T and the margin by walk-forward ([[Markets — Backtesting Without Fooling Yourself]]).
- **Optimal stopping view:** exit is a stopping-time problem. Entropy-regularised RL formulations for entry and exit exist (Zhao, Tse & Zheng 2026, applied to pairs trading). That's useful theory, but it hasn't been demonstrated on betting exchanges. `[Benchmark]`

## Simulators for learning policies safely

- **Bristol Betting Exchange (BBE):** an agent-based model of second-by-second in-play exchange dynamics, where events mid-event trigger cascades of position changes. `[Benchmark]`
- **XGBoost in BBE** (Terawong & Cliff 2024): learned profitable dynamic wager placement from the profitable bets of simpler agents. It's supervised, not RL, but it's the closest published learning-based in-play exchange policy. `[Benchmark]`
- **Plan:** calibrate a BBE-style simulator to our recorded Polymarket tennis books, then compare the rules baseline with a learned policy (RL or supervised imitation of the best rule runs). Only a policy that beats the rules **out of sample on real recorded books** goes anywhere near money.
- Earlier precedent: a 2008 NTNU thesis trained neural nets on Betfair in-play **tennis** odds against a trading-return cost function rather than prediction error. `[Benchmark]`

## Pitch in

- [ ] ML/RL: fork the BBE code and swap in tennis point dynamics (point-by-point from Sackmann) for horse-race events.
- [ ] Sports: from the event study ([[Markets — Efficiency and Biases in Sports and Prediction Markets]]), report the reversion half-life. That sets the exit timer T.

## Sources

- [BBE — Bristol Betting Exchange (arXiv 2105.08310)](https://arxiv.org/pdf/2105.08310) · [XGBoost dynamic wager placement (SciTePress 2024)](https://www.scitepress.org/Papers/2024/124875/124875.pdf) · [RL optimal stopping for trading (arXiv 2604.02035)](https://arxiv.org/abs/2604.02035) `[Benchmark]`
- [Trading in-play betting exchange markets with ANNs (NTNU)](https://ntnuopen.ntnu.no/ntnu-xmlui/handle/11250/252063) `[Benchmark]`
