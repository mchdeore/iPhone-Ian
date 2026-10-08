---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, rl-and-simple-robots, math, game-theory, cfr, regret-minimization, poker, self-play]
---

# Game Theory — Counterfactual Regret Minimization (CFR)

**TL;DR**
- **CFR** (Zinkevich et al., NeurIPS 2007) computes Nash equilibria in **imperfect-information** games by self-play: at every information set, track how much you *regret* not taking each action, and play actions in proportion to positive regret.
- The **average** strategy converges to equilibrium.
- **CFR+** (2015) converges much faster in practice and **essentially solved heads-up limit hold'em** (Cepheus).
- It's the algorithmic core of poker AI, and a close cousin of RL.

**Builds on:** [[Game Theory — Foundations for Sports, Poker and Markets]]; leads to [[Game Theory — Poker AI Milestones (Cepheus to Pluribus)]].

## The algorithm in plain terms

1. **Information set:** everything a player knows at a decision (own cards, betting history), not the hidden state.
2. **Counterfactual value** of action a at information set I: the expected payoff if you *had* steered play to I and then taken a, weighted by the opponents' (and chance's) probability of reaching I.
3. **Regret** = counterfactual value of a − value of your current mixed strategy. Accumulate it over iterations.
4. **Regret matching:** the next strategy plays a ∝ max(cumulative regret(a), 0).
5. Repeat via self-play. The **average strategy** over iterations converges to a Nash equilibrium in two-player zero-sum games.

Key result: minimising counterfactual regret at every information set minimises overall regret, so self-play converges to equilibrium. The 2007 paper scaled to limit hold'em abstractions with **10¹² states**, two orders of magnitude beyond earlier methods [1][2].

## Variants

| Variant | Change | Effect |
|---|---|---|
| **CFR+** | Regret-matching+ (cumulative regrets clipped at 0) + linear averaging (weight iteration t by t) | Empirically ~O(1/T) vs O(1/√T); soundness proved [3] |
| **Monte Carlo CFR (MCCFR)** | Sample parts of the tree per iteration instead of traversing all of it | Much cheaper iterations for huge games (Lanctot et al. 2009; background, verify) |
| **Deep CFR / ReBeL-style** | Neural networks approximate regrets and values | Scales without hand-made abstraction ([[Game Theory — Poker AI Milestones (Cepheus to Pluribus)]]) |

## Connection to RL and our other work

- CFR is **learning from counterfactual regret**; policy-gradient RL is learning from reward. Both are self-play improvement loops ([[RL — Training GUI Agents with RL (DigiRL to MobileRL)]]).
- **Regret matching** is also an online-learning algorithm for repeated decisions under adversarial conditions, e.g. choosing quote spreads against unknown traders ([[Markets — Market Making in Binary Contracts (Avellaneda-Stoikov)]]).
- **Exercise:** implement CFR for **Kuhn poker** (3 cards, ~12 information sets) in ~100 lines of Python. The known equilibrium value (−1/18 for player 1) is a correctness check.

## Pitch in

- [ ] ML/Math: implement vanilla CFR and CFR+ on Kuhn and Leduc poker; plot exploitability vs iterations for both (code in repo).

## Sources

1. [Zinkevich et al. — Regret Minimization in Games with Incomplete Information (NeurIPS 2007)](https://proceedings.neurips.cc/paper/2007/hash/08d98638c6fcd194a4b1e6992063e944-Abstract.html) · [PDF](https://proceedings.nips.cc/paper_files/paper/2007/file/08d98638c6fcd194a4b1e6992063e944-Paper.pdf) `[Benchmark]`
2. [U Alberta tech report TR07-14](https://era.library.ualberta.ca/files/vh53wx015/TR07-14.pdf) `[Benchmark]`
3. [Tammelin et al. — Solving HULHE with CFR+ (IJCAI 2015)](https://www.cs.ualberta.ca/~games/poker/publications/2015-ijcai-cfrplus.pdf) `[Benchmark]`
4. [Bowling et al. — Heads-up limit hold'em poker is solved (Science 2015)](https://webdocs.cs.ualberta.ca/~bowling/publications/b2hd-15science.html) `[Benchmark]`
5. [A Survey of RL for Economics (arXiv 2603.08956)](https://arxiv.org/pdf/2603.08956) `[Benchmark]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — RL and Simple Robots]] · [[State of — Math]]
