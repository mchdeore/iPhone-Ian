---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, rl-and-simple-robots, qlora, lora, unsloth, vlm, fine-tuning, gpu]
---

# Training — QLoRA Fine-Tuning a Small VLM on 12 GB

**TL;DR**
- The ML plan calls for fine-tuning a ~3B grounding VLM (ZonUI-3B-class) on our captures, using the **RTX 3060 12 GB**.
- **QLoRA** (4-bit base + LoRA adapters) cuts weight memory ~75%. Unsloth supports Qwen2.5-VL, including vision GRPO.
- No source confirms Qwen2.5-VL-3B QLoRA *on 12 GB* specifically, so treat it as **plausible but untested**. Image tokens are the main memory risk.

**Builds on:** [[Agents — VLM GUI Agents and Vision Grounding Survey]] (ZonUI-3B fits a single 4090 with 24k samples), [[YOLO — Training on Different Hardware]], [[RL — GRPO in Practice on Small GPUs]].

## What the sources support

- QLoRA quantises the base to 4-bit before attaching adapters, "cutting memory by roughly 75%". Guide estimate ~5 GB for 7B *text* models [1].
- Unsloth added **vision RL (GRPO) for Qwen2.5-VL** (Aug 2025), with the 7B example on a free Colab T4 and a "90% less VRAM than FA2 setups" vendor claim [2].
- Current Unsloth VLM guides default to `max_seq_length 2048`, per-device batch 4, with newer small VLMs (e.g. Qwen3.5-2B) on 24 GB [3][4].
- Consumer-GPU guides claim 7B text QLoRA in 2–4 h on 12 GB (secondary source; not VLM) [5].

## Recipe to try (in order of memory relief)

1. Base: 4-bit Qwen2.5-VL-3B-Instruct (Unsloth notebook) [2].
2. **batch 1 + gradient accumulation 8–16**; gradient checkpointing on.
3. **Cap the image resolution.** Our screenshots can be downscaled or cropped to the region of interest, and image tokens dominate sequence length.
4. LoRA r = 16 on attention + MLP; freeze the vision tower first, unfreeze later if grounding plateaus.
5. **Short targets:** the answer is a JSON action or a point (x, y), so `max_seq_length` mostly goes to image tokens.
6. Watch peak VRAM over the first 20 steps; if it OOMs, reduce image size before anything else [4].

## Data format

`(image, instruction) → {"action": "tap", "x": 0.42, "y": 0.77}` in normalised coordinates, so data from phones of different sizes can be mixed. Source: Flask episodes, plus emulator traces later ([[RL — Imitation Learning from Logged Taps (BC, ACT, LeRobot)]]).

## Evaluate like ScreenSpot

Point-in-box accuracy on a held-out set **of our own camera or capture images**, split by element size. Camera photos are harder than screenshots and there's no published benchmark for that gap.

## Pitch in

- [ ] ML: run the recipe on 2k Flask samples; post peak VRAM, step time and point-in-box accuracy.

## Sources

1. [LoRA training on consumer hardware (PDF)](https://insiderllm.com/pdfs/lora-training-consumer-hardware.pdf) `[Community]`
2. [Unsloth — vision RL](https://unsloth.ai/blog/vision-rl) `[Documented]` (vendor)
3. [Intel — VLM fine-tuning with Unsloth](https://docs.openedgeplatform.intel.com/2026.2/edge-ai-suites/ai-suite-manufacturing/industrial-edge-insights-multimodal/how-to-guides/how-to-fine-tune-vlm.html) `[Documented]`
4. [LearnOpenCV — Unsloth vision fine-tuning guide](https://learnopencv.com/unsloth-guide-efficient-llm-fine-tuning/) `[Community]`
5. [MachineLearningPlus — Unsloth fine-tuning](https://machinelearningplus.com/gen-ai/unsloth-fine-tuning/) `[Community]`
