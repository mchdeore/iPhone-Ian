---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, robotics, rl-and-simple-robots, imitation-learning, behavior-cloning, lerobot, act, smolvla, dagger]
---

# RL — Imitation Learning from Logged Taps (BC, ACT, LeRobot)

**TL;DR**
- Every human tap in the Flask app is already a **demonstration**. Behavior cloning on them is step 1 of the RL recipe, not an alternative to it.
- Adopt **LeRobot's dataset format** for rig logs, so our data works with its policies (ACT, Diffusion, SmolVLA) and its real-robot RL (HIL-SERL).
- Expect a BC ceiling. DigiRL's SFT-only baseline was 17.7%, and RL took it to 67.2%.

**Builds on:** [[YOLO — Flask Closed-Loop Trainer App]] (episode JSONL) and [[RL — Training GUI Agents with RL (DigiRL to MobileRL)]].

## Methods, from cheapest up

| Method | What | When for us |
|---|---|---|
| **Behavior cloning (BC)** | Supervised: screen → action | Grounding and single taps. Equivalent to SFT of the VLM. |
| **DAgger** | Run the policy, have a human label the *correct* action on states the policy visited, retrain | Fixes BC's compounding errors. The Flask app can show "what would you tap here?" on policy-visited screenshots. |
| **ACT** (action chunking transformer) | Predicts *chunks* of future actions; strong on cheap arms | Continuous arm control (SO-101). Overkill for (x, y, tap). |
| **Diffusion Policy / SmolVLA** | Generative action models; SmolVLA is a small vision-language-action model | Multi-task arm skills. SmolVLA fine-tuning guides suggest **~50 good episodes per task** to start, ~10–16 GB VRAM at batch 8. `[Community]` |

## Why LeRobot's format

- One standard for episodes, camera frames, actions and metadata, shared on the Hugging Face Hub. It works across ACT, Diffusion, SmolVLA and HIL-SERL training scripts.
- The **SO-101 arm** (see [[Simple Robots — Cheap Platforms to Practise RL On]]) records natively into it, so the robotics members practise on the same pipeline the phone rig uses.
- Map our rig: `observation.image` = camera/screen frame, `action` = [x_mm, y_mm, z_tap, dwell], `task` = instruction string.

## Data quality beats data quantity

- Vary the conditions *within* a task (lighting, phone position, app state) rather than recording unrelated tasks. That's the same advice the SmolVLA guides give for object positions. `[Community]`
- Log failures too. Offline RL (the next step) needs negative examples; BC alone discards them.

## Pitch in

- [ ] ML: write a converter from the Flask JSONL to a LeRobot dataset (code in repo).
- [ ] Robotics/ML: record 50 demos of one phone task on the rig and train a BC baseline. Report its success rate here as the number RL has to beat.

## Sources

- [LeRobot SmolVLA on SO-101 guide](https://openelab.io/blogs/learn/how-to-fine-tune-smolvla-on-so-101-with-lerobot) · [Community 9-task SO-101 SmolVLA model](https://huggingface.co/Harrysunshine/so101-smolvla-9task) · [NVIDIA — LeRobot background](https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/04-lerobot.html) `[Community]`
- [DigiRL — SFT vs RL](https://arxiv.org/abs/2406.11896) `[Benchmark]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]]
