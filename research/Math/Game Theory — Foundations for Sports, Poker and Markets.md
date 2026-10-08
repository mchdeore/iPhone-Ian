---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, ml-and-sports-markets, math, game-theory, nash-equilibrium, minimax, mixed-strategies]
---

# Game Theory — Foundations for Sports, Poker and Markets

**TL;DR**
- Game theory studies decisions where **your best move depends on what others do**.
- Four ideas cover almost everything in this series: **Nash equilibrium**, **mixed strategies** (randomise so you can't be exploited), the **minimax theorem** for two-player zero-sum games, and **imperfect information** (you don't see the other side's cards or intentions).
- Sports, poker and betting markets are all games of this kind. This note is the shared vocabulary for the other six.

## Core concepts

| Concept | Meaning | Where it shows up |
|---|---|---|
| **Zero-sum game** | One side's gain is the other's loss | Penalty kicks, a serve point, heads-up poker, a bettor vs a bookmaker |
| **Nash equilibrium** | Strategies where no player gains by changing alone | GTO poker; equilibrium serve mix |
| **Mixed strategy** | Choose actions randomly with fixed probabilities | Serve left/right, kick left/right, bluff frequency |
| **Indifference principle** | At equilibrium, every action you mix between has the **same expected payoff** | The testable prediction in sports ([[Game Theory — Mixed Strategies in Sports (Serves and Penalties)]]) |
| **Minimax (von Neumann)** | In 2-player zero-sum games, maximising your worst case = equilibrium; the game has a single value | Why GTO is "unexploitable" ([[Game Theory — GTO vs Exploitative Play (Poker and Markets)]]) |
| **Imperfect information** | Players hold private information (cards, fitness, intent) | Poker AI needs special algorithms ([[Game Theory — Counterfactual Regret Minimization (CFR)]]) |
| **Exploitability** | How much a perfect opponent could win against your strategy | The quality metric for poker bots |
| **Best response** | The strategy that maximises payoff against a *fixed* opponent strategy | Exploitative play; node locking |

## Worked micro-example: the 2×2 serve game

Server picks Left/Right; returner guesses L/R. The server's win probabilities are: guessed correctly → 0.55, guessed wrong → 0.80 (illustrative). The server's equilibrium mix makes the returner **indifferent**; solve p·0.55 + (1 − p)·0.80 = p·0.80 + (1 − p)·0.55 → p = 0.5 in this symmetric case. Asymmetric payoffs give skewed mixes. The real data tests are in the next note.

## Why the group should care

- **Sports analytics:** coaching decisions (mix rates, 4th down) are testable against equilibrium. Deviations are inefficiencies.
- **ML:** CFR and RL are the same kind of algorithm ("learn from regret or reward"). Poker AI is where self-play RL was proven on imperfect information.
- **Markets:** pricing against informed traders is an imperfect-information game ([[Game Theory — Bookmakers, Bettors and Market Makers as Games]]).
- **Security:** attacker and defender are a game. Bot detection vs automation is a classic one.

## Sources

1. [Walker & Wooders — Minimax Play at Wimbledon (AER 2001)](https://www.math.stonybrook.edu/~gaston/print/Old/WimbledonAER.pdf) `[Benchmark]`
2. [Zinkevich et al. — Regret Minimization in Games with Incomplete Information (NeurIPS 2007)](https://proceedings.neurips.cc/paper/2007/hash/08d98638c6fcd194a4b1e6992063e944-Abstract.html) `[Benchmark]`
3. [Cornell INFO 2040 — Game theory in tennis](https://nsdl.library.cornell.edu/websites/expertvoices/info2040/archives/1888.html) `[Community]`

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — ML and Sports Markets]] · [[State of — Math]]
