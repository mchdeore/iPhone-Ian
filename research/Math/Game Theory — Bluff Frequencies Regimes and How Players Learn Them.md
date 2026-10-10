---
type: research
status: answered
author: marc
date: 2026-10-10
tags: [machine-learning, math, game-theory, poker, gto, bluffing, mdf, solvers, opponent-modeling]
---

# Game Theory — Bluff Frequencies, Regimes, and How Players Learn Them

**TL;DR**
- A **bluff rate** is not one number — it is a **regime**: a mix of actions at a specific **game-tree node** (board, pot, stack, line taken). Equilibrium ties bluff frequency to **bet size** via **indifference** (MDF on the defender; bluff:value ratio on the aggressor).
- People learn by: **theory → solver outputs → GTO trainers → HUD population stats → hand-history tagging**. Most of that is **offline study** (allowed). **Live solver lookup** is RTA (banned) — detection targets **solver-shaped frequencies**, not “knowing math.”
- **ML in the loop:** solvers use **CFR / regret minimization** (not classic supervised learning); exploitative tools and rooms use **supervised + clustering on hand histories**; anti-cheat uses **equilibrium-distance scoring** (e.g. GTO Wizard Fair Play).

**Builds on:** [[Game Theory — Foundations for Sports, Poker and Markets]], [[Game Theory — GTO vs Exploitative Play (Poker and Markets)]], [[Game Theory — Counterfactual Regret Minimization (CFR)]], [[Game Theory — Real-Time Poker Under Personal Compute and Time Banks]], [[Poker Platforms — RTA Bot and Solver Detection]].

---

## 1. What a “regime” means

| Term | Meaning |
|---|---|
| **Node** | One decision point: your cards (hidden), board, action history, pot, stacks |
| **Strategy at node** | Probabilities over {check, bet s1, bet s2, fold, call, raise…} |
| **Bluff rate (informal)** | Share of **weak hands** in your betting range that bet/raise — *conditional* on choosing the aggressive line |
| **MDF (defender)** | Minimum **call+raise** frequency so aggressor cannot profit bluffing any two cards: MDF ≈ pot / (pot + bet) ([[Game Theory — GTO vs Exploitative Play (Poker and Markets)]]) |
| **Bluff:value (aggressor, river)** | For a pot-sized bet, classic toy model: ~**1 bluff combo per 2 value combos** (size-dependent) so defender is indifferent with MDF 50% |

**Platform difference is not a different formula.** Stakes change **population mistakes** (microstakes over-folds → exploitative bluff *more*; tough pools → closer to GTO mixes). The **regime** is still defined by the tree; the **exploit** is locking opponent fold frequency ([[Game Theory — GTO vs Exploitative Play (Poker and Markets)]] node locking).

---

## 2. How people actually learn bluff rates

### Stage A — Closed-form intuition (no software)

- Learn MDF and pot-odds.
- River toy games: if you bet pot, defender needs ~50% continue; aggressor mixes so weak hands bluff often enough to make top pair indifferent.
- **Output:** ballpark (“need some bluffs on this runout”) — not exact frequencies.

### Stage B — Solver libraries (offline, hours of compute)

- Tools: **PioSolver, GTO+, Simple Postflop, MonkerSolver** (preflop).
- User picks: ranges, bet-size menu, stack depth → run **CFR** overnight.
- **Output:** exact **% at every node** — e.g. “with this sizing on this turn, bet 34% of range, 12% of that is bluffs.”
- This is how pros **memorize structures**, not single numbers.

### Stage C — GTO trainers (gamified drills)

- **GTO Wizard, Hand2Note Academy-style drills, etc.**
- Show a spot → you pick freq/size → app shows **GTO mix** and EV loss.
- **ML here:** mostly **lookup** against precomputed solutions; the *training product* may use ML for **clustering spots** and UI, but equilibrium numbers come from **CFR trees**.

### Stage D — Population stats on the platform (exploit layer)

- **HUD / tracker** (where allowed): fold-to-cbet, WTSD, fold-to-river-bet, aggression factor.
- Interpretation: if pool **over-folds** river → bluff regime shifts **up** (exploit); if pool **calls too much** → bluff **down**, value **up**.
- **Sample discipline:** ~200+ hands on a stat before trusting ([[Game Theory — GTO vs Exploitative Play (Poker and Markets)]]).
- **Platform note:** many apps **ban HUDs** on mobile; stats then come from **manual review** or site-provided summaries.

### Stage E — Hand-history review

- Tag river bluffs vs value bets in exported HH.
- Compare your **empirical** bluff rate in “spot type X” to solver or population.
- Slow, accurate for **your leaks**, not for live lookup.

**Legal/ToS line:** A–E **off-table** = study. Opening Pio **during** a session = **RTA** on most real-money sites → [[Poker Platforms — RTA Bot and Solver Detection]].

---

## 3. Machine learning — what is actually used

### 3.1 Computing GTO bluff rates (equilibrium engines)

| Method | Role | “ML”? |
|---|---|---|
| **CFR / CFR+ / MCCFR** | Iterate regret matching on game tree; average strategy → Nash (2p zero-sum) | **Game-theory RL**, not ImageNet-style ML → [[Game Theory — Counterfactual Regret Minimization (CFR)]] |
| **Depth-limited + subgame solve** | Live or batch refinement | Same family → [[Game Theory — Poker AI Milestones (Cepheus to Pluribus)]] |
| **Deep CFR / ReBeL** | Neural nets approximate regrets/values | **Deep RL** |
| **Abstraction learning** (research) | Learn card buckets from data | Supervised / clustering on hands |

**Takeaway:** the **bluff % you see in GTO Wizard** is almost always **CFR on an abstracted tree**, not a model trained to “predict bluffs” from pixels.

### 3.2 Exploitative / assistant tools (player-side)

| Method | Input | Output |
|---|---|---|
| **Player clustering** | HUD stats (VPIP, PFR, 3bet, fold-to-X) | Archetype → default exploit (e.g. bluff more vs “nit”) |
| **Bayesian range updating** | Action sequence + prior range | Fold/call estimates → **optimal bluff freq vs this villain** |
| **Supervised fold prediction** | Hand history features | P(fold \| bet size, board texture) — used in some RTA/HUD extensions |
| **LLM coaches (2024+)** | Hand text | Verbal advice — **not** equilibrium; quality varies |

These are **supervised ML on logs** or **heuristics**, layered on top of **solver baselines**.

### 3.3 Platform detection ML (operator-side)

Rooms do **not** detect “you studied MDF.” They score **whether your action mix matches a solver library** at scale:

| Feature class | Bluff-regime angle |
|---|---|
| **Action mix at node class** | River bluff:value ratio vs **stored GTO** for that sizing/board |
| **Sizing menu** | Bets at solver fractions → same bluff structure as Pio |
| **Cross-node consistency** | Turn bluff freq + river bluff freq jointly GTO while rest of profile is fishy |
| **Complexity vs time** | Instant “correct” mix on hard river nodes |
| **Multi-table correlation** | Same mix on 12 tables |

**GGPoker + GTO Wizard Fair Play:** explicit **equilibrium-distance** check on flagged accounts [1]. PokerStars cites **solver-like play at critical moments** [2].

**What is NOT detected:**

- Knowing population is **too sticky** and bluffing **more** than GTO (human exploit).
- Being **wrong** about bluff rate (bad play).
- Studying solvers **away from the table**.

**What IS detected (risk):**

- **Matching high-precision GTO mixes** + **solver sizings** + **inhuman timing** over thousands of hands.

---

## 4. “Regimes on certain platforms” — practical map

| Platform type | How bluff regimes are learned | ML you touch |
|---|---|---|
| **Desktop cash (tracker allowed)** | HUD population + solver study | Clustering nits/lags; CFR offline |
| **Mobile / tracker banned** | Memory + off-table GTO Wizard; simpler exploits (overfold pools) | Less live stats; same CFR study |
| **Play-money / vs CPU (our rig)** | OpenSpiel + blueprint → test bluff mixes in sim | CFR + optional policy net → [[Game Theory — Real-Time Poker Under Personal Compute and Time Banks]] |
| **Training sites (GTO Wizard free tier)** | Drills only | Precomputed CFR libraries |

**Stakes as regime:** deep stacks vs push/fold change the **tree** entirely — different bluff rates because **different nodes**, not because the site changes math.

---

## 5. Research connections for our team

1. **Implement Leduc poker in OpenSpiel** — print equilibrium bluff freq at one node; see it change when bet size changes.
2. **Node-lock exploit experiment** — lock villain over-fold in sim; measure bluff rate shift (exploit vs GTO).
3. **Do not conflate** rig automation with “hidden bluff learning” — operators catch **EV and frequencies**, not the gantry ([[Betting Apps — Physical-Agent Red Team and Detection Hardening]]).
4. **Legitimate ML project:** train **population fold predictor** on **public hand-history datasets** (research licenses) to quantify how much exploitative bluffing beats GTO vs **typical** online pool — parallel to tennis fade exploit ([[Game Theory — GTO vs Exploitative Play (Poker and Markets)]] mapping table).

---

## Sources

1. [PokerNews — GGPoker and GTO Wizard Fair Play](https://www.pokernews.com/news/2025/03/ggpoker-and-gto-wizard-team-up-to-keep-poker-fair-48110.htm) `[Documented]`
2. [PokerNews — PokerStars vs RTA](https://www.pokernews.com/news/2023/10/pokerstars-battle-against-real-time-assistance-44628.htm) `[Documented]`
3. [Zinkevich et al. — CFR (NeurIPS 2007)](https://proceedings.neurips.cc/paper/2007/hash/08d98638c6fcd194a4b1e6992063e944-Abstract.html) `[Benchmark]`
4. [Brown & Sandholm — Superhuman multiplayer poker (Science 2019)](https://science.org/doi/10.1126/science.aay2400) `[Benchmark]`

## Related

- **Summary:** [[State of — Math]] · [[State of — Machine Learning]] · [[State of — Cybersecurity]]
