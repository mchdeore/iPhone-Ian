---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, machine-learning, math, game-theory, dynamic-programming, nfl, decision-analysis]
---

# Game Theory — Fourth Down and Coaching Decisions

**TL;DR**
- **Romer (Journal of Political Economy 2006)** used dynamic programming on NFL play-by-play and found coaches kick far too often on 4th down: "systematic, clear-cut, and overwhelmingly statistically significant" departures from win-maximising choices.
- The method (value of field position + success probability → expected-value comparison) is a reusable template for **any sport's** strategic decisions.
- It's also an example of a **market inefficiency that persisted for years**, because the decision-makers' incentives (avoiding blame) differ from winning.

**Builds on:** [[Game Theory — Foundations for Sports, Poker and Markets]]; data from [[Data — Open Sports Datasets Beyond Tennis]] (nflverse).

## Romer's method

1. Estimate the **value of having the ball at each yard line** (expected point differential) from play-by-play, via dynamic programming [1].
2. For each 4th-down situation, compare EV(go for it) = P(convert)·V(first down) + (1 − P)·V(turnover on downs) against EV(punt) and EV(field goal).
3. **Proxy:** 4th-down conversion rates are rare, so 3rd-down success rates stand in for them [2].

## Findings

- Data: first-quarter 4th downs, 1998–2000 (to avoid end-game distortions) [3]; one account counts 1,068 situations where teams kicked in 959 [3].
- Rule of thumb: inside the opponent's 45, facing less than 4th-and-8, going for it beats punting [4].
- Example: 4th-and-goal from the 3 early in the game. Teams kicked 38 of 47 times [3].
- **Critique:** Adams (AEA 2008) argues the third-down proxy overstates the case; coaches may be closer to optimal [2].

## Where game theory comes in

- 4th down alone is decision analysis against nature. **Play-calling** (run vs pass) is a **mixed-strategy game** against the defence, and the indifference principle predicts equal success rates across play types at equilibrium. Testing that on nflverse data is a natural extension (not covered by our sources yet).
- **Incentives:** coaches minimise *blame risk*, not loss probability, a principal–agent problem. The same structure explains why markets misprice: participants optimise something other than accuracy.

## Transfer to tennis and markets

- Tennis tactical choices (serve-and-volley, challenge usage, tanking a set) can get the same DP treatment with the Markov model as the value function.
- In markets, the "coach" is the crowd. Find decisions where participants systematically optimise the wrong thing (fear of the break → overreaction).

## Pitch in

- [ ] Sports: rebuild Romer's 4th-down chart on nflverse 2015–2025 data; has the inefficiency closed since analytics went mainstream?

## Sources

1. [Romer — Do Firms Maximize? Evidence from Professional Football (JPE 2006)](https://eml.berkeley.edu/%7Edromer/papers/JPE_April06.pdf) `[Benchmark]`
2. [Adams — critique (AEA 2008)](https://topcat.aeaweb.org/annual_mtg_papers/2008/2008_386.pdf) `[Benchmark]`
3. [ESPN — Romer fourth-down coverage](https://www.espn.in/espnmag/story?id=3641375) `[Community]`
4. [Statistics and decision making in football](https://bakadesuyo.com/2009/10/statistics-and-effective-decision-making-in-f/) `[Community]`

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — Machine Learning]] · [[State of — Math]]
