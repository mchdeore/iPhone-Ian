# Running question log

Check here before starting new research. If your question is already listed,
read the linked notes first — don't re-research.

| Slug | Question | Status | Answer / research |
|---|---|---|---|
| `gantry-reference-build` | Cartesian XY-gantry reference build with passive spring-Z capacitive stylus | Answered | `08-xy-gantry-builds.md` — Instructables "Screen Tapping Robot" deep-dived. Y-axis/Z/controller/BOM extracted. Arduino Uno + CNC Shield V3 + GRBL recommended. |
| `microcontroller-choice` | Simplest microcontroller + firmware for 2-axis + servo gantry | Answered | `08-xy-gantry-builds.md` — Arduino Uno + CNC Shield V3 + A4988 + GRBL 1.1h. ~$14 total. Laser mode for servo control. |
| `stylus-tip-materials` | Best capacitive stylus tip for automated tapping | Answered | `02-mechanical-architecture-notes.md` — Conductive silicone > carbon-fiber > conductive foam. Ground wire mandatory. Wipe with isopropyl alcohol weekly. |
| `ios-faceid-robot` | Face ID / passkey / autofill behavior when a robot drives the phone | Answered | `07-ios-control-constraints.md` — 5 failed Face ID attempts forces passcode. Robot always uses passcode fallback. Passcode entry is standard number pad. |
| `ios-autofill-robot` | iOS autofill / password manager behavior under robot tapping | Answered | `07-ios-control-constraints.md` — Two flows: (A) credentials saved → tap suggestion → auth, (B) not saved → dismiss bar → type manually. QuickType bar is extra UI element for CV. |
| `ios-accessibility-robot` | Accessibility features (VoiceOver, Switch Control) — help or hinder? | Answered | `07-ios-control-constraints.md` — VoiceOver is a risk (changes gesture model). Disable triple-click shortcut. Don't rely on accessibility features. |
| `app-login-landscape` | App-specific login on iOS — passkey vs password in 2026 | Answered | `07-ios-control-constraints.md` — Password fallback still universal. Passkeys growing but additive. "Sign in with Apple" buttons are dead ends. 2FA hardest problem; prefer TOTP. |
| `vision-grounding-ios` | Screen→coordinate grounding when agent sees screen through camera (black box) | Answered | `06-vlm-gui-agent-survey.md` — Phase 2: UGround/OmniParser zero-shot. Phase 3: fine-tune ZonUI-3B on our camera captures. No published work on camera-photo grounding gap. |
| `vlm-gui-agents` | State of the art in VLM GUI agents (Mobile-Agent, CogAgent, OS-Atlas, etc.) | Answered | `06-vlm-gui-agent-survey.md` — Vision-only validated. Multi-agent architecture (30%+ gain). ZonUI-3B is our fine-tuning target. |
| `prompting-vs-finetuning` | Do off-the-shelf VLMs work for GUI grounding or need fine-tuning? | Answered | `06-vlm-gui-agent-survey.md` — Zero-shot for prototyping only. Fine-tuned 3B model beats large prompted models. ZonUI-3B proof: 84.9% ScreenSpot. |
| `physical-robot-agent-prior-art` | Any prior work where a robot physically interacts with a phone + VLM agent? | Answered | `06-vlm-gui-agent-survey.md` — Almost none. BrainyBot (game tapping), Robo-Harness K1 (VLM→robot, not phone-specific). This intersection is novel. |
| `yolo-efficient-dataset` | What makes an efficient YOLO training set? | Answered | `yolo-training/01-efficient-dataset.md` |
| `yolo-synthetic-data` | How to generate synthetic training data with a flash app? | Answered | `yolo-training/02-synthetic-data-and-flash-app.md` |
| `yolo-training-hardware` | Bare-minimum hardware for training YOLO? | Answered | `yolo-training/03-hardware.md` |
| `yolo-train-per-hardware` | How to train YOLO on CPU-only 16 GB / MPS / low-VRAM GPU / Pi? | Answered | `yolo-training/04-training-on-hardware.md` |
| `yolo-quantization` | How to quantize YOLO weights? | Answered | `yolo-training/05-quantization.md` |
| `flask-trainer-app` | Flask app that flashes synthetic data and requests actions to train the model | Answered | `yolo-training/06-flask-trainer-app.md` |
| `yolo-pruning` | How to prune YOLO models, and is it worth it? | Answered | `yolo-training/07-pruning.md` |
| `yolo-other-optimizations` | Other YOLO optimizations (runtime, ROI, change detection, variant) | Answered | `yolo-training/08-other-optimizations.md` |
| `grouping-methods` | Class taxonomy / detection grouping / data grouping | Answered | `yolo-training/09-grouping-methods.md` |
| `knowledge-distillation` | Should KD be used on low-VRAM hardware? | Answered | `yolo-training/10-knowledge-distillation.md` |
| `quantization-by-hardware` | Which quantizations work on which hardware/tasks? | Answered | `yolo-training/11-quantization-by-hardware.md` |
| `efficient-training-strategy` | Quickest, minimal-overhead training strategy | Answered | `yolo-training/12-efficient-training-strategy.md` |
| `expose-device-controls` | How to expose device controls to the model? | Answered | `yolo-training/13-exposing-device-controls.md` |
| `windows-public-port` | Safe, stable public port + low-latency stream on Windows | Answered | `yolo-training/14-windows-public-port-and-streaming.md` |
| `pi-input-converter` | Raspberry Pi input converter for the device | Answered | `yolo-training/15-raspberry-pi-input-converter.md` |
| `hid-vs-gantry` | Use AssistiveTouch + HID (needs one Settings toggle) or keep pure gantry? | Open | — tension between `13`/`15` and `07`; see `yolo-training/README.md` |
| `capacitive-touch-physics` | PCAP touch physics, grounding, calibration for stylus-based robot | Answered | `02-mechanical-architecture-notes.md` |
| `ai-agent-loop` | Perception→planning→action loop for phone-driving agent | Answered | `05-ai-agent-architecture-notes.md` + `06-vlm-gui-agent-survey.md` |
| `android-software-control` | Software control surfaces for Android (ADB, scrcpy, accessibility) | Answered (legacy) | `android-control-survey.md` — kept for evidence that software-only iPhone control is not viable. |
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