---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, robotics, rl-and-simple-robots, sim-to-real, domain-randomization, emulator, mujoco, isaac-lab, genesis]
---

# RL — Emulator-First Training and Sim-to-Real for the Rig

**TL;DR**
- Our "simulator" isn't a physics engine. It's **phone emulators plus a camera-and-actuator corruption model**.
- There are two gaps to close: the **visual gap** (clean screenshot vs camera photo) and the **action gap** (perfect tap vs a real gantry tap with offset, latency and misses).
- Randomise both in the emulator, calibrated from our own telemetry, so the policy arrives at the rig already robust.
- Physics simulators (MuJoCo/Isaac/Genesis) matter only for the group's *other* simple robots.

**Builds on:** [[YOLO — Synthetic Data and Flash Training App]] (homography rendering), [[Touch Telemetry — Measuring What the Rig Emits]] (noise parameters), [[RL — Training GUI Agents with RL (DigiRL to MobileRL)]].

## Gap 1: visual (screenshot → camera)

Pass every emulator frame through a randomised **camera model** before the policy sees it:
- perspective warp (homography jitter ± a few degrees), lens blur, exposure/white-balance shifts
- glare and specular highlights, moiré, compression noise
- occasional occlusion by the stylus or toolhead sitting over the screen

Fit the ranges from real rig captures; don't guess. Widen until rig accuracy stops improving. This is classic domain randomisation applied to GUI frames. Note that if the screen-capture path (no camera) is chosen in Aria's hardware v2, this gap mostly disappears. `[Community]`

## Gap 2: action (perfect tap → gantry tap)

Wrap the emulator's tap API with:
- **landing offset** ~ N(0, σ), with σ taken from the telemetry landing scatter
- **miss probability** p_miss (no touch registered)
- **latency**: the action lands 0.5–2 s later (gantry traverse + Z dwell) while the screen may still be animating
- **settle requirement**: the policy must wait for a stable frame (add a "wait" action)

A policy that has met these in simulation learns to verify after tapping instead of assuming success.

## When you *do* need a physics simulator (other robots in the group)

| Sim | Strength | Caveat |
|---|---|---|
| **MuJoCo / MJX** | Accurate contact, the standard for manipulation. MJX runs batched on GPU | MJX lacks some MuJoCo features (tendons, some mesh collisions) `[Community]` |
| **Isaac Lab** | Massive parallel RL (~150k steps/s for 4096 envs on a 4090, per one guide); good sensor rendering | Heavy; single-env overhead `[Community]` |
| **Genesis** | Fast batched claims | Independent tests found the benchmarks inflated and 3–10× slower on collision-heavy scenes `[Community]` |

For a CoreXY gantry the dynamics are near-static at our speeds. **Don't build a MuJoCo twin of the gantry** unless you're studying vibration.

## Pitch in

- [ ] ML: implement `CameraCorruption` and `ActuatorNoise` wrappers around the emulator environment (code in repo).
- [ ] Robotics: after the first rig captures, fit the homography-jitter and blur ranges and post them here.

## Sources

- [MuJoCo vs Isaac Sim (2026)](https://roboticscenter.ai/rl-environments/mujoco-vs-isaac-sim) · [Isaac Sim vs MuJoCo (TowardsAI)](https://pub.towardsai.net/isaac-sim-vs-mujoco-the-4-000-question-that-will-define-robotics-in-2025-4c41a2984c2c) · [Genesis speed critique](https://stoneztao.substack.com/p/the-new-hyped-genesis-simulator-is) `[Community]`
- [DigiRL — parallel emulators](https://arxiv.org/abs/2406.11896) `[Benchmark]`
