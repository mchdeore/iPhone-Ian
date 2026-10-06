---
tags: [YOLO, hardware, GPU, training, ML, Colab]
status: answered
date: 2026-10-04
related:
  - "[[YOLO — Efficient Dataset Recipe]]"
  - "[[YOLO — Synthetic Data and Flash Training App]]"
---

# 03 — Hardware for YOLO training and the capture rig

Epoch times are estimates from
community reports and can swing 2–3× with dataset/`imgsz`/workers.

## Q: What is the bare minimum hardware?

| Option | Verdict |
|---|---|
| **CPU only** | Works (Ultralytics falls back to `device='cpu'`) but 1–2 orders slower: est. **~10–40 min/epoch** for 2–5k images on an 8-core desktop. OK for one overnight run; too slow for iteration. `[Documented]/[Community]` |
| **Apple Silicon (`device='mps'`)** | Works but immature: arXiv:2501.14925 measures a significant gap vs NVIDIA `[Benchmark]`; known zero-mAP bug (#9113) and MPS-slower-than-CPU at small batch `[Community]`. ~2–15 min/epoch. **Check mAP ≠ 0 after epoch 1.** |
| **Free cloud — Colab T4 16 GB** (≈RTX 2070) | **Recommended zero-cost path.** ~20–90 s/epoch for n/s. Kaggle (T4×2/P100) equivalent. `[Documented]` |
| **Cheapest practical NVIDIA** | **8 GB floor** for comfort; nano/small fit in **4–6 GB @640 with AMP**. Must have **Tensor Cores (RTX 20-series+)**. Sweet spot: **used RTX 3060 12 GB (~$300)**. `[Documented]` |

**Capture rig minimum**
- Camera: **1080p/30 fps UVC webcam** is plenty (training is at 640). **Locked manual focus + exposure matters far more than resolution** — AF hunting / AE drift poison auto-labels. Logitech C920/C922/Brio expose UVC manual controls. Global shutter not needed.
- Rigid mount for phone + camera; controlled lighting.
- Host: serving the flash page + driving GRBL over USB serial is near-zero load. **The current Mac is fine as rig host**; offload training.

## Q: What factors most contribute to suitability? (ranked)

1. **GPU VRAM** — hard gate on `batch × imgsz`. Activation memory scales ~`imgsz²` (1280 ≈ 4× the cost of 640). `batch=-1` targets ~60% VRAM; validation uses 2× train batch. `[Documented]`
2. **GPU compute: Tensor Cores > memory bandwidth > cache > raw FLOPS** (Dettmers). Tensor Cores unlock the default `amp=True`. `[Documented]`
3. **CUDA vs MPS/CPU** — CUDA is stable, fast, AMP-enabled; MPS slower and buggier. `[Benchmark]`
4. **Dataloader throughput** — the usual hidden bottleneck when GPU utilization is low. Use `cache='ram'` (a few-GB dataset fits) and enough `workers`. `[Community]`
5. PCIe/interconnect — minor for one GPU.

## Q: What are the least limiting components?

Dettmers: for single-GPU, don't overspend on PCIe lanes, CPU cores, or RAM speed. `[Documented]`

| Rank | Component | How limiting | Why |
|---|---|---|---|
| 1 | GPU VRAM | **Hard gate** | batch×imgsz ceiling / OOM |
| 2 | Tensor Cores + memory bandwidth | High | Drives epoch speed |
| 3 | CUDA vs MPS/CPU | High | AMP + mature kernels |
| 4 | Dataloader (workers, cache) | Medium | Starves GPU if weak |
| 5 | RAM beyond ~2× dataset | Low | Excess sits idle |
| 6 | CPU beyond ~6–8 cores | Low | Only feeds the loader |
| 7 | NVMe vs SATA (once cached) | Low | Served from RAM after epoch 1 |
| 8 | PCIe gen / x8 vs x16 | Very low | Negligible for single GPU |
| 9 | Storage capacity | Very low | ~50 GB suffices |
| 10 | PSU / motherboard / network | Negligible | Just needs to power the card |

**Rule:** buy VRAM + Tensor Cores first; everything else only needs to be "enough."

## Three tiers (YOLO11n/s, ~2–5k images @640, est.)

| Tier | Hardware | Cost | `n` / epoch | `s` / epoch |
|---|---|---|---|---|
| Zero-cost | Mac MPS **or** Colab free T4 | $0 | MPS ~2–8 min · T4 ~20–60 s | MPS ~5–15 min · T4 ~40–90 s |
| Budget | Used RTX 3060 12 GB (or 8 GB 2060S/3060 Ti) | $300–600 | ~10–25 s | ~20–45 s |
| Comfortable | RTX 3090 / 4070 Ti / 4090 (16–24 GB) | $800–1,800 | ~5–15 s | ~10–25 s |

Iteration math: ~15 s/epoch × 50 epochs ≈ **12 min per model** on the budget tier →
many retrain cycles/day. Minutes-per-epoch on CPU/MPS is what bottlenecks the
flash → train → evaluate loop. For HomeLab, a used 12 GB RTX 3060 in the server is
the natural target.

## Key takeaways

- VRAM gates; Tensor Cores + bandwidth set speed; the rest just needs to be adequate.
- Nano/small need only 4–6 GB @640; used 12 GB RTX 3060 is the sweet spot.
- Free Colab T4 beats Mac MPS on speed and reliability — use it until a GPU lands in HomeLab.
- Mac = capture/gantry host.
- Dataloader is the common real bottleneck → `cache='ram'` + workers.
- Camera: lock focus + exposure; resolution beyond 1080p is irrelevant.

## Sources

- https://docs.ultralytics.com/modes/train/
- https://docs.ultralytics.com/help/FAQ/
- https://timdettmers.com/2023/01/30/which-gpu-for-deep-learning/
- https://timdettmers.com/2018/12/16/deep-learning-hardware-guide/
- https://arxiv.org/abs/2501.14925 — Apple Silicon vs NVIDIA training profiling
- https://github.com/ultralytics/ultralytics/issues/9113 — MPS zero-metrics bug
- https://github.com/ultralytics/ultralytics/issues/1010 — cache=ram + workers bug
- https://github.com/ultralytics/ultralytics/issues/3097
- https://github.com/ultralytics/ultralytics/issues/7673
- https://forums.developer.nvidia.com/t/yolov8-model-training-on-jetson-orin-nano/301591
- https://markaicode.com/errors/yolov11-common-errors-and-fixes/
- https://towardsdatascience.com/the-comprehensive-guide-to-training-and-running-yolov8-models-on-custom-datasets-22946da259c3/
