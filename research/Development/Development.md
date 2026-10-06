---
tags: [development]
---

# Development

Project timeline and status. All planning lives here.

## Phase 0 — Research close-out

- [x] XY-gantry reference build found — Instructables "Screen Tapping Robot"
- [x] iOS Face ID / autofill / accessibility constraints
- [x] AssistiveTouch + HID pointer mechanics
- [x] Relative cursor calibration
- [x] Alternative iOS input paths
- [x] VLM GUI agent literature survey
- [x] YOLO training: dataset, synthetic data, hardware
- [x] YOLO: quantization, pruning, distillation, optimizations
- [x] YOLO closed-loop Flask trainer
- [x] Device control API + networking
- [ ] Decide: HID keyboard vs pure gantry for typing
- [ ] Pick first target iPhone model

## Phase 1 — Mechanical prototype

- [ ] 3D-print Instructables robot parts
- [ ] Source BOM: Arduino Uno + CNC Shield + A4988 + NEMA 17 + MG90S
- [ ] Add grounding wire (Arduino GND to stylus tip)
- [ ] Rig iPhone mount + overhead camera
- [ ] Flash GRBL 1.1h, configure laser mode
- [ ] Calibration: camera → screen → gantry

## Phase 2 — Perception + control

- [ ] UGround/OmniParser zero-shot on iPhone camera captures
- [ ] Implement tap/swipe/type primitives via GRBL
- [ ] Build calibration pipeline

## Phase 3 — Training rig

- [ ] Flask flash app with ArUco fiducials
- [ ] Capture Phase 0: ~500 frames, single class
- [ ] Train YOLO nano on Colab T4
- [ ] Fine-tune ZonUI-3B on iPhone captures

## Phase 4 — Commands + credentials

- [ ] Intent vocabulary: login, enter, exit, navigate, type, tap
- [ ] Credential vault integration
- [ ] End-to-end login test with 2FA