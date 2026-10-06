---
tags: [timeline, project-management]
status: live
date: 2026-10-06
related:
  - "[[Home]]"
  - "[[../specs/00-charter]]"
---

# Project Timeline

Living document. Update checkboxes as work progresses. Each phase links to the research that informed it and the specs that implement it.

---

## Phase 0 — Research close-out

**Goal:** answer every open question before buying parts.

- [x] Cartesian XY-gantry reference build found → [[mechanical/03-xy-gantry-microcontroller]]
- [x] iOS Face ID / autofill / accessibility constraints → [[ios-control/01-faceid-autofill-accessibility]]
- [x] AssistiveTouch + HID pointer mechanics → [[ios-control/02-assistivetouch-pointer]]
- [x] Relative cursor calibration → [[ios-control/03-relative-cursor-calibration]]
- [x] Alternative iOS input paths → [[ios-control/04-alternative-input-paths]]
- [x] VLM GUI agent literature survey → [[agent-ml/02-vlm-gui-agent-survey]]
- [x] YOLO training: dataset, synthetic data, hardware → [[yolo-training/README]]
- [x] YOLO training: quantization, pruning, distillation, optimizations → [[yolo-training/README]]
- [x] YOLO closed-loop Flask trainer → [[yolo-training/06-flask-trainer-app]]
- [x] Device control API + networking → [[yolo-training/13-exposing-device-controls]], [[yolo-training/14-windows-public-port-and-streaming]]
- [ ] **Decide: HID keyboard for typing vs pure gantry-only** — tension between [[yolo-training/13-exposing-device-controls]], [[yolo-training/15-raspberry-pi-input-converter]], [[ios-control/04-alternative-input-paths]]. Needs a decision in [[../specs/]].
- [ ] **Decide: is the black-box constraint hard?** (charter §4 assumption check)
- [ ] **Pick first target iPhone model(s)** — affects mount design and calibration

---

## Phase 1 — Mechanical prototype

**Goal:** build the thing, make it tap reliably.

- [ ] 3D-print Instructables "Screen Tapping Robot" parts
- [ ] Source BOM: Arduino Uno + CNC Shield V3 + A4988 + NEMA 17 + MG90S servo
- [ ] Add grounding path (wire from Arduino GND to stylus tip)
- [ ] Rig fixed iPhone mount + overhead camera
- [ ] Flash GRBL 1.1h, configure laser mode for servo
- [ ] Nail calibration routine: camera → screen → gantry
- [ ] Validate: tap a known grid of points, measure error

**Research backing:** [[mechanical/02-touch-physics-gantry]], [[mechanical/03-xy-gantry-microcontroller]], [[ios-control/01-faceid-autofill-accessibility]]

**Spec:** [[../specs/01-hardware]]

---

## Phase 2 — Perception + control loop

**Goal:** off-the-shelf VLM sees the screen, robot taps where it's told.

- [ ] Set up overhead camera with locked focus/exposure
- [ ] UGround / OmniParser zero-shot on iPhone camera captures
- [ ] Implement tap/swipe/type primitives against GRBL gantry
- [ ] Build calibration: camera pixel → screen coordinate → gantry G-code
- [ ] Test: "tap the Settings icon" end-to-end

**Research backing:** [[agent-ml/02-vlm-gui-agent-survey]], [[agent-ml/01-agent-architecture]], [[ios-control/03-relative-cursor-calibration]]

**Spec:** [[../specs/02-firmware-and-software]]

---

## Phase 3 — Training rig

**Goal:** collect our own data, fine-tune a grounding model.

- [ ] Build Flask flash app (ArUco fiducials, randomized targets, frame-ID sync)
- [ ] Capture Phase 0: ~500 frames, single class, 4–6 lighting setups
- [ ] Train YOLO nano on Colab T4; validate on real iOS captures
- [ ] Capture UI vocabulary dataset (button, text_field, icon, keyboard_key, etc.)
- [ ] Fine-tune ZonUI-3B on our iPhone camera captures
- [ ] Close the loop: tap → detect error → recalibrate → retry

**Research backing:** [[yolo-training/01-efficient-dataset]], [[yolo-training/02-synthetic-data-and-flash-app]], [[yolo-training/12-efficient-training-strategy]], [[agent-ml/02-vlm-gui-agent-survey]]

**Spec:** [[../specs/02-firmware-and-software]] §5

---

## Phase 4 — Commands + credentials

**Goal:** say `login` or `enter`, robot does it, secrets handled safely.

- [ ] Intent vocabulary: `login`, `enter`, `exit`, `navigate`, `type`, `tap`
- [ ] Credential vault integration (macOS Keychain / 1Password CLI / age/sops)
- [ ] Security: no secrets in logs, screenshots, or training data
- [ ] Test: `login bank-app` end-to-end with 2FA handling

**Research backing:** [[ios-control/01-faceid-autofill-accessibility]] §App login landscape

**Spec:** [[../specs/02-firmware-and-software]], [[../specs/00-charter]] §6

---

## Open decisions

| Decision | Blocked by | Impact |
|---|---|---|
| Pure gantry vs HID keyboard for typing | Phase 0 decision needed | Changes Phase 1 BOM, Phase 2 primitives |
| Black-box constraint hard? | Phase 0 decision needed | If relaxed, XCUITest path is cheaper |
| Target iPhone model | Phase 0 decision needed | Mount design, screen size calibration |
| 2FA strategy (TOTP vs SMS) | Phase 4 | Credential vault design |