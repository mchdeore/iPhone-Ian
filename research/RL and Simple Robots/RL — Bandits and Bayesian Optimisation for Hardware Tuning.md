---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, robotics, rl-and-simple-robots, bandits, bayesian-optimization, thompson-sampling, tuning]
---

# RL — Bandits and Bayesian Optimisation for Hardware Tuning

**TL;DR**
- For the rig's physical knobs (tap dwell, Z depth, approach speed, servo gains), **Bayesian optimisation (BO)** finds good settings in **tens of trials**, where deep RL would need thousands and wear out hardware.
- A real-robot controller study improved performance within **32 trials**.
- Use Thompson sampling when trials can run in parallel (2 phones = 2 workers).

**Builds on:** [[RL — Where RL Helps a Gantry Robot (and Where It Doesn't)]] (layers 2 and 3) and [[Touch Telemetry — Measuring What the Rig Emits]] (the reward signal).

## Why not RL here

- "Data-hungry methods such as standard RL need many experimental samples, which is prohibitive in robotics because hardware can deteriorate and break" [1].
- Our knobs are **static parameters with an immediate score**. That's black-box optimisation, not sequential control.

## The toolkit

| Situation | Method | Notes |
|---|---|---|
| A few discrete settings (e.g. 3 dwell × 3 depth) | **Thompson-sampling bandit** (Beta posterior per arm) | ~100 taps total; trivial to code |
| 2–6 continuous knobs, noisy score | **GP-based BO** (e.g. BoTorch, Optuna) | A path-following controller improved within 32 trials, 15 of them warm-start [2] |
| Parallel workers (2 phones) | **Asynchronous parallel Thompson sampling** | n evaluations over M workers ≈ n sequential; the async version beats sync under a time budget [3] |
| No clean metric ("feels right") | **Preferential BO** (pairwise comparisons) | Useful for swipe smoothness; handles crashes poorly by default [4] |

## Objective design for tap tuning

- **Score** = P(tap registered) − λ·(cycle time) − μ·(landing error mm), measured over k taps per trial.
- **Constraints:** registration ≥ 99%, force within the stylus spring's range. Treat violations as infeasible rather than penalties.
- **Noise:** use k ≥ 20 taps per evaluation; a GP models the remaining noise.
- **Warm start** from Aria's design values so the first trials are already safe.

## Pitch in

- [ ] Robotics: expose the knobs as host-side parameters; write `evaluate(params) -> score` that runs k taps on the flash app's target grid.
- [ ] ML: wrap it in Optuna or BoTorch with 2 async workers; post the convergence plot.

## Sources

1. [Bayesian Optimisation in Robot Learning — Tübingen PhD thesis](https://ics.is.mpg.de/publications/bayesian) `[Benchmark]`
2. [BO tuning of a Lyapunov path-following controller (arXiv 2512.12649)](https://arxiv.org/abs/2512.12649v1) `[Benchmark]`
3. [Asynchronous Parallel BO via Thompson Sampling — CMU RI](https://www.ri.cmu.edu/publications/asynchronous-parallel-bayesian-optimisation-via-thompson-sampling) `[Benchmark]`
4. [Preferential BO with crash feedback (arXiv 2604.01776)](https://arxiv.org/pdf/2604.01776) `[Benchmark]`
