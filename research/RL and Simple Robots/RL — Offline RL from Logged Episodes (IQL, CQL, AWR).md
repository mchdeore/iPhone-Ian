---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, robotics, rl-and-simple-robots, offline-rl, iql, cql, awr]
---

# RL — Offline RL from Logged Episodes (IQL, CQL, AWR)

**TL;DR**
- Offline RL learns a better-than-demonstrator policy from **logs we already have**: Flask-app episodes and rig runs, successes *and* failures. No new rollouts needed.
- **IQL** is the default pick: it never evaluates unseen actions, it's fast, and it fine-tunes well online afterwards. That's exactly the DigiRL-style offline → online path.

**Builds on:** [[RL — Imitation Learning from Logged Taps (BC, ACT, LeRobot)]] (BC uses only good demos) and [[RL — Training GUI Agents with RL (DigiRL to MobileRL)]] (step 2 of the recipe).

## The core problem

Offline data only covers some actions. A naive Q-learner overrates actions it never saw (out-of-distribution, OOD), and the policy then chases those phantom values. The methods differ in how they block this:

| Method | Idea | Notes |
|---|---|---|
| **CQL** | Penalise Q-values of OOD actions directly | Conservative and robust; slower. One reimplementation took ~80 min per 1M updates vs ~20 min for IQL [1] |
| **IQL** (Kostrikov et al.) | Learn V(s) by **expectile regression** over dataset actions only; the Q backup is SARSA-style inside the data; extract the policy by **advantage-weighted behaviour cloning** | Never queries unseen actions; state of the art on D4RL when published; **strong online fine-tuning after offline initialisation** [2][3] |
| **AWR** | Weighted BC: imitate actions in proportion to exp(advantage) | The policy-extraction half of IQL; DigiRL's learner is a curriculum-filtered AWR [4] |
| **IDQL** | Keep the IQL critic, swap the Gaussian actor for a **diffusion** policy | Fixes IQL's single-mode actor when actions are multimodal [5] |

## Fit for our data

- **Action space:** (x, y, tap/swipe/type) on a screenshot. For a VLM policy, "advantage-weighted SFT" is easy to implement: weight each logged (screen, action) by exp(A/β) in the normal fine-tuning loss.
- **Reward:** only use episodes with trustworthy `reward_source` values ([[RL — Rewards and Success Detection from the Screen]]).
- **Failures are the point:** BC throws them away; offline RL learns *what not to do* from them. Log every episode, including the bad ones.
- **Multimodality:** a screen often has several valid next taps. If the AWR policy averages between targets (tapping halfway between two buttons), predict a *discrete* target element instead of raw coordinates, or move to an IDQL-style generative actor.

## Pitch in

- [ ] ML: implement advantage-weighted SFT on top of the BC baseline; the critic is a small value head on frozen VLM features.
- [ ] Report BC vs AWR vs IQL success on the same held-out tasks.

## Sources

1. [IQL quick review](https://liner.com/review/offline-reinforcement-learning-with-implicit-qlearning) `[Community]`
2. [Kostrikov et al. — Offline RL with Implicit Q-Learning (arXiv 2110.06169)](https://arxiv.org/abs/2110.06169v1) `[Benchmark]`
3. [Berkeley EECS-2023-62 thesis](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2023/EECS-2023-62.pdf) `[Benchmark]`
4. [DigiRL (arXiv 2406.11896)](https://arxiv.org/abs/2406.11896) `[Benchmark]`
5. [IDQL (arXiv 2304.10573)](https://arxiv.org/pdf/2304.10573) `[Benchmark]`
