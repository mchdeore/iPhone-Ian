---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, cybersecurity, ml-and-sports-markets, math, game-theory, adverse-selection, bookmaking, market-microstructure]
---

# Game Theory — Bookmakers, Bettors and Market Makers as Games

**TL;DR**
- **Levitt (Economic Journal 2004):** bookmakers *don't* balance their books like financial market makers. They **set prices away from market-clearing to exploit bettor biases** and take the risk, because they forecast better than most bettors.
- Financial market makers instead widen spreads to cover **adverse selection** from informed traders (the Glosten–Milgrom logic).
- Account limiting ([[Betting — Account-Level Behavior Models]]) is the bookmaker's move in a **screening game**: find and remove informed players.
- Prediction-market CLOBs bring back the financial structure, which is why bots are welcome there.

**Builds on:** [[Game Theory — GTO vs Exploitative Play (Poker and Markets)]] and [[Markets — Market Making in Binary Contracts (Avellaneda-Stoikov)]].

## Levitt's puzzle and answer

- **Puzzle:** gambling and financial markets are both zero-sum with heterogeneous beliefs and big money, yet they're organised completely differently [1].
- **Answer:** the bookmaker "does not play the traditional role of market makers matching buyers and sellers but, rather, takes large positions" [1][2]. It can out-forecast bettors **and** shade prices toward bettor biases; rational bettors limit how far it can shade [1].
- **Evidence:** an online bookmaker's NFL contest, 2001–02: 285 entrants, 19,770 bets, 242 games. Aggregate risk to the book was minimal, and there was little evidence of bettors who could systematically beat it [2][3].

## Adverse selection (Glosten–Milgrom, background)

A market maker trading against a mix of informed and uninformed traders loses to the informed and recovers from the uninformed via the **spread**. More informed flow → wider spread → prices update after each trade (each trade carries information). This is standard theory, not from our search results; Levitt's paper discusses the contrast [1].

## Three games in the betting ecosystem

| Game | Players | Equilibrium logic | Our relevance |
|---|---|---|---|
| **Pricing** | Book vs bettors | Book shades lines toward biases; informed bettors cap the shading | Biases persist where informed money is limited, i.e. retail in-play |
| **Screening** | Book vs sharps | Profile behaviour → limit or ban winners (a separating equilibrium) | [[Betting — Account-Level Behavior Models]]; why the sanctioned API venue matters |
| **Market making** | Maker vs informed takers | Spread ≥ expected loss to informed flow; requote on news | Our maker quotes in-play: pull quotes at point end ([[Markets — Polymarket Order Book, Fees and Execution]]) |
| **Detection** | Platform vs automation | Attacker–defender arms race | [[Betting Apps — Behavioral and Automation Detection]] (security view) |

## Research directions

- **Measure adverse selection on Polymarket tennis:** after our simulated maker fills, does the price move against us within 10 s? The answer sets the minimum spread.
- **Levitt-style bias test:** do Polymarket tennis prices shade toward popular players (name recognition) beyond what the model says?

## Sources

1. [Levitt — Why are Gambling Markets Organised So Differently from Financial Markets? (EJ 2004, PDF)](https://www.stat.berkeley.edu/%7Ealdous/157/Papers/Levitt_Gambling_2004.pdf) · [IDEAS](https://ideas.repec.org/a/ecj/econjl/v114y2004i495p223-246.html) `[Benchmark]`
2. [Levitt — How Do Markets Function? (NBER w9422)](https://www.nber.org/papers/w9422) `[Benchmark]`
3. [AcaWiki summary](https://acawiki.org/Why_are_Gambling_Markets_Organised_So_Differently_from_Financial_Markets%3F) `[Community]`

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — Cybersecurity]] · [[State of — ML and Sports Markets]] · [[State of — Math]]
