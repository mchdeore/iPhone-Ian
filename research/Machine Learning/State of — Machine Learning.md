---
type: summary
status: living
author: marc
date: 2026-10-07
updated: 2026-10-10
tags: [machine-learning, state-of]
---

# State of — Machine Learning

> Living summary of everything tagged #machine-learning. **Update this when you add or change an ML note**: one or two lines in the right section, then bump `updated`.

## Current best answers

- **Perception:** a vision-only stack. Phase 2 is zero-shot UGround/OmniParser; Phase 3 fine-tunes a ~3B grounder (ZonUI-3B class) on our own captures. Small fine-tuned models beat big prompted ones → [[Agents — VLM GUI Agents and Vision Grounding Survey]], [[Agents — Architecture and Perception Loop]].
- **Detection:** (full detail in [[State of — YOLO]], tag #yolo) YOLO nano, pretrained, cropped to the screen, `imgsz` 640, `fliplr=0`. Export FP16 by default, INT8 only if CPU-bound, and skip pruning and distillation → [[YOLO — Efficient Training Strategy]], [[YOLO — Quantization]], [[YOLO — Pruning]].
- **Fine-tuning on our GPU:** QLoRA on a 4-bit ~3B VLM is the plan for the RTX 3060 12 GB. It's plausible but **untested**, and image tokens are the memory risk → [[Training — QLoRA Fine-Tuning a Small VLM on 12 GB]].
- **OCR:** no benchmark covers phone UIs. PaddleOCR usually leads on accuracy, Tesseract on speed, and Apple Vision looks strong on macOS. **Measure on our own 200-image set** → [[OCR — Engines for Phone Screens]].
- **Learning loop:** SFT → offline RL → online RL in emulators → rig fine-tune. Details live in [[State of — RL and Simple Robots]].
- **Poker brain (rig / sim only):** blueprint offline, bounded subgame solve online, optional small value net — not for real-money RTA → [[Game Theory — Real-Time Poker Under Personal Compute and Time Banks]]; operator detection → [[Poker Platforms — RTA Bot and Solver Detection]].
- **Betting models:** select them by **calibration, not accuracy**, blend with the market (Benter test), and size with uncertainty-shrunk Kelly. Details live in [[State of — ML and Sports Markets]].

## Decisions made

- Closed loop: flash → capture → label → tap → score → retrain, with JSONL episodes → [[YOLO — Flask Closed-Loop Trainer App]].
- Training compute: free Colab T4, then a used RTX 3060 12 GB → [[YOLO — Training Hardware and Capture Rig]].
- Adopt the **LeRobot dataset format** for rig logs → [[RL — Imitation Learning from Logged Taps (BC, ACT, LeRobot)]].

## Where sources disagree or we're unsure

- Camera photos vs screenshots: there's **no published benchmark** for the grounding accuracy gap. It's ours to measure.
- Self-reported GUI-agent scores (~66–80% on AndroidWorld) use different harnesses and can't be compared across papers.
- VLM judges are lenient, so any reward or evaluation that relies on one is suspect → [[RL — Rewards and Success Detection from the Screen]].

## Open questions

- Does the 3B QLoRA recipe actually fit in 12 GB with our image sizes?
- Which OCR engine wins on our captures (camera path vs screen-capture path)?
- How detectable is the rig to behavioural-biometric models? → [[Behavioral Biometrics — Datasets and Bot-Detection Baselines]] (in progress).

## Next actions

- [ ] Run the QLoRA recipe on 2k Flask samples; post VRAM and point-in-box accuracy.
- [ ] Build the OCR ground-truth set and the 4-engine harness.
- [ ] Get a BC baseline success rate: the number RL has to beat.

## Changelog

- 2026-10-10: linked poker compute-budget and detection notes.
- 2026-10-07: first version.

## Other summaries

[[State of — Sports Analytics]] · [[State of — Cybersecurity]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]] · [[State of — ML and Sports Markets]] · [[State of — Math]] · [[State of — YOLO]] · [[State of — System Design]]
