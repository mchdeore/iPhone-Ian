# iPhone-Ian — Detailed Pipeline

Step-by-step breakdown of `PLAN.md`, wired into Marc's `research/` vault and the hardware design in `aria/hardware-concept-v2.md`. No hard dates; order and gates matter, not the calendar.

Legend: **[A]** Aria / hardware · **[M]** Marc / software+model · **[S]** shared.

---

## Stage 2 — Design (current)

- [A] Base-plate CAD, slotted holes → JLCCNC quote.
- [A] Printable parts: toolhead + lever + stylus sleeve, end blocks, idler posts, motor clamps, phone slots, cable guides, controller box.
- [A] Wiring plan from the MKS DLC32 / TMC2209 docs: servo pin, power input, motor + endstop pinout — so "confirm on arrival" becomes "known now."
- [A] FluidNC `config.yaml` draft: `noradio` build, CoreXY kinematics, RC-servo Z, soft limits. → backs `research/Robotics/Gantry — FluidNC Control Interface`.
- [S] Lock the robot interface: `move(x,y) / tap() / down() / up() / home()` over USB serial, mm in the machine frame (concept doc §3.1). Marc codes against a **fake robot** stub implementing this now.
- [S] Finalize BOM, work-sourcing, split, place the order (`BOM.md`).

**Open Qs to close on a call:** cases vs bare phones (slot width + spring travel); which offline app is the reference target.

---

## Stage 3 — Build & bring-up ("get it moving") · [A] lead

1. Print all parts; heat-set inserts in.
2. Assemble frame, rails, CoreXY belts; motor pulleys hub-up; idlers clamped top+bottom.
3. Flash FluidNC `noradio`; load `config.yaml`.
4. Wire motors, endstops, servo (via Mini560 PRO 5 V), 24 V in.
5. Home (`$H`); square the axes; set soft limits = phone-row rectangle.
6. Mount the grounded spring-stylus; **ground wire to controller GND** (mandatory for PCAP — `research/Robotics/Gantry — Capacitive Touch Physics`).
7. Tune TMC2209 StealthChop for quiet; set feed/accel.

**Gate:** a hand-sent `move`+`tap` lands a registered touch on the phone. First tap on 1 phone.

---

## Stage 4 — Simple test app · [M] lead, [A] calibration rig

Backs `research/System Design — Bare-Minimum iPhone Setup (MVP)` and `— Drag, Tap and Verify Primitives`.

1. [M] `capture.py` — pull frames from the phone (USB screen capture to the PC).
2. [S] `calib.py` — tap known points, fit screen-px → machine-mm homography. With screen capture the pixels are exact (`research/Robotics/Rig — Camera-to-Screen Calibration`).
3. [M] `robot.py` — the interface over serial (soft limits = screen rect).
4. [M] minimal harness: show a target, command a tap/drag, verify from the next frame; log every action as JSONL.
5. [A] printed calibration fixture + repeatability check (tap a grid, measure error).

**Gate:** robot hits pointed-to targets ≥ ~19/20 across the screen; drags move reliably; every action logged.

---

## Stage 5 — Train the model (local, on Marc's PC) · [M] lead

Compute: multi-year gaming CPU, 32 GB DDR4, **GTX 1080 = 8 GB VRAM**, M.2 SSD. The 8 GB VRAM is the hard limit.

- [M] Model choice must fit 8 GB. QLoRA/4-bit on a **small** VLM, or a compact detector (YOLO) for UI elements, offloading to RAM/SSD as needed. Marc's `research/Machine Learning — QLoRA Fine-Tuning a Small VLM on 12 GB` assumes 12 GB — **re-scope for 8 GB** (smaller base, lower res, gradient checkpointing, or train UI detection only and keep reasoning on a prompted model).
- [M] Perception: template-match or a small YOLO on captured frames (`research/System Design — Reading Cards from the Screen`, `research/.../YOLO`).
- [M] Data: capture runs from Stage 4; synthetic + real frames (`research/.../YOLO — Efficient Dataset Recipe`, `— Synthetic Data`).
- [S] **Natural interaction quality** = taps/drags with realistic timing and smooth motion, so actions are reliable and non-jerky. This is a *quality/robustness* goal (and good robotics), **not** a bot-detection-evasion goal — see guardrails. Physical side (motion smoothing, dwell/hold timing, touch telemetry) is [A]; policy side is [M].
- [M] Loop: screen → perceive → decide → plan → act → verify, state machine as source of truth (`research/System Design — Card-Playing Gantry Rig Architecture`, `— Reliability, Error Recovery`).

**Gate:** the model drives the robot through the Stage-4 app unattended.

---

## Stage 6 — Teach it poker (parallel with Stage 5) · [S], game theory [M]

Backs `research/Math/Game Theory — *` (CFR, GTO vs exploitative, Poker AI milestones).

- Rules/state engine for the chosen poker variant.
- Decision engine: CFR / counterfactual regret for the computer opponent; betting conventions, hand strength, position.
- Validate in pure simulation before any screen.

**Gate:** decision engine plays correctly in sim (beats a greedy baseline by a clear margin).

---

## Stage 7 — Offline poker test · [S]

- Install an **offline** poker game on the test phone (no real money, no accounts).
- Run trained model (5) + engine (6) + robot through full games.
- Measure: win rate vs the AI, action accuracy, taps/hand, failures, recovery.

**Gate:** completes games unattended; we have real performance numbers to optimize against.

---

## Stage 8 — Optimize · [S]

- [M] Model: errors from Stage 7 → retrain/prompt-tune; speed vs accuracy on the 1080.
- [A] Motion: faster safe feed/accel, quieter, tighter calibration; 2nd-phone throughput.
- [S] Reliability: RECOVER ladder, timeouts, SAFE_STOP, hours-long unattended runs (`research/System Design — Reliability`).

**Gate:** accuracy, speed, and stability are good enough that we'd trust it on the real task.

---

## Stage 9 — Commissioned app · [S]

Only after Stage 8. Test the authorized target app **within its ToS and the engagement agreement**.

- Confirm the authorization/ToS scope in writing before running it.
- Carry all guardrails (below). Keep runs logged.
- Detection stacks are *understood* from `research/Cybersecurity` (mapping only); we do not attempt to defeat them.

**Gate:** the agreed test runs and is reported.

---

## Stage 10 — Scale & refine (ongoing) · [A] hardware

- 2nd phone slot live; then more phones (longer rails, set `N_PHONES`).
- v3: bent-aluminium tray/bridge, quieter drive, slimmer.
- Drawer enclosure + 24/7 charging/thermal check.

---

## Guardrails (every stage)
- Authorized/commissioned and offline/play-money targets only. **No real-money multiplayer poker.**
- **No detection-evasion work** (anti-bot, geofencing, biometric/identity spoofing). Detection is mapped to understand risk, never bypassed. "Human-like" = interaction quality, not disguise.
- Never train against a judge on apps that move money or send messages (`research/.../RL — Rewards and Success Detection`).
- Test phones: no real credentials/payments/messaging; notifications off; dedicated test Apple ID.
- Controller USB-only, Wi-Fi off (`noradio`); remote access via the host only.
