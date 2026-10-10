---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [system-design, machine-learning, math, card-games, solitaire, ismcts, search]
---

# System Design — Game State and Decision Engines for Card Games

**TL;DR**
- The "brain" depends on what the game hides:
  - **Perfect information, single player** (e.g. FreeCell; thoughtful Klondike) → exhaustive or heuristic **search**.
  - **Hidden cards** (real Klondike, Hearts, rummy against the computer) → **determinization / ISMCTS**.
  - **Adversarial betting** (poker against the computer) → **CFR-style equilibrium**.
- Even the brain can only do so well: **~82% of Klondike deals are winnable** with full information (Blake & Gent), and a human-level player wins far fewer. Measure the robot against that ceiling, not against 100%.

**Builds on:** [[Game Theory — Counterfactual Regret Minimization (CFR)]], [[Game Theory — Foundations for Sports, Poker and Markets]], [[System Design — Card-Playing Gantry Rig Architecture]].

## State tracking comes first

- A typed `GameState` (piles, face-down counts, stock and waste, score), plus a **rules engine** giving `legal_moves(state)` and `apply(state, move)`.
- **Belief state:** for hidden cards, keep the set of cards *not yet seen*. Each flip removes one. This is what determinization samples from.
- **Consistency check:** after every move, the predicted state must equal the perceived state, or stop and re-observe ([[System Design — Reliability, Error Recovery and Testing Harness]]).

## Engines by game type

| Game type | Engine | Evidence |
|---|---|---|
| Klondike, full information ("thoughtful") | Depth-first search with pruning (Solvitaire) | **81.945% ± 0.084%** of deals winnable; the same solver covers 73 variants of 35 patience games [1][2] |
| Klondike, normal (hidden cards) | **Rollouts / determinized search** | Yan et al.'s iterated-rollout strategy wins ~2× as many games as an expert human (on the thoughtful variant) [3] |
| Hidden-information games vs computer opponents (Hearts, Spades, rummy) | **ISMCTS:** search over *information sets*, not sampled states | Fixes determinization's strategy fusion and wasted budget [4][5] |
| Poker vs computer (play money) | CFR / pre-solved strategy | [[Game Theory — Poker AI Milestones (Cepheus to Pluribus)]], [[Game Theory — Real-Time Poker Under Personal Compute and Time Banks]] |
| Anything, quick start | Greedy heuristics (e.g. Klondike: play to foundation, reveal face-down cards first) | Baseline to beat |

**Libraries:** OpenSpiel (DeepMind) implements many card games and algorithms (CFR, MCTS, ISMCTS-style). Prototype the brain in OpenSpiel against a simulator before connecting it to the robot. (Repo: github.com/google-deepmind/open_spiel.)

## Why this split matters for the rig

- Most solver time comes from search, and it runs while the gantry is moving. Overlap them: plan move N+1 during the drag for move N.
- The solver should output **moves**; turning them into **gestures** is a separate layer ([[System Design — Drag, Tap and Verify Primitives for Card Moves]]).
- Win rate depends on both brain quality and **execution reliability**. Log both, so a loss can be attributed to a bad decision or a bad drag.

## Pitch in

- [ ] Math/ML: wrap a Klondike rules engine; compare greedy vs rollout vs ISMCTS win rates over 1,000 simulated deals.
- [ ] Measure robot-executed vs simulator win rate for the same policy. The gap is execution loss.

## Sources

1. [Blake & Gent — The Winnability of Klondike Solitaire and Many Other Patience Games (JAIR)](https://jair.org/index.php/jair/article/view/17167) `[Benchmark]`
2. [arXiv 1906.12314 (v5)](https://arxiv.org/html/1906.12314v5) · [St Andrews seminar](https://blogs.cs.st-andrews.ac.uk/csblog/?p=9350) `[Benchmark]`
3. [Yan, Diaconis, Rusmevichientong & Van Roy — Solitaire: Man Versus Machine](https://mlanthology.org/neurips/2004/yan2004neurips-solitaire) `[Benchmark]`
4. [Cowling, Powley & Whitehouse — Information Set MCTS](https://eprints.whiterose.ac.uk/75048) `[Benchmark]`
5. [Cowling, Ward & Powley — determinization in Magic: The Gathering](https://eprints.whiterose.ac.uk/75050) · [Whitehouse PhD thesis](https://etheses.whiterose.ac.uk/id/eprint/8117/) `[Benchmark]`
6. [MCTS review (arXiv 2103.04931)](https://arxiv.org/pdf/2103.04931) `[Benchmark]`

## Related

- **Summary:** [[State of — System Design]] · [[State of — Machine Learning]] · [[State of — Math]]
- **See also:** [[System Design — Reading Cards from the Screen]] · [[Game Theory — GTO vs Exploitative Play (Poker and Markets)]]
