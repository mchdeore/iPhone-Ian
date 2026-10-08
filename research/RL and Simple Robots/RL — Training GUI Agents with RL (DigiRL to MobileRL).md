---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, robotics, rl-and-simple-robots, reinforcement-learning, gui-agent, vlm, grpo, ppo, androidworld]
---

# RL — Training GUI Agents with RL (DigiRL to MobileRL)

**TL;DR**
- The field's recipe has settled: **SFT on demonstrations → offline RL → online RL in many parallel emulators**, with rewards from device state or a VLM judge.
- RL adds tens of points of task success over SFT alone.
- This is the "reinforcement loop" on Marc's action list. Its natural home is an emulator farm, with the physical rig used for fine-tuning and evaluation.

**Builds on:** [[Agents — VLM GUI Agents and Vision Grounding Survey]] (the models) and [[Agents — Architecture and Perception Loop]] (the loop). This note adds *how they're trained*.

## The main results

| Work | Method | Result | Takeaway for us |
|---|---|---|---|
| **DigiRL** (NeurIPS 2024) | Offline RL → offline-to-online. Curriculum-filtered Advantage-Weighted Regression. **64 parallel emulators**. VLM evaluator gives reward | 1.3–1.5B VLM: **17.7% → 67.2%** on Android-in-the-Wild. Beat CogAgent and the prior filtered-BC best (57.8%) | Small models plus RL beat big prompted models. Static demos don't cope with real-world randomness. `[Benchmark]` |
| **AndroidWorld** (benchmark) | 116 parameterised tasks across 20 apps. **Reward from system state**, not pixels | The standard evaluation; rewards are robust to task variation | We can't read iPhone state. See [[RL — Rewards and Success Detection from the Screen]]. `[Documented]` |
| **MobileRL** (ICLR 2026) | Difficulty-Adaptive **GRPO** + shortest-path reward reshaping | 9B model: **80.2% AndroidWorld**, 53.6% AndroidLab | GRPO (no value network) is the cheaper online algorithm. Rewarding shorter paths stops dithering. `[Benchmark]` |
| **UI-TARS-2** | Multi-turn PPO variant. A generative outcome reward model where there's no programmatic check | AndroidWorld ~73% (self-reported, harnesses differ) | Use a judge model when state checks aren't possible. `[Benchmark]` |
| **GUI-Owl / Mobile-Agent-v3** | Asynchronous RL, Trajectory-aware Relative Policy Optimisation | GUI-Owl-7B 66.4, Mobile-Agent-v3 73.3 on AndroidWorld | Asynchronous rollouts matter when environments are slow, which our rig is. `[Benchmark]` |
| **GUI-Shepherd** | Process reward model (per-step) + online PPO | 40.5% vs 32.8% baseline; beats outcome-only reward (37.0%) | Dense step rewards help on long tasks, but can be gamed. `[Benchmark]` |

Self-reported scores use different step budgets and prompts. Compare *within* a paper, not across papers.

## A recipe at our scale (RTX 3060 12 GB, later a 4090)

1. **SFT.** Fine-tune the grounding model (the ZonUI-3B path in [[Agents — VLM GUI Agents and Vision Grounding Survey]]) on Flask-app episodes plus emulator traces.
2. **Offline RL.** Run AWR/IQL-style advantage-weighted updates on logged episodes, successes and failures together. No new rollouts needed.
3. **Online RL, emulator first.** Run GRPO with LoRA on a ≤3B policy and N parallel Android emulators (DigiRL used 64; 4–8 is realistic on one box). Use a shortest-path bonus.
4. **Rig fine-tune and evaluation.** A few hundred real episodes with camera input close the gap. See [[RL — Emulator-First Training and Sim-to-Real for the Rig]].

**iOS caveat:** the iOS Simulator runs on a Mac and lacks most App Store apps. Android emulators are the scalable farm, and the policy learns *GUI skills* that mostly transfer to iOS layouts. The transfer needs measuring.

## Pitch in

- [ ] ML: stand up 4 Android emulators with an AndroidWorld subset; reproduce a GRPO baseline on 10 tasks.
- [ ] Robotics: define the rig's action API to match the emulator's (tap x,y · swipe · type · home) so policies swap without changes. See [[iOS Control — Exposing Device Controls to the Agent]].

## Sources

- [DigiRL (arXiv 2406.11896)](https://arxiv.org/abs/2406.11896) · [NeurIPS poster](https://neurips.cc/virtual/2024/poster/96658) `[Benchmark]`
- [MobileRL (arXiv 2509.18119)](https://arxiv.org/html/2509.18119v2) · [ICLR 2026](https://mlanthology.org/iclr/2026/xu2026iclr-mobilerl/) `[Benchmark]`
- [UI-TARS-2 review](https://www.themoonlight.io/en/review/ui-tars-2-technical-report-advancing-gui-agent-with-multi-turn-reinforcement-learning) · [GUI-Owl (arXiv 2508.15144)](https://arxiv.org/abs/2508.15144) · [GUI-Shepherd (arXiv 2509.23738)](https://arxiv.org/html/2509.23738v1) `[Benchmark]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]]
