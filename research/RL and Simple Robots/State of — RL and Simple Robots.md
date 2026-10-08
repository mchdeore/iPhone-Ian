---
type: summary
status: living
author: marc
date: 2026-10-07
updated: 2026-10-07
tags: [rl-and-simple-robots, machine-learning, robotics, state-of]
---

# State of — RL and Simple Robots

> Living summary of everything tagged #rl-and-simple-robots. **Update this when you add or change a note here**, then bump `updated`.

## Current best answers

- **Use RL only where it pays:** the agent policy is RL; tap parameters are bandits/BO (tens of trials); motion and targeting are classical control → [[RL — Where RL Helps a Gantry Robot (and Where It Doesn't)]], [[RL — Bandits and Bayesian Optimisation for Hardware Tuning]].
- **Recipe:** SFT/BC on logged taps → offline RL (IQL / advantage-weighted SFT) → online **GRPO** in emulators → rig fine-tune. DigiRL went from 17.7% to 67.2% over SFT alone; MobileRL reached 80.2% on AndroidWorld → [[RL — Training GUI Agents with RL (DigiRL to MobileRL)]], [[RL — Offline RL from Logged Episodes (IQL, CQL, AWR)]], [[RL — GRPO in Practice on Small GPUs]].
- **Rewards are the hard part:** pixel-only VLM judges are lenient and get reward-hacked. Use the reward ladder: app ground truth > OCR checks > active probing > voting judges > a single judge → [[RL — Rewards and Success Detection from the Screen]].
- **Tasks:** generate them in emulators (ZeroGUI style), keep tasks with a 20–80% success rate, and promote only verifiable ones to the rig → [[RL — Self-Generated Tasks and Curricula for GUI Agents]].
- **Sim-to-real for the rig** = emulator + camera-corruption + actuator-noise wrappers, not a physics twin → [[RL — Emulator-First Training and Sim-to-Real for the Rig]].
- **Real-world throughput:** ~1–2.4k steps/hour/phone, but resets are free. HIL-SERL-style learning (1–2.5 h per skill) fits that budget → [[RL — Real-World Training Loop on the Gantry (Resets, Safety, HIL-SERL)]].
- **Practice hardware:** an SO-101 group build (LeRobot-native, printable); Open Duck Mini or Microduck for locomotion sim-to-real → [[Simple Robots — Cheap Platforms to Practise RL On]], [[Simple Robots — Sim-to-Real Walking for Cheap Bipeds]].

## Decisions made

- LeRobot dataset format for rig logs; a `reward_source` field on every episode.
- The rig action API matches the emulator's (tap · swipe · type · home · wait).
- Safety envelope: soft limits = screen + margin, app allowlist, watchdog.

## Where sources disagree or we're unsure

- Whether Android-emulator GUI skills transfer to iOS layouts on the rig: unmeasured.
- Whether vision GRPO fits our 12 GB GPU: vendor claims only → [[Training — QLoRA Fine-Tuning a Small VLM on 12 GB]].

## Open questions

- Does screen capture (vs camera) remove most of the visual sim-to-real gap? (Depends on the capture decision.)
- Is single-step GRPO on Flask screenshots enough before multi-step?

## Next actions

- [ ] Tap-parameter bandit on the rig: the first learning-on-hardware result.
- [ ] Flask JSONL → LeRobot converter → BC baseline.
- [ ] 4 Android emulators + GRPO on 10 AndroidWorld tasks.
- [ ] Price the SO-101 servo BOM.

## Changelog

- 2026-10-07: first version.

## Other summaries

[[State of — Sports Analytics]] · [[State of — Machine Learning]] · [[State of — Cybersecurity]] · [[State of — Robotics]] · [[State of — ML and Sports Markets]] · [[State of — Math]] · [[State of — YOLO]]
