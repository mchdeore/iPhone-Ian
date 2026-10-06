---
tags: [development]
---

# == Development Central ==

Project timeline and active build progress. All development work lives here.

## Active work

- [[CAD Build Progress — Gantry Parts]] — 4 of 14 parts done, build123d pipeline working

## Phase 0 — Research close-out

- [x] XY-gantry reference build found
- [x] iOS constraints: Face ID, autofill, accessibility
- [x] AssistiveTouch + HID pointer mechanics
- [x] Relative cursor calibration
- [x] Alternative iOS input paths
- [x] VLM GUI agent literature survey
- [x] YOLO training: full pipeline researched
- [x] Device control API + networking
- [ ] Decide: HID keyboard vs pure gantry for typing
- [ ] Pick first target iPhone model

## Phase 1 — Mechanical prototype

- [ ] 3D-print robot parts
- [ ] Source BOM: Arduino Uno + CNC Shield + A4988 + NEMA 17 + MG90S
- [ ] Add grounding wire (Arduino GND to stylus tip)
- [ ] Rig iPhone mount + overhead camera
- [ ] Flash GRBL 1.1h, configure laser mode
- [ ] Calibration: camera → screen → gantry

## Phase 2 — Perception + control

- [ ] UGround/OmniParser zero-shot on iPhone captures
- [ ] Tap/swipe/type primitives via GRBL
- [ ] Calibration pipeline

## Phase 3 — Training rig

- [ ] Flask flash app with ArUco fiducials
- [ ] Capture ~500 frames, single class
- [ ] Train YOLO nano on Colab T4
- [ ] Fine-tune ZonUI-3B on iPhone captures

## Phase 4 — Commands + credentials

- [ ] Intent vocabulary: login, enter, exit, navigate
- [ ] Credential vault integration
- [ ] End-to-end login test with 2FA