---
type: hub
---

# == MACHINE LEARNING ==

Training, datasets, computer vision (YOLO), VLM GUI agents, and compression/deployment to small hardware.

## Notes

- [[Agents — Architecture and Perception Loop]] · also Robotics
- [[Agents — VLM GUI Agents and Vision Grounding Survey]]
- [[YOLO — Detection Grouping and Class Taxonomy]]
- [[YOLO — Efficient Dataset Recipe]]
- [[YOLO — Efficient Training Strategy]]
- [[YOLO — Flask Closed-Loop Trainer App]] · also Robotics
- [[YOLO — Knowledge Distillation]]
- [[YOLO — Other Optimization Techniques]]
- [[YOLO — Pruning]]
- [[YOLO — Quantization by Hardware]]
- [[YOLO — Quantization]]
- [[YOLO — Synthetic Data and Flash Training App]] · also Robotics
- [[YOLO — Training Hardware and Capture Rig]] · also Robotics
- [[YOLO — Training on Different Hardware]]

## From other domains

- [[Tennis — In-Play Market Research]] · from Sports Analytics
- [[Tennis — Player and Matchup Modeling]] · from Sports Analytics
- [[Betting Apps — Behavioral and Automation Detection]] · from Cybersecurity
- [[Prior Art — Touchscreen Robots and Software Agents]] · from Robotics
- [[iOS Control — Exposing Device Controls to the Agent]] · from Robotics
- [[iOS Control — Relative Cursor Calibration and Visual Servoing]] · from Robotics

## Exchange

- **Gives others:** detection and grounding models, training recipes, edge deployment (quantization, distillation) for anyone's project.
- **Wants from others:** capture rigs and labelled data (→ Robotics); problems with clean ground truth (→ Sports Analytics); adversarial or bot-detection angles (→ Cybersecurity).

## Key decisions

- Phase 2: UGround/OmniParser zero-shot. Phase 3: ZonUI-3B fine-tuned on iPhone captures (single RTX 4090)
- YOLO nano pretrained, crop to screen, 640 imgsz, `fliplr=0`
- Free Colab T4 → used RTX 3060 12 GB (~$300)
- FP16 export by default; INT8 PTQ only if CPU-bound; skip pruning/KD
- Closed loop: flash → capture → label → tap → score → retrain

## Help wanted (all domains)

```query
[type:request] -[status:answered]
```

## Adding to the pool

- New note → put it in the folder of its **main** domain, add a link to it on this hub, and fill in `domain`, `type`, `status`, `author`, `date`. Copy the frontmatter from any existing note.
- `domain: [ml, sports]`: list **every** domain it could help. Also link it under *"From other domains"* on those hubs. That's how research crosses over.
- Need something researched? Make a note with `type: request`, `status: seed`. It shows up on Help Wanted on every hub. Pick one up by adding `claimed_by: <you>`.
- Start every note with a 3-line **TL;DR**. Domain values: `sports` · `ml` · `security` · `robotics`.
