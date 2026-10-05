---
tags: [YOLO, index, ML, computer-vision]
status: answered
date: 2026-10-04
related:
  - "[[../06-vlm-gui-agent-survey]]"
---

# YOLO training setup — research index

Research session 2026-10-04. Question: what makes an efficient "reinforcement"
YOLO training setup for iPhone-Ian (dataset, synthetic flash app, hardware)?
Gathered by three parallel research agents; sources listed in each note were found
by those agents and not individually re-verified.

| File | Covers |
|---|---|
| [`01-efficient-dataset.md`](01-efficient-dataset.md) | Dataset size, label quality, diversity, splits, `imgsz`, augmentations, model size, "is reinforcement YOLO a thing?", minimal recipe |
| [`02-synthetic-data-and-flash-app.md`](02-synthetic-data-and-flash-app.md) | Domain randomization, synthetic:real ratios, flash-app architecture, CSS px/DPR, Safari viewport, sync, glare/moiré, pitfalls |
| [`03-hardware.md`](03-hardware.md) | Bare-minimum hardware, most vs least limiting components (ranked), cost tiers, capture rig |

## Questions answered (short form)

**Is "reinforcement YOLO" a thing?** No. YOLO is supervised detection. The tap
score is best used as a calibration metric and hard-example signal; RL is optional
and only on top, for sequential navigation. → `01`

**What makes an efficient training set?** Pretrained nano model; a few hundred
instances/class to start (Ultralytics target ≥1,500 images / ≥10k instances per
class); diversity of conditions over raw count; 0–10% negatives; split by session,
not frame; crop to screen; `fliplr=0`. → `01`

**How do we make synthetic data?** The flash app: Flask page in Safari shows
randomized targets + 4 fiducials in CSS px; flash → hold → capture; per-frame
homography maps boxes to camera pixels → YOLO labels for free. Add ~5–20% real iOS
captures for fine-tune/validation. → `02`

**Bare minimum hardware?** $0: the current Mac as rig host + free Colab T4 for
training. Cheapest local GPU worth buying: used RTX 3060 12 GB (~$300). Camera:
1080p UVC webcam with locked focus/exposure. → `03`

**What matters most?** GPU VRAM → Tensor Cores/memory bandwidth → CUDA (vs MPS/CPU)
→ dataloader throughput. → `03`

**What matters least?** PCIe gen/lanes, CPU beyond 6–8 cores, RAM beyond 2× dataset,
NVMe vs SATA, storage size, PSU/motherboard/network. → `03`

## Cross-note tension to resolve

`01` suggests `imgsz` 960–1280 for small icons; `03`'s timings assume 640, and 1280
costs ~4× memory/time. Plan: **crop to screen and start at 640**; raise `imgsz`
only if small targets are missed.

## Suggested next steps

1. Build the flash page (Flask, 4 ArUco fiducials, randomized targets, frame-ID patch).
2. Capture Phase 0 (~500 frames, single class) with locked camera settings.
3. Train `yolo11n` on Colab T4; validate on real, hand-checked iOS captures.
