---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, cybersecurity, robotics, rl-and-simple-robots, real-world-rl, hil-serl, sac, safety, throughput, resets]
---

# RL — Real-World Training Loop on the Gantry (Resets, Safety, HIL-SERL)

**TL;DR**
- The phone rig has a rare advantage for real-world RL: **resets are nearly free** (go Home, relaunch the app).
- Its weakness is throughput, roughly 1–2k steps per hour per phone.
- HIL-SERL shows real robots learning simple skills in **1–2.5 hours** from demos plus human corrections, which fits that budget.
- Use the rig for **short skills and fine-tuning**, never for from-scratch agent RL.

**Builds on:** [[RL — Where RL Helps a Gantry Robot (and Where It Doesn't)]] and [[iOS Control — Relative Cursor Calibration and Visual Servoing]] (tap timing).

## Throughput math

- Per step: gantry traverse + Z dwell (~0.5–2 s, from the cursor-calibration note) + screen settle (~0.3–1 s) + capture and inference (~0.2–0.5 s) ≈ **1.5–3.5 s**.
- That gives **~1,000–2,400 steps/hour/phone**. Hardware v2 holds 2 phones, so ×2.
- Compare: DigiRL ran **64 emulators** in parallel. One rig-hour is about a minute of emulator farm time. That's why emulator-first matters ([[RL — Emulator-First Training and Sim-to-Real for the Rig]]).

## HIL-SERL: the real-world RL template

- **Recipe:** 10–20 human demos → train a binary **reward classifier** (success yes/no from images) → distributed **SAC** actor-learner → a human can step in at any time to correct.
- **Results:** near-perfect success on manipulation tasks in 1–2.5 h. On average 2× success and 1.8× faster cycle time vs imitation baselines. `[Benchmark]`
- **Integrated into LeRobot**, so the same tooling runs on the SO-101 arm and could drive the gantry's (x, y, tap) action space. `[Community]`
- For the phone, the "intervention" is a human tapping the correct target in the Flask app UI. That interface already exists.

## Resets (our advantage)

- Scripted reset macro: Home → (optional) swipe the app away → relaunch → wait for a known screen (template match).
- Detect a **reset failure** (e.g. a notification banner covers the screen) and retry. Count reset success as a health metric.
- Turn off auto-lock, notifications and Focus interruptions on the test phone. Use a dedicated test Apple ID.

## Safety envelope (non-negotiable)

- **Mechanical:** FluidNC soft limits sized to the screen rectangle plus a margin; the spring-loaded stylus caps force; an e-stop is reachable.
- **Software:** the action space is clipped to the screen bounds; no "type" action outside allowlisted fields.
- **Account:** **no real credentials, payments or messaging apps** on training phones. The app allowlist is shared with [[RL — Rewards and Success Detection from the Screen]].
- **Watchdog:** stop if there's no reward progress for N steps, or if an unknown screen persists (the agent has wandered).

## Pitch in

- [ ] Robotics: write the reset macro and soft limits; measure step time over 100 steps.
- [ ] ML: get LeRobot HIL-SERL running on a toy rig task, e.g. "tap the moving target in the flash app until 95% hit rate".

## Sources

- [HIL-SERL (arXiv 2410.21845)](https://arxiv.org/html/2410.21845v2) `[Benchmark]` · [LeRobot HIL-SERL docs](https://www.mintlify.com/huggingface/lerobot/policies/hilserl) `[Community]`
- [DigiRL — 64 parallel emulators](https://arxiv.org/abs/2406.11896) `[Benchmark]`
