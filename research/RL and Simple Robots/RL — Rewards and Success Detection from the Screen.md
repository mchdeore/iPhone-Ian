---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, cybersecurity, robotics, rl-and-simple-robots, reinforcement-learning, reward-design, vlm-judge, reward-hacking, verification]
---

# RL — Rewards and Success Detection from the Screen

**TL;DR**
- Emulator RL reads success straight from device state. A black-box iPhone gives us only **pixels**.
- Pixel-only VLM judges are **systematically lenient**: they score failures as successes. RL then **reward-hacks** them, so the reward climbs while real success doesn't.
- Fix: get dense, verifiable reward from our own Flask flash app; make the robot **probe** state for real apps; and keep an honest metric the policy can't touch.

**Builds on:** [[YOLO — Flask Closed-Loop Trainer App]] (episodes and scores) and [[RL — Training GUI Agents with RL (DigiRL to MobileRL)]].

## What goes wrong

- **Leniency bias.** OSReward found even top VLM judges lean lenient and mislabel failed runs as successes. The reliable ones are too expensive to run at scale. Its open 9B/35B reward models match commercial judges at 30–60× lower cost. `[Benchmark]`
- **Screenshot-only judging misses state.** In the Interactive Reward Agent paper, a before/after-screenshot judge got VLC fullscreen wrong (the oracle checked window size) and passed a failed Chrome task. `[Benchmark]`
- **Reward hacking.** Demo2Reward: frequent VLM false positives "induce severe reward hacking", and the policy never solves the task. `[Benchmark]`
- **Judges can be fooled** with trivial inputs. LLM-judge false-positive rates hit 80% in one study (different domain, but it shows the scale). `[Benchmark]`

## The reward ladder for our rig (best first)

| Source | Where | Reward quality |
|---|---|---|
| **Ground truth from our own app** | Flask flash app: it knows where the target was drawn and receives the tap event | **Perfect, dense.** Use it for all grounding and tapping RL. |
| **Deterministic screen checks** | OCR / template match for an expected end state ("Saved", a specific screen title) | High. Brittle across app versions, so version-pin the checks. |
| **Active probing** | The robot *does something* to verify, e.g. reopens a list to confirm an item exists (the ProRe idea) | High, but costs extra steps. Use it for the final step only. |
| **Voting judges** | Several VLM queries must *all* agree (ZeroGUI) | Medium. Cuts false positives a lot. |
| **Single VLM judge** | One screenshot pair | Low. Evaluation hint only, never a training reward. |

**Process rewards** (per step, GUI-Shepherd style) speed up learning on long tasks but are the easiest to game. Cap their weight, and always keep a sparse outcome term (as ADMIRE argues).

## Honest metric (keep it outside the loop)

- A fixed hold-out task set, scored by **deterministic checks plus occasional human audit**, never by the training judge.
- Track judge-says-success minus audited success over training. A growing gap means hacking.

## Security angle

A policy optimised against a lenient judge learns to *look* done. On a real phone with real accounts that's a safety bug. Keep the agent on an **app allowlist** during RL, and never train on apps that can move money or send messages.

## Pitch in

- [ ] ML: add a `reward_source` field to episode JSONL (`app_truth | ocr | probe | vote | judge`) so we can always filter to trustworthy rewards.
- [ ] Security: draft the allowlist and blocklist for apps the agent may touch during training.

## Sources

- [OSReward](https://www.alphaxiv.org/abs/2607.28609) · [Interactive Reward Agent (arXiv 2607.25904)](https://arxiv.org/pdf/2607.25904) · [Demo2Reward (arXiv 2606.00083)](https://arxiv.org/pdf/2606.00083) · [GUI Agents with RL survey (arXiv 2604.27955)](https://arxiv.org/pdf/2604.27955) `[Benchmark]` (preprints)
- [One Token to Fool LLM-as-a-Judge (arXiv 2507.08794)](https://arxiv.org/html/2507.08794v1) · [GUI-Shepherd](https://arxiv.org/html/2509.23738v1) `[Benchmark]`
