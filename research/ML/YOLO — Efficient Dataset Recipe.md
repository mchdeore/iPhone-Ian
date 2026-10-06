---
tags: [YOLO, training, dataset, ML, computer-vision]
status: answered
date: 2026-10-04
related:
  - "[[== ML CENTRAL ==]]"
---

# 01 — What makes an efficient YOLO training set

Scope: a data-efficient YOLO detector for a **fixed camera filming a stock iPhone**,
with the flash app (`02-synthetic-data-and-flash-app.md`) auto-labeling targets at
known screen coordinates.

Tags: `[Documented]` official docs/papers · `[Benchmark]` measured · `[Community]` anecdotal/forum.

## Q: How many images and instances per class?

- Ultralytics target: **≥1,500 images/class** and **≥10,000 labeled instances/class** for reliable real-world performance. `[Documented]`
- Floor to *start*: "a few hundred annotated objects per class" is enough to experiment with transfer learning. `[Documented]`
- Instances matter more than images. Lever for us: **flash 3–8 targets per frame** to hit instance counts fast.

## Q: How much does label quality matter, and what's our risk?

Ultralytics rules: label every instance of every class in every image (partial
labeling "will not work"), boxes tight with no gap, no missing labels; eyeball
`train_batch*.jpg`. `[Documented]`

Our advantage: flash-app labels are tight, complete and consistent **by
construction**. The risk moves to **camera↔screen homography calibration** — a
drifting mount silently corrupts every label. Treat the homography as a sensor that
needs recalibration (re-detect fiducials per frame).

## Q: What diversity matters when filming a screen?

Images must be "representative of the deployed environment" (lighting, angle,
camera). `[Documented]` Screen-specific nuisances to cover: **glare/specular
highlights, moiré, motion blur, brightness/auto-exposure swings, slight oblique
perspective**. Diversity of conditions beats raw count.

## Q: Background images and class balance?

- **0–10% background (negative) images** with no label file (COCO ≈1%). Use blank, other-app and screen-off frames. `[Documented]`
- Keep class distribution similar across splits; oversample rare classes. `[Documented]`

## Q: How do we split without leakage?

- Rule: val/test never in train. `[Documented]`
- Trap: consecutive video frames are near-duplicates; random per-frame splits leak them into val → inflated mAP. **Split by capture session**, and de-duplicate bursts (perceptual hash / motion threshold). ~80/20 or 70/20/10. `[Community]`

## Q: What `imgsz` for small UI icons?

- Default `imgsz=640`; many small objects benefit from **1280**; train and infer at the **same** size. `[Documented]`
- A tall phone screen letterboxed into 640² shrinks icons to ~15–25 px. Mitigations:
 1. **Crop to the screen region** before training (biggest, cheapest win).
 2. Train at **960–1280** (cost: ~2.25–4× memory/time vs 640 — see `03-hardware.md`).
 3. **SAHI** tiled inference as fallback (+38% small-object mAP in one YOLOv5 study). `[Benchmark]`
- Prior art: ScreenParser, a YOLO UI detector with 55 classes. `[Documented]`

## Q: Which augmentations to keep vs disable?

Detect defaults: `hsv_h=0.015 hsv_s=0.7 hsv_v=0.4 degrees=0 translate=0.1 scale=0.5
shear=0 perspective=0 flipud=0 fliplr=0.5 mosaic=1.0 mixup=0 copy_paste=0
close_mosaic=10`. `[Documented]`

| Aug | Action | Why |
|---|---|---|
| `fliplr` | **set 0.0** | Default 50% mirror flips text/chevrons ("‹ Back" → "Back ›") — never happens on a real phone |
| `flipud` | keep 0 | same |
| `mosaic` | lower (~0.3) + `close_mosaic=10` | Helps small objects but fabricates multi-screen composites |
| `degrees`/`shear` | keep 0 | Fixed POV |
| `perspective`/`translate`/`scale` | mild (`0.0005`/`0.1`/`0.3`) | Covers mount drift |
| HSV | keep default | Covers brightness/True Tone/exposure |

If `albumentations` is installed, Ultralytics silently adds blur/CLAHE/grayscale at
p=0.01 (uninstall to remove). `[Documented]`

## Q: Pretrained or scratch? Which model size?

- **Pretrained (COCO) + fine-tune** for small/medium datasets; scratch only at COCO scale. Optional `freeze` of early layers. `[Documented]`
- Start **nano (`n`)**; move to **small (`s`)** only if mAP is insufficient. Closed-loop latency usually dominates. `[Documented]`

## Q: Epochs and early stopping?

Ultralytics suggests starting at 300 epochs and adjusting. For a small first set:
**100–300 epochs, `patience` 20–50, `batch=-1`** (auto ~60% VRAM), AMP on (default). `[Documented]`

## Q: Active learning / diminishing returns?

- Labeling is free here, so the analogue of active learning is **hard-example mining**: keep frames where the detector misses the known target (low IoU/conf, bad tap) and oversample those conditions. The **tap score is a built-in difficulty signal**.
- Gains are steep up to a few hundred instances/class, solid by ~1,500 images/class, then flat — more data only helps when it adds **new conditions**. `[Community]`

## Q: Is "reinforcement YOLO" a thing?

**No.** YOLO training is supervised (box + class + DFL loss on labeled boxes); there
is no reward and no standard "reinforcement YOLO." `[Documented]` RL can sit **on
top** as a controller fed by YOLO detections (e.g. YOLO-perception + DRL grasping,
MDPI 2023). `[Community]`

For this project, box → screen coord → gantry steps is a **deterministic geometric
mapping**. Closed-loop calibration (flash → detect → tap → measure error → fit
affine/homography correction) converges in dozens of samples. Use the tap score as
(1) a detector/calibration metric and (2) a hard-example signal. Reserve RL for
sequential UI navigation, after perception + calibration are solid. This matches the
existing note in `specs/02-firmware-and-software.md` §5.1.

## Recommended minimal recipe

**Phase 0 — single-class flash-target model**
- 1 class (`tap_target`), auto-labeled.
- **300–800 frames × 3–8 targets** → 2k–6k instances.
- 4–6 lighting setups, 2–3 brightness levels, 2–3 phone re-seatings, ± glare, some blur.
- 5–10% negatives.
- Crop to screen; `imgsz` 640 first, 960–1280 if small targets miss.
- `yolo11n.pt`, `epochs=100 patience=20 batch=-1`.
- `fliplr=0 flipud=0 degrees=0 mosaic=0.3 close_mosaic=10 perspective=0.0005 translate=0.1 scale=0.3`.
- Split by session, 80/20, de-duplicated.

```bash
yolo detect train model=yolo11n.pt data=flash.yaml imgsz=640 epochs=100 patience=20 batch=-1 \
 fliplr=0 flipud=0 degrees=0 mosaic=0.3 close_mosaic=10 perspective=0.0005 translate=0.1 scale=0.3
```

**Phase 1 — UI vocabulary**: 5–8 coarse classes (button, text_field, icon,
keyboard_key, toggle, back_chevron, list_row, link). Start 300–500 images/class,
scale toward 1,500 images / 10k instances per class. Keep `fliplr=0` permanently.

## Key takeaways

- Targets: ≥1,500 images & ≥10k instances/class; a few hundred instances/class is enough to start with pretrained weights.
- Auto-labeling kills the label-quality problem **only if the homography stays calibrated**.
- Spend effort on diversity + 0–10% negatives, not raw count.
- Split by session, not by frame.
- `fliplr=0`; tame mosaic; keep HSV + mild geometry.
- Small targets → crop + higher `imgsz`; SAHI fallback.
- Pretrained nano first.
- No "reinforcement YOLO"; tap score → calibration + hard-example mining.

## Sources

- https://docs.ultralytics.com/guides/model-training-tips/
- https://docs.ultralytics.com/yolov5/tutorials/tips-for-best-training-results/
- https://docs.ultralytics.com/datasets/detect/
- https://docs.ultralytics.com/guides/data-collection-and-annotation/
- https://docs.ultralytics.com/modes/train/
- https://docs.ultralytics.com/guides/yolo-data-augmentation/
- https://docs.ultralytics.com/guides/sahi-tiled-inference/
- https://arxiv.org/html/2511.19728v1 (SAHI +38% small-object result)
- https://huggingface.co/docling-project/ScreenParser
- https://www.mdpi.com/2075-1702/11/2/275 (YOLO + DRL grasping)
- https://arxiv.org/abs/2508.01966
