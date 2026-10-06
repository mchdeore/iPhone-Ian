---
tags: [questions, project-management]
status: live
date: 2026-10-06
related:
  - "[[Home]]"
  - "[[Timeline]]"
---

# Running question log

Check here before starting new research. If your question is already listed,
read the linked notes first — don't re-research.

| Slug | Question | Status | Answer / research |
|---|---|---|---|
| `gantry-reference-build` | Cartesian XY-gantry reference build with passive spring-Z capacitive stylus | Answered | [[XY Gantry Builds and Microcontroller Choice]] — Instructables "Screen Tapping Robot" deep-dived. Y-axis/Z/controller/BOM extracted. Arduino Uno + CNC Shield V3 + GRBL recommended. |
| `microcontroller-choice` | Simplest microcontroller + firmware for 2-axis + servo gantry | Answered | [[XY Gantry Builds and Microcontroller Choice]] — Arduino Uno + CNC Shield V3 + A4988 + GRBL 1.1h. ~$14 total. Laser mode for servo control. |
| `stylus-tip-materials` | Best capacitive stylus tip for automated tapping | Answered | [[Capacitive Touch Physics and Gantry Architecture]] — Conductive silicone > carbon-fiber > conductive foam. Ground wire mandatory. |
| `ios-faceid-robot` | Face ID / passkey / autofill behavior when a robot drives the phone | Answered | [[iOS Control Constraints — Face ID, Autofill, Accessibility]] — 5 failed Face ID attempts forces passcode. Robot always uses passcode fallback. |
| `ios-autofill-robot` | iOS autofill / password manager behavior under robot tapping | Answered | [[iOS Control Constraints — Face ID, Autofill, Accessibility]] — Two flows: (A) credentials saved → tap suggestion + auth, (B) not saved → dismiss bar → type manually. |
| `ios-accessibility-robot` | Accessibility features (VoiceOver, Switch Control) — help or hinder? | Answered | [[iOS Control Constraints — Face ID, Autofill, Accessibility]] — VoiceOver is a risk. Disable triple-click shortcut. |
| `app-login-landscape` | App-specific login on iOS — passkey vs password in 2026 | Answered | [[iOS Control Constraints — Face ID, Autofill, Accessibility]] — Password fallback still universal. Passkeys growing but additive. |
| `assistivetouch-pointer` | AssistiveTouch + HID pointer mechanics for robot control | Answered | [[AssistiveTouch Pointer Mechanics for Robot Control]] — Relative pointer only on iOS. Lock screen behavior, UIAccessibility API. |
| `relative-cursor-calibration` | Relative cursor calibration, dead reckoning, visual servoing | Answered | [[Relative Cursor Calibration and Visual Servoing]] — Visual servoing beats dead reckoning. PID control for convergence. |
| `alternative-input-paths` | Full Keyboard Access, Switch Control, Voice Control, Back Tap | Answered | [[Alternative iOS Accessibility Input Paths]] — FKA most promising for typing. Switch Control needs setup. Voice Control usable. |
| `vision-grounding-ios` | Screen→coordinate grounding when agent sees screen through camera (black box) | Answered | [[VLM GUI Agents and Vision Grounding Survey]] — Phase 2: UGround/OmniParser zero-shot. Phase 3: fine-tune ZonUI-3B on our captures. No published work on camera-photo grounding gap. |
| `vlm-gui-agents` | State of the art in VLM GUI agents (Mobile-Agent, CogAgent, OS-Atlas, etc.) | Answered | [[VLM GUI Agents and Vision Grounding Survey]] — Vision-only validated. Multi-agent architecture (30%+ gain). ZonUI-3B is our fine-tuning target. |
| `prompting-vs-finetuning` | Do off-the-shelf VLMs work for GUI grounding or need fine-tuning? | Answered | [[VLM GUI Agents and Vision Grounding Survey]] — Zero-shot for prototyping only. Fine-tuned 3B beats large prompted models. ZonUI-3B: 84.9% ScreenSpot. |
| `physical-robot-agent-prior-art` | Any prior work where a robot physically interacts with a phone + VLM agent? | Answered | [[VLM GUI Agents and Vision Grounding Survey]] — Almost none. This intersection is novel. |
| `yolo-efficient-dataset` | What makes an efficient YOLO training set? | Answered | [[YOLO — Efficient Dataset Recipe]] |
| `yolo-synthetic-data` | How to generate synthetic training data with a flash app? | Answered | [[YOLO — Synthetic Data and Flash Training App]] |
| `yolo-training-hardware` | Bare-minimum hardware for training YOLO? | Answered | [[YOLO — Training Hardware and Capture Rig]] |
| `yolo-train-per-hardware` | How to train YOLO on CPU-only 16 GB / MPS / low-VRAM GPU / Pi? | Answered | [[YOLO — Training on Different Hardware]] |
| `yolo-quantization` | How to quantize YOLO weights? | Answered | [[YOLO — Quantization]] |
| `flask-trainer-app` | Flask app that flashes synthetic data and requests actions to train the model | Answered | [[YOLO — Flask Closed-Loop Trainer App]] |
| `yolo-pruning` | How to prune YOLO models, and is it worth it? | Answered | [[YOLO — Pruning]] |
| `yolo-other-optimizations` | Other YOLO optimizations (runtime, ROI, change detection, variant) | Answered | [[YOLO — Other Optimization Techniques]] |
| `grouping-methods` | Class taxonomy / detection grouping / data grouping | Answered | [[YOLO — Detection Grouping and Class Taxonomy]] |
| `knowledge-distillation` | Should KD be used on low-VRAM hardware? | Answered | [[YOLO — Knowledge Distillation]] |
| `quantization-by-hardware` | Which quantizations work on which hardware/tasks? | Answered | [[YOLO — Quantization by Hardware]] |
| `efficient-training-strategy` | Quickest, minimal-overhead training strategy | Answered | [[YOLO — Efficient Training Strategy]] |
| `expose-device-controls` | How to expose device controls to the model? | Answered | [[YOLO — Exposing Device Controls to Model]] |
| `windows-public-port` | Safe, stable public port + low-latency stream on Windows | Answered | [[YOLO — Windows Public Port and Streaming]] |
| `pi-input-converter` | Raspberry Pi input converter for the device | Answered | [[YOLO — Raspberry Pi Input Converter]] |
| `hid-vs-gantry` | Use AssistiveTouch + HID (needs one Settings toggle) or keep pure gantry? | Open | — tension between [[YOLO — Exposing Device Controls to Model]], [[YOLO — Raspberry Pi Input Converter]], [[iOS Control Constraints — Face ID, Autofill, Accessibility]]; see [[Timeline]] open decisions |
| `capacitive-touch-physics` | PCAP touch physics, grounding, calibration for stylus-based robot | Answered | [[Capacitive Touch Physics and Gantry Architecture]] |
| `ai-agent-loop` | Perception→planning→action loop for phone-driving agent | Answered | [[AI Agent Architecture and Perception Loop]] + [[VLM GUI Agents and Vision Grounding Survey]] |
| `android-software-control` | Software control surfaces for Android (ADB, scrcpy, accessibility) | Answered (legacy) | [[Android Software Control Survey (Legacy)]] — kept for evidence that software-only iPhone control is not viable. |
| `iphone-model-target` | Which specific iPhone model(s) are the first targets? | Open | — affects mount design and screen size calibration |
| `2fa-handling` | How to handle 2FA codes (SMS, TOTP, email) from a robot? | Open | — TOTP preferred (offline computation). SMS is hardest case. |
| `human-typing-speed` | Does robot need to simulate human typing speed to avoid bot detection? | Open | — some apps may throttle or flag automated input |
| `retry-error-recovery` | Retry/error-recovery strategy when a tap misses? | Open | — need to define loop: retry count, fallback actions, timeout behavior |
| `dynamic-content-handling` | How to handle loading spinners, animations, popups during agent operation? | Open | — timing, OCR-based state detection, wait conditions |

---

## How to use

1. Before researching something, scan this table for a matching slug or keyword.
2. If you find a match, read the linked research notes. Only research what's still missing.
3. When you start researching a new question, add a row with status `Researching`.
4. When done, update the status to `Answered` and link the research file.
5. If a question turns out to be the wrong question, mark it `Stale` with a one-line explanation — don't delete it, someone else will wonder the same thing later.