# Firmware, Software & Machine-Learning Specification

**Scope:** everything that runs as code — on-robot **firmware**, the **host**
control software, **computer vision**, the **AI agent / ML**, command handling, and
credential security. Physical build lives in
[`01-hardware.md`](01-hardware.md).

> Guiding principle (see `00-charter.md`): the mechanics are commodity. The novel
> work is **calibration** (camera→screen→gantry) and the **command→action agent
> with safe credential handling**. Everything else, reuse or fork.
> All links cited in §10.

---

## 1. Layered architecture & the three firmware routes

```
 command ("login")           ┌─────────────── HOST (HomeLab box) ───────────────┐
        │                     │  Agent (planning)                                 │
        ▼                     │   ├─ Perception: camera → OCR/VLM/grounding       │
 [ Agent / planner ] ─────────┤   ├─ Calibration: screen px → gantry XY (homog.)  │
        │  target XY + tap    │   ├─ Credential vault (secrets)                   │
        ▼                     │   └─ Motion client → serial/USB → controller      │
 [ Host motion client ]  ─────┘                                                   
        │  G-code / protocol
        ▼
 [ Controller firmware ] → stepper drivers + servo → MOTION → stylus taps glass
```

**Firmware route decides how much we build vs. reuse:**

| Route | Firmware | Host does | Reuse | Verdict |
|---|---|---|---|---|
| **A. GRBL/FluidNC** ⭐ | Off-the-shelf CNC firmware; **Cartesian kinematics built in** | Stream G-code | Highest — no firmware to write | **Recommended** for our Cartesian gantry |
| **B. Firmata (Tapster-style)** | StandardFirmata (dumb pin I/O) | ALL logic incl. kinematics | Reuse Tapster's host stack directly | Best if we lift Tapster wholesale |
| **C. Custom Arduino** | AccelStepper + ServoEasing + custom serial | Send high-level cmds | Libraries only | Most control, most work — avoid unless needed |

Because our machine is **Cartesian**, GRBL maps trivially (X→X motor, Y→Y motor,
Z-servo→tap); Route A means **zero custom firmware**.

---

## 2. Reuse from Tapsterbot / Tappy (the "steal the firmware" plan)

**Reality check on what's open:** Tapster's *on-device firmware* is just
**StandardFirmata** (open, shipped with the Arduino IDE) — the intelligence
(delta inverse-kinematics, calibration, control API, Appium bridge) lives in its
**open-source Node.js host software**. So "steal the firmware" in practice means
**reuse the open host stack + the Firmata approach**, not a secret sauce binary.

**Directly reusable from Tapster/Tappy:**
- ⭐ **Browser-based calibration** — load a page on the phone, touch registers
  screen coords at the host; solves the screen↔robot mapping without installing
  anything on the phone. (Tappy: `http://server_ip/cal`.) [guntiss/tappy]
- ⭐ **Grounding requirement** baked into their setup notes — *"stylus must be
  grounded to arduino GND"* (see hardware spec §3). [guntiss/tappy]
- **Control server + API** and **Appium integration** (drive it like a test rig).
- **Record-and-play** tool for scripted sequences. [merinsTDL/tappy]
- Delta **inverse-kinematics** — *only if we ever go delta*; our Cartesian gantry
  doesn't need it (GRBL handles motion). Standalone lib if needed:
  tinkersprojects/Delta-Kinematics-Library.

**Repos:** hugs/tapsterbot (original) · pylapp/tapsterbot (maintained fork) ·
merinsTDL/tappy · guntiss/tappy · DeMaCS-UNICAL/tappy-original ·
DeMaCS-UNICAL/BrainyBot (CV taps a phone to *play games* — closest full
perception→tap precedent).

**Plan:** Route A firmware (GRBL) for motion + steal Tapster's **calibration page**
and **control/record ideas** at the host layer.

---

## 3. Firmware building blocks (by route)

### Route A — GRBL / FluidNC (recommended)
- **GRBL** (Arduino Uno/Atmega328) — https://github.com/gnea/grbl
- **FluidNC** (ESP32; YAML config, WiFi/BT, web UI) — https://github.com/bdring/FluidNC
- **Servo-Z "pen up/down" = our tap** (already solved):
  bdring/Grbl_Pen_Servo · vankesteren/grbl-servo · ArcaEge/grbl-28byj-48-pen-plotter-servo

### Route C — custom Arduino libraries (only if we skip GRBL)
- **AccelStepper** (Mike McCauley) — the standard accel/decel stepper lib.
- **SpeedyStepper** (Stan-Reifel) — speed-optimized alternative.
- **StepperDriver** (laurb9) — A4988/DRV8825/DRV8834/DRV8880, accel + microstep.
- **ServoEasing** (ArminJo) — smooth servo motion (linear/cubic/bounce…), works with
  the Arduino Servo lib **and PCA9685** — ideal for controlled tap depth.
- **PCA9685** 16-ch PWM driver + Adafruit_PWMServoDriver — if we later want multiple
  servos (e.g. multi-touch with two stylus tips).

### Stepper drivers (hardware interface)
- **A4988** (up to 1/16 microstep) / **DRV8825** (up to 1/32) on a CNC-shield —
  standard, cheap. RobTillaart/DRV8825 lib for direct control if needed.

---

## 4. Host-side control (HomeLab box → controller)

- ⭐ **Programmatic (for the agent):** thin Python **pyserial** G-code streamers
  with flow control — Sam-Freitas/python_to_GRBL · jonkensta gist (buffer-aware
  streaming). This is what the agent calls to move + tap.
- **Manual jog / calibration GUI:** Universal G-Code Sender (winder/UGS, Java) ·
  bCNC (Python, runs on a Pi) · gSender (Sienci, grblHAL).

Motion client exposes primitives to the agent: `move(x,y)`, `tap()`, `swipe(...)`,
`type(text)` (per-key taps). Under the hood these emit G-code (Route A).

### 4.1 "Can the Pi/Arduino just accept simple code inputs?" — yes ⭐

This is the split you want: **dumb, deterministic motors; smart host.** Two proven,
simple ways to make an Arduino/ESP32 accept coordinate commands from a Raspberry Pi
or PC:

1. **Firmata + pyFirmata / Johnny-Five (Tapster's exact approach).** Flash
   **StandardFirmata** (dumb pin/servo I/O) to the Arduino; the **Pi/host** runs a
   few lines of Python (**pyFirmata**) or Node (**Johnny-Five**) and commands the
   servos/steppers directly. Tapster drives it literally like this — a REPL where
   `go(0,0,-140)` moves the effector. The Arduino holds **no logic**; the host code
   + ML decide everything. *(Caveat: no on-board logic; motion timing depends on the
   host + USB link — perfectly fine for tapping.)*
2. **GRBL / FluidNC + G-code (recommended once we use steppers).** Flash GRBL; the
   host sends plain text lines — `G0 X100 Y50` to move, then a servo-Z line to tap.
   The controller handles stepping/acceleration **deterministically on-device**.

**Minimal input contract — start here (the "simple thing we know will work"):**

```
host → controller:   move(x, y)        # go to screen/robot coordinate
                     tap()             # Z down, brief dwell, Z up
                     (later) down()/up()  # for press-hold, swipe, drag
```

That is the **entire** firmware interface. Everything hard — *where* to tap and
*reading* the screen — lives in host code + ML (§5–§7), never in the firmware. Build
this dumb interface first, prove it moves to a coordinate and taps reliably, then let
the vision/agent stack layer on top.

---

## 5. Computer vision — camera → screen coordinates

The phone is a black box; the overhead camera is the only sensor. Both sub-problems
are stock **OpenCV**:

- ⭐ **Homography / four-point perspective warp** — reproject the angled camera view
  into a flat screen rectangle, then map screen px → gantry XY. This IS the
  calibration transform. `cv2.findHomography` / `getPerspectiveTransform`.
  - Tutorial (UI-scraping use case): [TheLinuxCode perspective warp]
  - Homography-from-reference-image: RaubCamaioni/OpenCV_Position
- **Camera intrinsic calibration** (undistort first) — OpenCV calib3d tutorial.
- **Auto-detect the phone rectangle** — OpenCV forum "Detecting a smartphone screen".

**CV-robot reference architectures (CV → serial → motion), study for the pattern:**
- Shen-Kev/**Petri-Dish-Gantry** — vision tracking drives a gantry (general-purpose
  tracking+motion arch).
- tunmaker/**Delta-Robot-Project** — image processing (EmguCV) → Arduino over USB
  serial, "like a CNC machine".
- himadripoddar/**Pick-and-Place-3-DOF** (OpenCV color detect) ·
  Mowbray-R-V/**Gantry_control-pose_estimation** · the Rubik's-cube-solver CAD in
  hardware §5.1 is this same class of CV-guided multi-motor rig.

### 5.1 Target-practice trainer app (calibration + benchmark + optional reward) ⭐

A tiny app that flashes a target on the phone, lets the robot try to tap it, and
**measures where the tap actually landed** — the single most useful test harness in
the whole project. It does triple duty:

1. **Calibration data** — a known displayed target + the measured touch point is
   exactly the correspondence needed to solve/refine the screen↔robot homography (§5).
2. **Accuracy benchmark** — score = how close the tap was; track it across builds.
3. **Optional training reward** — the same score can drive learning (see note).

**Build it the lazy way — a web page, not a native app:**
- A local page (served from the laptop) shows a dot/square at a known coordinate.
- Capture the real touch with standard JS **`touchstart`/`touchend` → `Touch`
  clientX/clientY** (MDN Touch events) and send it back to the host over
  WebSocket/HTTP.
- **No App Store, no install, works in mobile Safari** — this is precisely Tapster/
  Tappy's browser calibration page (§2). Reuse theirs as a starting point.

**Scoring rubric (your idea, made concrete):**
```
error = distance(tap_point, target_center)      # in screen mm/px
score = max(0, 1 - error / target_radius)        # 1.0 = dead center, 0 at edge
if tap outside phone screen bounds:  score = large negative  # "missed the phone"
```
Loop: show target → robot taps → measure → score → (refine transform) → next target,
across a grid of positions. Median score = the rig's calibration quality.

> **Honest note on "reinforcement learning":** full RL (reward-driven policy
> training) is *more machinery than this needs* and is hard to get working. The same
> hit/score loop gets you 95% of the value as **plain closed-loop calibration**:
> measure the systematic error and update the homography / add a small correction
> offset. Start there. Treat RL as an optional later layer only if nonlinear or
> position-dependent errors remain after calibration. (`ponytail:` deliberately
> avoiding an RL framework until a simpler correction is proven insufficient.)

---

## 6. Perception / UI grounding — reuse models before training

"Find the login button" → screen coordinates. **You likely don't need to train
anything at first:**

- ⭐ **UGround** (OSU-NLP; Qwen2-VL; open weights) — universal GUI visual grounding,
  SOTA on ScreenSpot-Pro. github.com/OSU-NLP-Group/UGround · huggingface.co/osunlp/UGround
- **OmniParser** (Microsoft) — screenshot → structured elements to feed a general
  VLM (GPT-4V/Claude).
- **SeeClick** — screenshot-only GUI agent + **ScreenSpot** benchmark (**includes
  iOS** screens — relevant to us).
- **OS-Atlas** — foundation action model + 13M-element open grounding corpus (data
  for fine-tuning).
- ⭐ **ZonUI-3B** — lightweight grounding model **trainable on one RTX 4090 with
  ~24K samples** — realistic target when we train our own.

---

## 7. Agent control loop

```
loop:
  frame   = camera.capture()
  screen  = calibrate(frame)              # homography (§5)
  state   = perceive(screen)              # OCR + grounding model (§6)
  action  = plan(command, state)          # intent → next primitive
  xy      = screen_to_gantry(action.tgt)  # calibration transform
  robot.do(action, xy)                    # move/tap/swipe/type (§4)
  if verified(camera.capture(), expected): continue else retry/abort
```

Mirrors `../research/05-ai-agent-architecture-notes.md`; only the action layer is
physical. Every action is **verified** against the next frame.

---

## 8. Command vocabulary

High-level intents expanded into primitive sequences:

| Command | Meaning | Expansion |
|---|---|---|
| `exit` | Leave screen/app | tap back/close, or swipe-up home |
| `enter` | Confirm/submit | tap primary button (Continue/Submit/OK) |
| `login <target>` | Authenticate | focus user → type user → focus pass → type secret (vault) → `enter` |
| `open <app>` | Launch app | home → locate icon → tap |
| `type <text>` | Type on keyboard | per-key tap sequence |
| `tap <label>` | Tap described element | ground `<label>` → tap |

`login` is the flagship command and the reason the credential vault exists.

---

## 9. Credential handling & security (non-negotiable)

- **No secrets in the repo, ever.** `.gitignore` excludes env/keys/vault/datasets.
- Secrets live in a **host-side vault** on HomeLab (macOS Keychain / 1Password CLI /
  `sops`+`age`). Agent requests the specific secret for the specific target at the
  moment of use; **never logs or persists its value.**
- **Scrub training data:** any frame where a secret is visible mid-type is dropped
  or masked before entering a dataset.
- **iOS reality:** Face ID / passkey-only logins can't be driven by a robot; scope
  `login` to credential-typeable flows.

### ML training rig (charter D4)
- **Data-collection app** records `(screen_image, command, action, target, outcome)`;
  `outcome` self-labels from the next-frame state change (§7).
- **Layer A (Phase 2):** off-the-shelf UGround/OmniParser + homography — no training,
  but generates labeled data.
- **Layer B (Phase 3):** fine-tune a small grounding model (ZonUI-3B scale) on our
  own iPhone captures; imitation learning from operator demos.
- **Metrics:** task success rate on a fixed eval battery (ScreenSpot-style),
  taps-to-completion, calibration drift, and **zero secret leaks** (hard gate).

---

## 10. Recommended build path (lazy senior-dev route)

1. **Motion:** OpenBuilds ACRO + **GRBL** + servo-Z pen fork → working
   move/tap/swipe with zero custom firmware.
2. **Bridge:** Python `pyserial` streamer exposing `move/tap/swipe/type`.
3. **Calibration:** steal Tapster's browser calibration page + OpenCV homography.
4. **Perception:** UGround (or OmniParser + a VLM) zero-shot — no training yet.
5. **Agent:** implement the §7 loop with §8 commands; add the vault last (§9).
6. **Only then**, if accuracy/speed/cost demand it, train ZonUI-3B on collected data.

---

## 11. Citations & links

**Robots / firmware to reuse**
- Tapsterbot — https://github.com/tapsterbot/tapsterbot · https://tapster.io · fork https://github.com/pylapp/tapsterbot
- Tappy — https://github.com/merinsTDL/tappy · https://github.com/guntiss/tappy · https://github.com/DeMaCS-UNICAL/tappy-original
- BrainyBot (CV taps phone) — https://github.com/DeMaCS-UNICAL/TappingBot
- Delta-Kinematics-Library — https://github.com/tinkersprojects/Delta-Kinematics-Library

**Motion firmware**
- GRBL — https://github.com/gnea/grbl · FluidNC — https://github.com/bdring/FluidNC
- Grbl_Pen_Servo — https://github.com/bdring/Grbl_Pen_Servo · grbl-servo — https://github.com/vankesteren/grbl-servo · grbl 28BYJ+servo — https://github.com/ArcaEge/grbl-28byj-48-pen-plotter-servo

**Motor / servo libraries**
- AccelStepper — https://www.airspayce.com/mikem/arduino/AccelStepper/
- SpeedyStepper — https://github.com/Stan-Reifel/SpeedyStepper · StepperDriver — https://github.com/laurb9/StepperDriver · DRV8825 — https://github.com/RobTillaart/DRV8825
- ServoEasing — https://github.com/ArminJo/ServoEasing · PCA9685 (Adafruit) — https://learn.adafruit.com/16-channel-pwm-servo-driver · PCA9685_RT — https://github.com/RobTillaart/PCA9685_RT
- A4988 / DRV8825 driver tutorials — https://www.makerguides.com/a4988-stepper-motor-driver-arduino-tutorial/ · https://www.makerguides.com/drv8825-stepper-motor-driver-arduino-tutorial/

**Host G-code control**
- python_to_GRBL — https://github.com/Sam-Freitas/python_to_GRBL · streaming gist — https://gist.github.com/jonkensta/7a69bb386fc31ebf3a4beeba2491ef51
- UGS — https://github.com/winder/Universal-G-Code-Sender · bCNC — https://github.com/vlachoudis/bCNC · gSender — https://github.com/Sienci-Labs/gSender

**Simple deterministic control (Firmata — the Tapster way)**
- pyFirmata guide (control Arduino from a Pi in Python) — https://roboticsbackend.com/control-arduino-with-python-and-pyfirmata-from-raspberry-pi/
- firmatazero (GPIO-Zero-style Firmata) — https://github.com/ollipal/firmatazero
- Firmata protocol examples — https://github.com/McGillBattlebotsClub-org/intro-to-firmata
- clapi-arduino (Pi↔Arduino serial) — https://github.com/tonykolomeytsev/kekmech-clapi-arduino
- Tapster REPL usage (`go(x,y,z)`) — https://github.com/hugs/tapsterbot

**Computer vision**
- Perspective warp / homography — https://thelinuxcode.com/perspective-warp-in-python-with-opencv-homography-four-point-mapping-and-real-time-camera-views/
- OpenCV calib3d — https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html · camera calibration — https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html
- OpenCV_Position — https://github.com/RaubCamaioni/OpenCV_Position · detecting a smartphone screen — https://forum.opencv.org/t/detecting-a-smartphone-screen/6829
- Trainer app touch capture: MDN Touch events — https://developer.mozilla.org/en-US/docs/Web/API/Touch_events/Using_Touch_Events

**CV-robot reference builds**
- Petri-Dish-Gantry — https://github.com/Shen-Kev/Petri-Dish-Gantry · Delta-Robot-Project (EmguCV) — https://github.com/tunmaker/Delta-Robot-Project
- Pick-and-Place-3-DOF — https://github.com/himadripoddar/Pick-and-Place-3-DOF-Robotic-Arm · Gantry pose estimation — https://github.com/Mowbray-R-V/Gantry_control-pose_estimation

**UI grounding models / benchmarks**
- UGround — https://github.com/OSU-NLP-Group/UGround · https://huggingface.co/osunlp/UGround
- OmniParser — https://arxiv.org/html/2408.00203v1 · SeeClick — https://github.com/njucckevin/SeeClick · OS-Atlas — https://arxiv.org/html/2410.23218v1 · ZonUI-3B — https://github.com/Han1018/ZonUI-3B
