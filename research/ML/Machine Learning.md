---
tags: [ml]
---

# Machine Learning

Central node for all ML research. Every note in this cluster feeds into the ML pipeline.

What we know:

- Vision-only grounding works (literature validated). No accessibility tree needed — we're camera-based anyway
- Phase 2: UGround/OmniParser zero-shot for prototyping
- Phase 3: fine-tune ZonUI-3B (3B params, single RTX 4090, 24K samples) on our iPhone captures
- Camera-photo grounding is an open research gap — screenshots ≠ photos
- YOLO nano with pretrained COCO weights, crop to screen, 640 imgsz, fliplr=0
- Synthetic data via Flask flash app with ArUco fiducials + per-frame homography
- Free Colab T4 for training; used RTX 3060 12 GB (~$300) when HomeLab lands
- FP16 export by default; INT8 PTQ only if CPU-bound. Skip pruning and KD for now
- Closed-loop trainer: flash → capture → label → tap → score → retrain

Agent: [[AI Agent Architecture and Perception Loop]]
Grounding: [[VLM GUI Agents and Vision Grounding Survey]]
Dataset: [[YOLO — Efficient Dataset Recipe]]
Synthetic: [[YOLO — Synthetic Data and Flash Training App]]
Hardware: [[YOLO — Training Hardware and Capture Rig]]
Trainer: [[YOLO — Flask Closed-Loop Trainer App]]
Strategy: [[YOLO — Efficient Training Strategy]]
Controls: [[YOLO — Exposing Device Controls to Model]]