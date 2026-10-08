---
type: summary
status: living
author: marc
date: 2026-10-07
updated: 2026-10-07
tags: [machine-learning, yolo, state-of]
---

# State of — YOLO

> Living summary of everything tagged #yolo (UI element detection for the rig). **Update this when you add or change a YOLO note**, then bump `updated`.

## Current best answers

- **Model:** start from COCO `yolo11n.pt`, not a UI-pretrained model. Crop to the screen, `imgsz=640`, `cache=ram`, `batch=-1`, `patience≈20`. Try `freeze=11` first → [[YOLO — Efficient Training Strategy]].
- **Classes:** a few coarse classes (start with 1, then ~6: `text_button, icon_button, text_field, toggle_switch, keyboard_key, cell_row`). Fine identity comes from **OCR + a small icon classifier**; the keyboard is a fixed grid → [[YOLO — Detection Grouping and Class Taxonomy]], [[OCR — Engines for Phone Screens]].
- **Data:** aim for ≥1,500 images and ≥10k instances per class eventually, though a few hundred per class is enough to start. Prioritise diversity and 0–10% negatives; `fliplr=0`; **split by session, dedupe before splitting** → [[YOLO — Efficient Dataset Recipe]].
- **Synthetic data:** the flash app gives free labels via per-frame homography. Domain randomisation is the biggest lever. Keep **5–20% real** and fail closed when calibration drifts → [[YOLO — Synthetic Data and Flash Training App]], [[YOLO — Flask Closed-Loop Trainer App]].
- **One pooled run** (mostly synthetic plus real). Retrain on the whole pool from `yolo11n.pt`; never fine-tune on new frames only → [[YOLO — Efficient Training Strategy]].
- **Hardware:** nano needs 4–6 GB at 640. Free Colab T4 now, a used RTX 3060 12 GB later. The 16 GB CPU box is an overnight fallback (`cache='disk'`) → [[YOLO — Training Hardware and Capture Rig]], [[YOLO — Training on Different Hardware]].
- **Deployment:** **FP16 is the default** (free ~2×, ~0 mAP loss). INT8 PTQ only if CPU-bound (−1–3 mAP on nano; calibrate on flash captures). **Skip pruning and classic KD.** The gantry, not the forward pass, is the bottleneck → [[YOLO — Quantization]], [[YOLO — Quantization by Hardware]], [[YOLO — Pruning]], [[YOLO — Knowledge Distillation]], [[YOLO — Other Optimization Techniques]].
- **"Distillation" that does pay:** offline pseudo-labelling by a big VLM, then train nano normally → [[YOLO — Knowledge Distillation]].

## Decisions made

- No "reinforcement YOLO": the tap score drives hard-example mining and calibration, not RL. (Agent-level RL lives in [[State of — RL and Simple Robots]].)
- Training is offline and periodic; the app only serves and logs.
- Labels and datasets stay out of git (`datasets/`, `captures/` ignored).

## Where sources disagree or we're unsure

- Model generation: notes reference `yolo11n` and `yolo26n`. Pick one and pin it in the training config.
- Camera vs screen capture changes the data distribution: screen capture makes synthetic ≈ real and shrinks the need for camera randomisation → [[Rig — iPhone Screen Capture Paths (USB, AirPlay, Multi-Phone)]].

## Open questions

- Does the detector still matter if a fine-tuned grounding VLM (ZonUI-3B class) handles targeting? It's likely kept as a fast, cheap first stage and for OCR crops.
- Real-validation mAP on actual iOS screens: not measured yet.

## Next actions

- [ ] Phase 0: 1 class, 300–800 auto-labelled frames, Colab T4, report real-val mAP.
- [ ] Pin the YOLO version; add a pHash dedupe + StratifiedGroupKFold split script.
- [ ] Pseudo-label 500 real iOS screenshots with a VLM; measure the lift.

## Changelog

- 2026-10-07: first version; YOLO promoted to its own key tag and folder.

## Other summaries

[[State of — Sports Analytics]] · [[State of — Machine Learning]] · [[State of — Cybersecurity]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]] · [[State of — ML and Sports Markets]] · [[State of — Math]] · [[State of — System Design]]
