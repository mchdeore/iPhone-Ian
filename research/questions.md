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
| `gantry-reference-build` | Cartesian XY-gantry reference build with passive spring-Z capacitive stylus | Answered | [[mechanical/03-xy-gantry-microcontroller]] — Instructables "Screen Tapping Robot" deep-dived. Y-axis/Z/controller/BOM extracted. Arduino Uno + CNC Shield V3 + GRBL recommended. |
| `microcontroller-choice` | Simplest microcontroller + firmware for 2-axis + servo gantry | Answered | [[mechanical/03-xy-gantry-microcontroller]] — Arduino Uno + CNC Shield V3 + A4988 + GRBL 1.1h. ~$14 total. Laser mode for servo control. |
| `stylus-tip-materials` | Best capacitive stylus tip for automated tapping | Answered | [[mechanical/02-touch-physics-gantry]] — Conductive silicone > carbon-fiber > conductive foam. Ground wire mandatory. |
| `ios-faceid-robot` | Face ID / passkey / autofill behavior when a robot drives the phone | Answered | [[ios-control/01-faceid-autofill-accessibility]] — 5 failed Face ID attempts forces passcode. Robot always uses passcode fallback. |
| `ios-autofill-robot` | iOS autofill / password manager behavior under robot tapping | Answered | [[ios-control/01-faceid-autofill-accessibility]] — Two flows: (A) credentials saved → tap suggestion + auth, (B) not saved → dismiss bar → type manually. |
| `ios-accessibility-robot` | Accessibility features (VoiceOver, Switch Control) — help or hinder? | Answered | [[ios-control/01-faceid-autofill-accessibility]] — VoiceOver is a risk. Disable triple-click shortcut. |
| `app-login-landscape` | App-specific login on iOS — passkey vs password in 2026 | Answered | [[ios-control/01-faceid-autofill-accessibility]] — Password fallback still universal. Passkeys growing but additive. |
| `assistivetouch-pointer` | AssistiveTouch + HID pointer mechanics for robot control | Answered | [[ios-control/02-assistivetouch-pointer]] — Relative pointer only on iOS. Lock screen behavior, UIAccessibility API. |
| `relative-cursor-calibration` | Relative cursor calibration, dead reckoning, visual servoing | Answered | [[ios-control/03-relative-cursor-calibration]] — Visual servoing beats dead reckoning. PID control for convergence. |
| `alternative-input-paths` | Full Keyboard Access, Switch Control, Voice Control, Back Tap | Answered | [[ios-control/04-alternative-input-paths]] — FKA most promising for typing. Switch Control needs setup. Voice Control usable. |
| `vision-grounding-ios` | Screen→coordinate grounding when agent sees screen through camera (black box) | Answered | [[agent-ml/02-vlm-gui-agent-survey]] — Phase 2: UGround/OmniParser zero-shot. Phase 3: fine-tune ZonUI-3B on our captures. No published work on camera-photo grounding gap. |
| `vlm-gui-agents` | State of the art in VLM GUI agents (Mobile-Agent, CogAgent, OS-Atlas, etc.) | Answered | [[agent-ml/02-vlm-gui-agent-survey]] — Vision-only validated. Multi-agent architecture (30%+ gain). ZonUI-3B is our fine-tuning target. |
| `prompting-vs-finetuning` | Do off-the-shelf VLMs work for GUI grounding or need fine-tuning? | Answered | [[agent-ml/02-vlm-gui-agent-survey]] — Zero-shot for prototyping only. Fine-tuned 3B beats large prompted models. ZonUI-3B: 84.9% ScreenSpot. |
| `physical-robot-agent-prior-art` | Any prior work where a robot physically interacts with a phone + VLM agent? | Answered | [[agent-ml/02-vlm-gui-agent-survey]] — Almost none. This intersection is novel. |
| `yolo-efficient-dataset` | What makes an efficient YOLO training set? | Answered | [[yolo-training/01-efficient-dataset]] |
| `yolo-synthetic-data` | How to generate synthetic training data with a flash app? | Answered | [[yolo-training/02-synthetic-data-and-flash-app]] |
| `yolo-training-hardware` | Bare-minimum hardware for training YOLO? | Answered | [[yolo-training/03-hardware]] |
| `yolo-train-per-hardware` | How to train YOLO on CPU-only 16 GB / MPS / low-VRAM GPU / Pi? | Answered | [[yolo-training/04-training-on-hardware]] |
| `yolo-quantization` | How to quantize YOLO weights? | Answered | [[yolo-training/05-quantization]] |
| `flask-trainer-app` | Flask app that flashes synthetic data and requests actions to train the model | Answered | [[yolo-training/06-flask-trainer-app]] |
| `yolo-pruning` | How to prune YOLO models, and is it worth it? | Answered | [[yolo-training/07-pruning]] |
| `yolo-other-optimizations` | Other YOLO optimizations (runtime, ROI, change detection, variant) | Answered | [[yolo-training/08-other-optimizations]] |
| `grouping-methods` | Class taxonomy / detection grouping / data grouping | Answered | [[yolo-training/09-grouping-methods]] |
| `knowledge-distillation` | Should KD be used on low-VRAM hardware? | Answered | [[yolo-training/10-knowledge-distillation]] |
| `quantization-by-hardware` | Which quantizations work on which hardware/tasks? | Answered | [[yolo-training/11-quantization-by-hardware]] |
| `efficient-training-strategy` | Quickest, minimal-overhead training strategy | Answered | [[yolo-training/12-efficient-training-strategy]] |
| `expose-device-controls` | How to expose device controls to the model? | Answered | [[yolo-training/13-exposing-device-controls]] |
| `windows-public-port` | Safe, stable public port + low-latency stream on Windows | Answered | [[yolo-training/14-windows-public-port-and-streaming]] |
| `pi-input-converter` | Raspberry Pi input converter for the device | Answered | [[yolo-training/15-raspberry-pi-input-converter]] |
| `hid-vs-gantry` | Use AssistiveTouch + HID (needs one Settings toggle) or keep pure gantry? | Open | — tension between [[yolo-training/13-exposing-device-controls]], [[yolo-training/15-raspberry-pi-input-converter]], [[ios-control/01-faceid-autofill-accessibility]]; see [[Timeline]] open decisions |
| `capacitive-touch-physics` | PCAP touch physics, grounding, calibration for stylus-based robot | Answered | [[mechanical/02-touch-physics-gantry]] |
| `ai-agent-loop` | Perception→planning→action loop for phone-driving agent | Answered | [[agent-ml/01-agent-architecture]] + [[agent-ml/02-vlm-gui-agent-survey]] |
| `android-software-control` | Software control surfaces for Android (ADB, scrcpy, accessibility) | Answered (legacy) | [[android-control-survey]] — kept for evidence that software-only iPhone control is not viable. |
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