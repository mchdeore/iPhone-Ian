---
type: summary
status: living
author: marc
date: 2026-10-07
updated: 2026-10-07
tags: [math, state-of]
---

# State of — Math

> Living summary of everything tagged #math. **Update this when you add or change a math note**, then bump `updated`.

## Current best answers

- **Shared vocabulary:** Nash equilibrium, mixed strategies, the indifference principle, minimax, imperfect information, exploitability, best response → [[Game Theory — Foundations for Sports, Poker and Markets]].
- **Sports are testable games.** Pros equalise win rates across serve and kick directions, but tennis servers switch too often (serial dependence), and the penalty result weakens with 3+ actions → [[Game Theory — Mixed Strategies in Sports (Serves and Penalties)]].
- **Decision analysis:** dynamic programming over field-position value showed systematic 4th-down conservatism (Romer 2006; the 3rd-down proxy is contested) → [[Game Theory — Fourth Down and Coaching Decisions]].
- **Solving imperfect-information games:** CFR (regret matching at every information set; the average strategy converges to Nash in 2-player zero-sum games). CFR+ ~O(1/T) essentially solved heads-up limit hold'em → [[Game Theory — Counterfactual Regret Minimization (CFR)]].
- **Poker AI path:** Cepheus (solved HULHE, 4,800 CPUs × 68 days) → Libratus (beat HUNL pros) → Pluribus (6-player, 12,400 core-hours) → ReBeL (RL + search). Blueprint plus real-time search is the pattern → [[Game Theory — Poker AI Milestones (Cepheus to Pluribus)]].
- **GTO vs exploit:** GTO caps losses, exploitation maximises profit against leaks; node locking computes best responses. It maps directly onto fading market overreaction → [[Game Theory — GTO vs Exploitative Play (Poker and Markets)]].
- **Markets as games:** bookmakers shade prices toward bettor biases and take the risk (Levitt 2004). Market makers price adverse selection into the spread. Limiting sharps is a screening game → [[Game Theory — Bookmakers, Bettors and Market Makers as Games]].

## Cross-links worth knowing

- Kelly, conformal prediction, calibration and the Benter test are the applied math of [[State of — ML and Sports Markets]].
- CFR ↔ RL: both are self-play improvement loops → [[State of — RL and Simple Robots]].
- Point importance is a derivative of the Markov win-probability function → [[Markets — Point Importance and Leverage in Tennis]].

## Open questions

- Do players become *more predictable* on high-importance points (equilibrium breaking under pressure)?
- Can binary-contract market making use regret matching to set spreads online?

## Next actions

- [ ] Implement CFR and CFR+ on Kuhn and Leduc poker; plot exploitability curves.
- [ ] Replicate the Walker–Wooders test on Match Charting data.
- [ ] Rebuild Romer's 4th-down chart on nflverse 2015–2025.

## Changelog

- 2026-10-07: first version.

## Other summaries

[[State of — Sports Analytics]] · [[State of — Machine Learning]] · [[State of — Cybersecurity]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]] · [[State of — ML and Sports Markets]] · [[State of — YOLO]] · [[State of — System Design]]
