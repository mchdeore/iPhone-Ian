---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, math, game-theory, poker, cfr, libratus, pluribus, deepstack, rebel]
---

# Game Theory — Poker AI Milestones (Cepheus to Pluribus)

**TL;DR**
- In about five years poker AI went from **solving** a small poker variant (Cepheus 2015) to **beating elite pros heads-up** (Libratus 2017) to **beating pros at 6-player** (Pluribus 2019) on **12,400 CPU core-hours**.
- The lessons that carry over: **abstraction + equilibrium blueprint + real-time search**. Cost falls by orders of magnitude when search replaces brute-force precomputation.

**Builds on:** [[Game Theory — Counterfactual Regret Minimization (CFR)]].

## Timeline

| System | Game | Method | Result | Compute |
|---|---|---|---|---|
| **Cepheus** (Alberta, Science 2015) | Heads-up **limit** hold'em | CFR+ | "**Essentially weakly solved**": a lifetime of play couldn't show it isn't exact; exploitability < 1 mbb/g; formally proves the dealer's advantage [1][2][3] | 4,800 CPUs × 68 days [3] |
| **DeepStack** (2017) | Heads-up **no-limit** (HUNL) | Depth-limited search + learned value nets | Beat non-elite pros; never beat prior top AIs [4] | >1M core-hours [4] |
| **Libratus** (CMU, 2017) | HUNL | Blueprint (MCCFR) + subgame solving + self-improvement | Beat 4 top specialists over 120k hands; ~14.7 bb/100 reported [5][6] | Millions of core-hours, TBs of memory [5] |
| **Depth-limited solving** (Brown et al. 2018) | HUNL | Cheaper search | Beat prior top AIs at orders of magnitude less compute [4] | Small |
| **Pluribus** (CMU/Facebook, 2019) | **6-player** NLHE | Blueprint + depth-limited search | Beat 15 pros; ~48 mbb/game reported [6] | **12,400 core-hours**, 64 cores, 8 days, <512 GB RAM [7] |
| **ReBeL** (2020) | HUNL | Deep RL + search, a unified AlphaZero-style framework | Superhuman with far less domain knowledge; **provably converges** in 2-player zero-sum games [8][9] | — |

## Lessons for us

- **Two-player zero-sum theory doesn't carry over to multiplayer.** No equilibrium guarantee at 6 players. Pluribus worked anyway, which is a pragmatic lesson for multi-agent markets.
- **Blueprint + real-time search** is the pattern: compute a coarse strategy offline, refine it at decision time. It's analogous to a pre-trained policy plus test-time search in GUI agents.
- **Compute fell ~100×** between Libratus and Pluribus through better *algorithms*, not hardware. Search smarter before scaling.
- **Evaluation:** poker reports win rate in mbb/g or bb/100 with significance over huge samples, and AIVAT-style variance reduction. Our backtests need the same rigour ([[Markets — Backtesting Without Fooling Yourself]]).

## Pitch in

- [ ] Math/ML: after Kuhn/Leduc CFR, try OpenSpiel's implementations of MCCFR and Deep CFR; write up the speedups here.

## Sources

1. [Bowling et al. — Heads-up limit hold'em is solved (Science)](https://webdocs.cs.ualberta.ca/~bowling/publications/b2hd-15science.html) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/25574016) `[Benchmark]`
2. [CACM 2017 extended version](https://www.cs.ualberta.ca/~games/poker/publications/heads-up_limit_poker_is_solved.acm2017.pdf) `[Benchmark]`
3. [Tammelin et al. — CFR+ (IJCAI 2015)](https://www.cs.ualberta.ca/~games/poker/publications/2015-ijcai-cfrplus.pdf) `[Benchmark]`
4. [Brown, Sandholm & Amos — Depth-Limited Solving (arXiv 1805.08195)](https://arxiv.org/pdf/1805.08195) `[Benchmark]`
5. [PokerGPT — background on Libratus compute (arXiv 2401.06781)](https://arxiv.org/pdf/2401.06781) `[Benchmark]`
6. [DeucesCracked — poker AI timeline](https://www.deucescracked.com/blog/poker-ai-research-timeline-data) `[Community]`
7. [The Register — Pluribus](https://www.theregister.com/2019/07/12/pluribus_ai_poker_human_pros) `[Documented]`
8. [ReBeL (NeurIPS 2020)](https://proceedings.neurips.cc/paper/2020/hash/c61f571dbd2fb949d3fe5ae1608dd48b-Abstract.html) · [arXiv 2007.13544](https://arxiv.org/pdf/2007.13544v1) `[Benchmark]`
9. [Simons Institute — ReBeL talk](https://simons.berkeley.edu/talks/rebel-combining-deep-reinforcement-learning-and-search-imperfect-information-games) `[Documented]`
