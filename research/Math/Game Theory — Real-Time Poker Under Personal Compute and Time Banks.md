---
type: research
status: answered
author: marc
date: 2026-10-10
tags: [machine-learning, math, game-theory, poker, cfr, real-time, subgame-solving, abstraction, open-spiel]
---

# Game Theory — Real-Time Poker Under Personal Compute and Time Banks

**TL;DR**
- Full no-limit hold'em equilibrium on a laptop **in every spot** is impossible. Winning pattern from superhuman AI: **offline blueprint** + **small subgame solve only where it matters**, under a **hard millisecond budget**.
- On a **personal machine** (one GPU / 8–16 CPU cores), treat decisions as **anytime algorithms**: return the best action seen so far when the timer fires.
- **Scope:** play-money tables, **vs-the-computer** apps, OpenSpiel simulators, and our **gantry rig** test games — not advice for beating real-money multiplayer ([[System Design — Related Work - Robots and Bots that Play Games]]). Operators ban RTA/solvers on money tables; detection is in [[Poker Platforms — RTA Bot and Solver Detection]].

**Builds on:** [[Game Theory — Counterfactual Regret Minimization (CFR)]], [[Game Theory — Poker AI Milestones (Cepheus to Pluribus)]], [[Game Theory — GTO vs Exploitative Play (Poker and Markets)]], [[System Design — Game State and Decision Engines for Card Games]].

---

## 1. What “limited time” actually means

| Context | Typical budget | What fits |
|---|---|---|
| Online cash / MTT (human UI) | **~7–15 s** pre-action clock; **time bank** ~30–90 s per session/hand (site-dependent) | Shallow search + lookup; not full-tree CFR |
| Play-money / vs CPU (our rig) | **2–5 s** per move if gantry-bound ([[System Design — Card-Playing Gantry Rig Architecture]]) | Overlap **solver with robot motion** |
| Offline study | Hours | Blueprint training, abstraction tuning |
| OpenSpiel Kuhn/Leduc | Unlimited | CFR correctness checks ([[Game Theory — Counterfactual Regret Minimization (CFR)]]) |

**Rule:** define `deadline_ms` before coding. Every solver must support **interrupt and return best-so-far**.

---

## 2. Why brute-force CFR on NLHE fails locally

- Abstracted heads-up no-limit hold'em still has **billions+** information sets. Vanilla CFR needs many iterations × large tree.
- Cepheus: **4,800 CPUs × 68 days** for **limit** hold'em [1]. Pluribus: **12,400 core-hours** for 6-max with heavy abstraction [2].
- Commercial solvers (Pio, GTO+, etc.) precompute **hours overnight** for one spot tree — that is the realistic **personal-machine** workload: **batch offline, query online**.

---

## 3. The workable stack (blueprint + bounded search)

Same pattern as Libratus / Pluribus / depth-limited solving [3][4]:

```
OFFLINE (night job, personal PC)
  ├── Abstraction: card buckets, bet-size menu (e.g. 33/75/125% pot)
  ├── MCCFR / CFR+ → blueprint strategy file (compressed)
  └── Optional: small value net (ReBeL-style) for leaf evaluation

ONLINE (each decision, ≤ deadline_ms)
  ├── Parse hand → abstract state + opponent range estimate
  ├── If river or near-terminal → endgame solve (exact-ish on small tree)
  ├── Else if time remains → depth-limited subgame solve from current node
  └── Else → sample action from blueprint (or argmax if exploit mode)
```

### 3.1 Abstraction (do this first)

- **Card bucketing:** EHS, hand strength, board texture → 10–200 buckets per street (not 1,326 combos live).
- **Action abstraction:** 2–4 bet sizes + check/call/fold. More sizes = bigger tree = slower.
- **Tradeoff:** coarse abstraction → fast but **exploitability** in weird sizes; fine abstraction → slow.

### 3.2 Where to spend live compute

| Street / spot | Personal-machine priority |
|---|---|
| **Preflop** | **Zero live solve.** Preflop charts / push-fold tables (ICM for MTT). O(1) lookup. |
| **Flop** | Blueprint only unless heads-up and shallow stacks |
| **Turn** | Subgame solve if `deadline_ms > 2000` and pot large |
| **River** | **Best ROI for live solve** — ranges narrowed, tree smallest |
| **Short-stack / jam nodes** | Precomputed Nash push/fold (≤20 BB) |

### 3.3 Anytime algorithms

- **Depth-limited solving:** expand tree to depth d, evaluate leaves with blueprint or net [3].
- **Iterative deepening:** each CFR iteration improves; stop at deadline.
- **Monte Carlo CFR online:** sample trajectories until timer — high variance but bounded time.

### 3.4 Exploitation under budget ([[Game Theory — GTO vs Exploitative Play (Poker and Markets)]])

- **Default:** blueprint ≈ GTO-ish baseline.
- **Exploit:** only when stat evidence exists (~200+ hands on tendency [5]) → **node lock** opponent freq in a *small* re-solve. Re-solve is smaller tree → fits laptop **if** locked nodes are few.
- **Risk:** wrong lock → worse than blueprint. Fall back to blueprint when sample thin.

---

## 4. ML on a personal GPU (optional layer)

| Approach | Train cost | Inference | Role |
|---|---|---|---|
| **Deep CFR / single net policy** | High; needs self-play data | **<50 ms** | Action picker when no time to search |
| **Value net on leaves** | Medium | **<10 ms** per leaf | Replaces blueprint eval in subgame solve |
| **Behavior clone human/solver** | Low if logs exist | **<5 ms** | Baseline for rig; not equilibrium |
| **Leduc/Kuhn in OpenSpiel** | Minutes | Trivial | Unit tests for CFR code |

**Practical order:** (1) CFR on Leduc in OpenSpiel, (2) blueprint + river solve, (3) net only if still missing deadline.

ReBeL shows RL + search can work with **less domain hand-crafting** [6] — but training is still **not** “install and play”; it is a research pipeline.

---

## 5. Latency budget for **our** phone + gantry loop

From [[System Design — Card-Playing Gantry Rig Architecture]]:

| Stage | Typical ms |
|---|---|
| Capture + perceive cards | 70–250 |
| Build `GameState` | 1–10 |
| **Decide (this note)** | **100–3000** (target) |
| Plan + act (gantry) | 1000–3000 |
| Verify | 50–150 |

**Overlap:** start deciding **move N+1** while gantry executes move N. Effective think time can be **gantry-limited**, not CPU-limited, for turn-based apps.

**Implication:** vs-computer poker on the rig should use **preflop chart + blueprint sample** almost always; reserve subgame solve for river in big pots only.

---

## 6. Implementation checklist (repo-friendly)

1. **OpenSpiel** Leduc poker: CFR+ until exploitability < 0.05 bb/hand; log time vs iterations.
2. **Abstract NLHE toy** (3 bet sizes, 5 buckets): offline MCCFR → `.bin` blueprint.
3. **Online wrapper:** `choose_action(state, deadline_ms)` → anytime CFR or lookup.
4. **Metrics:** exploitability (offline), **decision latency p95**, EV vs baseline bot (online sim).
5. Wire into [[System Design — Game State and Decision Engines for Card Games]] `legal_moves()` → `Move`.

---

## 7. What this does *not* solve

- **6-max multiplayer:** no Nash guarantee; blueprint from self-play is heuristic ([[Game Theory — Poker AI Milestones (Cepheus to Pluribus)]]).
- **Real-money site terms:** using this **during** live money play is RTA/bot territory → bans ([[Poker Platforms — RTA Bot and Solver Detection]]).
- **Opponent modeling latency:** good range updates need hand history; our rig may not have HUD — keep opponent as **population blueprint** unless logging many hands.

---

## Sources

1. [Bowling et al. — Heads-up limit hold'em is solved (Science 2015)](https://webdocs.cs.ualberta.ca/~bowling/publications/b2hd-15science.html) `[Benchmark]`
2. [Brown & Sandholm — Superhuman AI for multiplayer poker (Science 2019)](https://science.org/doi/10.1126/science.aay2400) · [Pluribus compute discussion](https://www.theregister.com/2019/07/12/pluribus_ai_poker_human_pros) `[Benchmark]`
3. [Brown, Sandholm & Amos — Depth-Limited Solving (arXiv 1805.08195)](https://arxiv.org/pdf/1805.08195) `[Benchmark]`
4. [Moravčík et al. — DeepStack (Science 2017)](https://science.org/doi/10.1126/science.aam6968) `[Benchmark]`
5. [GTO vs exploitative sample discipline (community coaching norm)](https://www.deucescracked.com/blog/gto-vs-exploitative-small-stakes-online-poker-2026) `[Community]`
6. [Brown et al. — ReBeL (NeurIPS 2020)](https://arxiv.org/pdf/2007.13544) `[Benchmark]`
7. [OpenSpiel](https://github.com/google-deepmind/open_spiel) — Leduc/CFR reference implementations `[Documented]`

## Related

- **Summary:** [[State of — Math]] · [[State of — Machine Learning]] · [[State of — System Design]]
