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

- [x] Cartesian XY-gantry reference build found → [[XY Gantry Builds and Microcontroller Choice]]
- [x] iOS Face ID / autofill / accessibility constraints → [[iOS Control Constraints — Face ID, Autofill, Accessibility]]
- [x] AssistiveTouch + HID pointer mechanics → [[AssistiveTouch Pointer Mechanics for Robot Control]]
- [x] Relative cursor calibration → [[Relative Cursor Calibration and Visual Servoing]]
- [x] Alternative iOS input paths → [[Alternative iOS Accessibility Input Paths]]
- [x] VLM GUI agent literature survey → [[VLM GUI Agents and Vision Grounding Survey]]
- [x] YOLO training: dataset, synthetic data, hardware → [[YOLO — Efficient Dataset Recipe]]
- [x] YOLO training: quantization, pruning, distillation, optimizations → [[YOLO — Efficient Dataset Recipe]]
- [x] YOLO closed-loop Flask trainer → [[YOLO — Flask Closed-Loop Trainer App]]
- [x] Device control API + networking → [[YOLO — Exposing Device Controls to Model]], [[YOLO — Windows Public Port and Streaming]]
- [ ] **Decide: HID keyboard for typing vs pure gantry-only** — tension between [[YOLO — Exposing Device Controls to Model]], [[YOLO — Raspberry Pi Input Converter]], [[Alternative iOS Accessibility Input Paths]]. Needs a decision in [[../specs/]].
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

**Research backing:** [[Capacitive Touch Physics and Gantry Architecture]], [[XY Gantry Builds and Microcontroller Choice]], [[iOS Control Constraints — Face ID, Autofill, Accessibility]]

**Spec:** [[../specs/01-hardware]]

---

## Phase 2 — Perception + control loop

**Goal:** off-the-shelf VLM sees the screen, robot taps where it's told.

- [ ] Set up overhead camera with locked focus/exposure
- [ ] UGround / OmniParser zero-shot on iPhone camera captures
- [ ] Implement tap/swipe/type primitives against GRBL gantry
- [ ] Build calibration: camera pixel → screen coordinate → gantry G-code
- [ ] Test: "tap the Settings icon" end-to-end

**Research backing:** [[VLM GUI Agents and Vision Grounding Survey]], [[AI Agent Architecture and Perception Loop]], [[Relative Cursor Calibration and Visual Servoing]]

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

**Research backing:** [[YOLO — Efficient Dataset Recipe]], [[YOLO — Synthetic Data and Flash Training App]], [[YOLO — Efficient Training Strategy]], [[VLM GUI Agents and Vision Grounding Survey]]

**Spec:** [[../specs/02-firmware-and-software]] §5

---

## Phase 4 — Commands + credentials

**Goal:** say `login` or `enter`, robot does it, secrets handled safely.

- [ ] Intent vocabulary: `login`, `enter`, `exit`, `navigate`, `type`, `tap`
- [ ] Credential vault integration (macOS Keychain / 1Password CLI / age/sops)
- [ ] Security: no secrets in logs, screenshots, or training data
- [ ] Test: `login bank-app` end-to-end with 2FA handling

**Research backing:** [[iOS Control Constraints — Face ID, Autofill, Accessibility]] §App login landscape

**Spec:** [[../specs/02-firmware-and-software]], [[../specs/00-charter]] §6

---

## Open decisions

| Decision | Blocked by | Impact |
|---|---|---|
| Pure gantry vs HID keyboard for typing | Phase 0 decision needed | Changes Phase 1 BOM, Phase 2 primitives |
| Black-box constraint hard? | Phase 0 decision needed | If relaxed, XCUITest path is cheaper |
| Target iPhone model | Phase 0 decision needed | Mount design, screen size calibration |
| 2FA strategy (TOTP vs SMS) | Phase 4 | Credential vault design |