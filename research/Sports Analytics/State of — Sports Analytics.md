---
type: summary
status: living
author: marc
date: 2026-10-07
updated: 2026-10-07
tags: [sports-analytics, state-of]
---

# State of — Sports Analytics

> Living summary of everything tagged #sports-analytics. **Update this when you add or change a sports note**, then bump `updated`.

## Current best answers

- **Main project:** fade overreactions to a single break of serve in in-play tennis. In-play mispricing is ~10× pre-match (5.3% average, Brown 2014), and momentum is empirically small → [[Tennis — In-Play Market Research]].
- **Fair value:** a point → game → set → match Markov model with surface-blended Elo and Barnett–Clarke serve/return adjustment. Points are *mildly* non-i.i.d. → [[Tennis — In-Play Market Research]] §2.
- **What predicts:** Dominance Ratio (~76% of RF feature importance), return points won, 2nd-serve points won. Mostly noise: aces, total points. The lefty effect is a free prior → [[Tennis — Player and Matchup Modeling]].
- **Point importance** (Morris) says where win probability swings. Servers do *worse* on important points, and weaker players more so (Klaassen–Magnus) → [[Markets — Point Importance and Leverage in Tennis]].
- **Game theory in sport:** pros are near equilibrium on serve and penalty direction, but servers **switch too often**, which is forecastable. NFL coaches were too conservative on 4th down (Romer) → [[Game Theory — Mixed Strategies in Sports (Serves and Penalties)]], [[Game Theory — Fourth Down and Coaching Decisions]].
- **Sportsbooks limit winners and run regulator-required harm models.** An automated in-play strategy trips both → [[Betting — Account-Level Behavior Models]].

## Decisions made

- Free data first: Sackmann point-by-point and the Match Charting Project; Betfair BASIC; Polymarket price history → [[Markets — Backtesting Without Fooling Yourself]].
- Practise the full pipeline on football-data.co.uk closing odds while the tennis data is built → [[Data — Open Sports Datasets Beyond Tennis]].

## Where sources disagree or we're unsure

- **Access:** Polymarket is barred in Ontario and self-restricted in AB/BC/QC. For Canadian members the tennis track may be research and paper trading only → [[Markets — Legal Status of Prediction Markets (US and Canada, Oct 2026)]].
- The favourite-longshot bias partly works *against* buying the post-break underdog, and it has to be separated from the overreaction → [[Markets — Efficiency and Biases in Sports and Prediction Markets]].

## Open questions

- Is Polymarket's retail in-play tennis flow less efficient than Betfair's? (Make-or-break.)
- Does the overreaction scale with the importance of the converted break point?
- How "harm-shaped" is the strategy (in-play bets per day, session hours)?

## Next actions

- [ ] Break event study: Polymarket vs Betfair price paths −60 s to +600 s.
- [ ] Replicate the Walker–Wooders serve test on Match Charting data, with a "predictability under pressure" column.
- [ ] Collect the retirement and walkover rules from 10 Polymarket tennis markets.

## Changelog

- 2026-10-07: first version.

## Other summaries

[[State of — Machine Learning]] · [[State of — Cybersecurity]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]] · [[State of — ML and Sports Markets]] · [[State of — Math]] · [[State of — YOLO]]
