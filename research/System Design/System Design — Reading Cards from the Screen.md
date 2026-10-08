---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [system-design, machine-learning, yolo, card-games, computer-vision, ocr]
---

# System Design — Reading Cards from the Screen

**TL;DR**
- On a phone **screen capture**, cards are pixel-identical every time, so **template matching on corner indices** gets near-perfect accuracy with no training. Start there.
- A **52-class YOLO** trained on synthetic cards reaches mAP50 ≈ 0.995 on its own validation set but stumbles on real-world card designs. Fine-tune on *our* game's art if we need a detector.
- The tricky parts aren't rank and suit. They're **face-down cards, overlapping stacks, animations and highlights**.

**Builds on:** [[State of — YOLO]] (training recipe), [[OCR — Engines for Phone Screens]], [[System Design — Card-Playing Gantry Rig Architecture]].

## Options

| Approach | Accuracy | Effort | When |
|---|---|---|---|
| **Template matching** on the rank/suit corner crop (OpenCV `matchTemplate`) | ~100% on screen capture of a fixed card skin | Hours: crop 13 ranks + 4 suits once | **MVP, screen-capture path** |
| **Layout-first parsing:** known pile positions → crop each pile's top card → classify | Very high; avoids detection entirely | Low | Fixed-layout games (Klondike, FreeCell) |
| **YOLO 52-class detector** | YOLO11s on Roboflow synthetic cards: mAP50 0.995, mAP50-95 ~0.80 (own split); misses some black court cards on real photos [1] | Medium: fine-tune on game captures | Camera path, varied layouts, multiple skins |
| **OCR on rank + colour/shape for suit** | Depends on font | Low | Fallback / sanity check |
| **VLM ("what cards are visible?")** | Flexible but slow and can hallucinate | Low effort, high latency | Debugging and unknown games only |

Datasets: Roboflow "Playing Cards" collections are synthetic cards on varied backgrounds (one has ~21k train images) [2]. A YOLOv4 study generated synthetic card data for duplicate bridge and reported 99.8% detection efficiency [3].

## Gotchas specific to card UIs

- **Two corners per card:** detectors fire on both visible corners, so **merge them into one card** by proximity [4].
- **Overlapping tableau stacks:** only the top strip of each covered card is visible. Classify by **corner strip** and pile order, not the full card face.
- **Face-down cards:** a separate "back" class; count them per pile, since the state tracker needs the counts.
- **Animations:** cards slide and flip for ~300–800 ms. Wait for **two identical consecutive frames** before reading ([[System Design — Drag, Tap and Verify Primitives for Card Moves]]).
- **Highlights and hints:** selection glow and hint arrows change pixels. Make templates highlight-invariant (grayscale + edges), or detect the glow as a signal.
- **Ads and pop-ups:** a "Rate us!" dialog breaks layout parsing. Detect non-game screens explicitly (and treat their text as untrusted).

## Validation

Build 200 labelled frames from real games. Metrics: per-card exact match, pile-count accuracy, and **state accuracy** (whole board correct). The state accuracy is what the solver needs, and it should be ≥99.5% before automation runs unattended.

## Sources

1. [YOLO11s playing-cards detector (model card)](https://huggingface.co/sroot/yolo11s-playing-cards-detector) · [later gen fine-tuned on real video](https://huggingface.co/sroot/lgd-cards-gen1) `[Community]`
2. [Roboflow Universe — Playing Cards dataset](https://universe.roboflow.com/uniontech/playing-cards-ow27d-nrh6c) `[Documented]`
3. [Synthetic training data for duplicate bridge card detection (arXiv 2109.11861)](https://arxiv.org/pdf/2109.11861) `[Benchmark]`
4. [Hack Club devlog — card corner merging](https://stardance.hackclub.com/projects/25641/devlogs/16067) · [Ultralytics — recognising playing cards](https://www.ultralytics.com/blog/using-a-vision-ai-model-to-recognize-playing-cards) `[Community]`

## Related

- **Summary:** [[State of — System Design]] · [[State of — Machine Learning]] · [[State of — YOLO]]
- **See also:** [[YOLO — Synthetic Data and Flash Training App]] · [[System Design — Game State and Decision Engines for Card Games]]
