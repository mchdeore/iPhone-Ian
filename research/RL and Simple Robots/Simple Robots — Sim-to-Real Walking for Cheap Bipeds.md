---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, robotics, rl-and-simple-robots, sim-to-real, locomotion, ppo, mujoco, open-duck-mini, microduck]
---

# Simple Robots — Sim-to-Real Walking for Cheap Bipeds

**TL;DR**
- The duck-style bipeds (Open Duck Mini, Microduck) are the cheapest **end-to-end deep-RL sim-to-real** projects you can copy.
- The pipeline: PPO across thousands of parallel MuJoCo/Isaac environments, **actuator modelling plus backlash plus domain randomisation**, export to ONNX, run onboard at ~50 Hz.
- It teaches the exact skills the phone rig *doesn't* need, which makes it the right side project for the robotics members who want real RL.

**Builds on:** [[Simple Robots — Cheap Platforms to Practise RL On]] and [[RL — Emulator-First Training and Sim-to-Real for the Rig]].

## Open Duck Mini

- Community open-source biped, BOM under ~$400. The original walking policy was **trained in Isaac Gym**, with **sim-to-sim checks in MuJoCo** before hardware; the author reports sim-to-real walking "starting to work" [1].
- Vendor kits ship URDF and MJCF models and claim compatibility with the "Open Duck Playground" (marketing claim) [2].

## Microduck pipeline (the most detailed write-up)

- **One neural policy shared across thousands of parallel MuJoCo simulations**, trained with **PPO** [3].
- **Actuator modelling + backlash + domain randomisation** prepare it for imperfect hardware [3].
- The policy is **exported to ONNX and evaluated onboard at 50 Hz** [3].
- Training runs on mjlab's MuJoCo Warp path [3].

## MuJoCo Playground

- MJX (JAX MuJoCo) on GPU; "train policies on a single GPU after a simple pip install"; built to simplify sim-to-real [4].

## The sim-to-real checklist (applies to any cheap robot)

1. **System identification** of the servos: measure torque/speed curves, deadband and backlash on the bench, and put them in the actuator model.
2. **Randomise** mass, friction, motor strength (±20%), latency (0–40 ms) and sensor noise. Widen until the real robot stops falling.
3. **Sim-to-sim first**: a policy from Isaac/MJX must also walk in plain MuJoCo C before touching hardware [1].
4. **Low control rate** (50 Hz) with action filtering. Cheap servos can't follow a 500 Hz jittery policy.
5. **Safety:** harness or tether for the first runs; torque limits in firmware.

## Pitch in

- [ ] Robotics: print an Open Duck Mini and log servo system-ID data.
- [ ] ML: reproduce the Playground walking policy on our RTX 3060 and report wall-clock to a stable gait.

## Sources

1. [Open Duck Mini (mirror)](https://gitee.com/MatLzg/Open_Duck_Mini) `[Community]`
2. [Open Duck Mini v2 kit (Tindie)](https://www.tindie.com/products/wsk/open-duck-mini-v2-raspberry-pi-4b-8gb/) `[Community]` (vendor)
3. [How Microduck learns to walk — MuJoCo, PPO and sim-to-real](https://openelab.io/blogs/learn/how-microduck-learns-to-walk-mujoco-ppo-sim-to-real) `[Community]`
4. [MuJoCo Playground (arXiv 2502.08844)](https://www.arxiv.org/pdf/2502.08844) `[Benchmark]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]]
