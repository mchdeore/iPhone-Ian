---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, robotics, rl-and-simple-robots, reinforcement-learning, bandits, bayesian-optimization, control, gantry]
---

# RL — Where RL Helps a Gantry Robot (and Where It Doesn't)

**TL;DR**
- Split the rig into four layers. Only the top one, the **agent policy** (what to tap next, across many steps), is a real RL problem, and that's where the published wins are.
- The motion and targeting layers are solved by classical control. Tuning their few parameters is a job for **bandits / Bayesian optimisation**, not deep RL.
- This refines the "one-step bandit at most" verdict in [[YOLO — Flask Closed-Loop Trainer App]]: true for the flash app, false for multi-step tasks.

**Useful for:** Robotics (what not to over-engineer), ML (where to spend GPU time).

## The four layers

| Layer | Decision | Best tool | Why not deep RL |
|---|---|---|---|
| **1. Motion** | Accel/jerk limits, microstepping, current | Trapezoid/S-curve profiles + resonance tuning (input shaping, e.g. Klipper's measured-frequency method) | Open-loop steppers **can't sense a lost step**. With no encoder, an RL agent would be learning from a signal that doesn't show the error. `[Documented]` |
| **2. Tap** | Z dwell time, press depth, stylus approach speed | **Contextual bandit** or Bayesian optimisation over 2–3 params; reward = tap registered (from [[Touch Telemetry — Measuring What the Rig Emits]]) | One-step decision with an immediate reward: textbook bandit, ~100 trials. |
| **3. Targeting** | Pixel → mm mapping, visual-servo gains | Homography + PID/visual servoing ([[iOS Control — Relative Cursor Calibration and Visual Servoing]]); tune gains with BO | A well-posed control problem with known structure. RL would rediscover the homography slowly. |
| **4. Agent policy** | Which element, in what order, recovering from errors | **RL on a VLM policy** after SFT ([[RL — Training GUI Agents with RL (DigiRL to MobileRL)]]) | This is where RL wins: DigiRL went from 17.7% to 67.2% over SFT alone on Android tasks. `[Benchmark]` |

## Rules of thumb

- **Is there a model?** Use it. Kinematics, homography and timing all have physics; RL is for when the dynamics are unknown or the horizon is long.
- **Is the reward immediate?** Then it's a bandit (Thompson sampling or UCB), not RL. Credit assignment over many steps is the only reason to pay RL's sample cost.
- **Count the actions per hour.** The physical rig manages ~1–2k steps/hour per phone (see [[RL — Real-World Training Loop on the Gantry (Resets, Safety, HIL-SERL)]]). Any method that needs millions of steps has to run in an emulator.
- **Optimise the expensive thing.** Layer 4 failures (wrong element, stuck in a menu) cost minutes; layer 2 failures (missed tap) cost a retry.

## What to build first

1. **Bandit for tap params** (dwell × depth × approach speed). This is a weekend job, and it gives the group its first "learning on hardware" result.
2. **BO for servo gains**, if visual servoing is used. Target: fewest corrections per tap.
3. **Agent RL in an emulator**, transferred to the rig. See [[RL — Emulator-First Training and Sim-to-Real for the Rig]].

## Pitch in

- [ ] Robotics: expose dwell, depth and approach speed as tunable params in the tap command (FluidNC macro or host-side).
- [ ] ML: write the bandit loop (Thompson sampling over a small grid). The reward comes from the telemetry logger.

## Sources

- [Klipper — Resonance Compensation](https://www.klipper3d.org/Resonance_Compensation.html) `[Documented]` · [Machine Design — avoiding step loss](https://www.machinedesign.com/archive/avoiding-step-loss) `[Documented]`
- [DigiRL (arXiv 2406.11896)](https://arxiv.org/abs/2406.11896) `[Benchmark]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]]
