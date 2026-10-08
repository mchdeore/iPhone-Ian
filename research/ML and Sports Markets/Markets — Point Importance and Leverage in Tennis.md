---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, ml-and-sports-markets, tennis, point-importance, leverage, markov]
---

# Markets — Point Importance and Leverage in Tennis

**TL;DR**
- **Importance** of a point = how much the match win probability swings on it: Imp = M(server wins point) − M(returner wins point) (Morris 1977).
- It tells you *which points move the market most*, so it's the natural feature for spread-setting, entry timing and the "is this break real?" filter.
- Klaassen & Magnus showed servers win **fewer** points on important points, and **weaker players more so**. Points aren't i.i.d. exactly where it matters.

**Builds on:** [[Tennis — In-Play Market Research]] §2 (the Markov model gives M(a, b)) and [[Tennis — Player and Matchup Modeling]] §1d (pressure points).

## Definition

Let M(a, b) be the probability the current server wins the match from score (a, b). Then **Imp(a, b) = M(a + 1, b) − M(a, b + 1)** [1]. It's cheap to compute from the same Markov recursion already used for fair value. Kovalchik & Reid's version assumes both servers win 65% of service points (the ATP average) [1].

## What the research says

- **Points aren't i.i.d.:** at important points it's harder for the server to win, and the weaker the player, the stronger the effect (Klaassen & Magnus 2001) [2].
- The book *Analyzing Wimbledon* (2014) covers which points matter, match prediction and serving strategy [3]. Their "Richard" program updates win probability within a second [4].
- Little academic work exists on importance in pro scoring beyond this line [5].

## How to use it

| Use | How |
|---|---|
| **Feature for the residual model** | Importance of the break point that was just converted: high importance, plus a clutch player, means a more "real" break ([[Markets — Model plus Market - Blending and the Benter Test]]) |
| **Adjust the Markov model** | Lower the server's p on high-importance points, more so for weaker players (Klaassen–Magnus). That improves fair value right where the fade trades |
| **Market-making spread** | Spread ∝ upcoming point importance ([[Markets — Market Making in Binary Contracts (Avellaneda-Stoikov)]]) |
| **Entry timing** | Avoid entering just before a very high-importance point unless the model edge is large, since price variance is maximal there |
| **Leverage-weighted stats** | Weight a player's clutch stats by importance, not by the raw "break point" label |

## Pitch in

- [ ] ML: add `importance(a, b, p, q)` to the Markov module; plot the importance heatmap for best-of-3 vs best-of-5.
- [ ] Sports: test whether market overreaction size scales with the importance of the break point (Polymarket/Betfair event study).

## Sources

1. [Kovalchik & Reid — importance (via SA-IJAS PDF)](https://sa-ijas.org/ojs/index.php/sa-ijas/article/download/30-11/52/370) `[Benchmark]`
2. [Are points in tennis i.i.d.? (Klaassen & Magnus)](https://academicnewsletter.sufe.edu.cn/info/446049) `[Benchmark]`
3. [Analyzing Wimbledon — Tinbergen news](https://tinbergen.nl/news/261/analyzing-wimbledon-new-book-by-fellows-klaassen-and-magnus) `[Documented]`
4. [ITF Coaching Review — Klaassen & Magnus](https://itfcoachingreview.com/index.php/journal/article/download/478/1296/1943) `[Documented]`
5. [Emerging Investigators — point importance](https://emerginginvestigators.org/articles/24-370/pdf) `[Community]`

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — ML and Sports Markets]]
