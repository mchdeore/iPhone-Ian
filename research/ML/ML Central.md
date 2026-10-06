---
tags: [ml]
---

# ML Central

Vision-only grounding. YOLO nano detection. ZonUI-3B fine-tuning on iPhone captures. Flask flash app for synthetic data.

## Research

- [[AI Agent Architecture and Perception Loop]]
- [[VLM GUI Agents and Vision Grounding Survey]]
- [[YOLO — Efficient Dataset Recipe]]
- [[YOLO — Synthetic Data and Flash Training App]]
- [[YOLO — Training Hardware and Capture Rig]]
- [[YOLO — Training on Different Hardware]]
- [[YOLO — Quantization]]
- [[YOLO — Flask Closed-Loop Trainer App]]
- [[YOLO — Pruning]]
- [[YOLO — Other Optimization Techniques]]
- [[YOLO — Detection Grouping and Class Taxonomy]]
- [[YOLO — Knowledge Distillation]]
- [[YOLO — Quantization by Hardware]]
- [[YOLO — Efficient Training Strategy]]
- [[YOLO — Exposing Device Controls to Model]]
- [[YOLO — Windows Public Port and Streaming]]
- [[YOLO — Raspberry Pi Input Converter]]

## Key decisions

- Phase 2: UGround/OmniParser zero-shot
- Phase 3: ZonUI-3B fine-tuned on iPhone camera captures (3B, single RTX 4090)
- YOLO nano pretrained, crop to screen, 640 imgsz, fliplr=0
- Free Colab T4 → used RTX 3060 12 GB (~$300)
- FP16 export default. INT8 PTQ only if CPU-bound. Skip pruning/KD
- Closed-loop: flash → capture → label → tap → score → retrain