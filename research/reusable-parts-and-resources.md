# Reusable Parts & Resources — buy/borrow before you build

**Purpose:** you're right that this is "a pretty simple system in the end." It
decomposes into a handful of well-solved layers, each with a mature open-source
ecosystem. This doc is the shopping list of things to **reuse instead of
rebuild**, mapped to our design (`specs/01-hardware.md`,
`specs/02-training-and-control.md`).

> Legend: ⭐ = strongest reuse candidate for its layer.

---

## 0. The one-paragraph synthesis (the "lazy" path)

Almost the entire machine already exists as open parts. A realistic
off-the-shelf stack: **Tapsterbot** (whole robot + calibration + control server,
software reusable even if we keep our own gantry) → **GRBL pen-servo firmware**
(servo Z "pen up/down" *is* our tap) → **OpenBuilds V-slot / ACRO** linear motion
(skip designing rails) → **a Python `pyserial` G-code streamer** as the host
bridge → **OpenCV homography** for the camera→screen mapping → **UGround /
OmniParser** for "find the button" so we may not need to train a model at all at
first. Each layer below expands this.

---

## 1. CAD tools & model libraries

**Editable CAD (parametric — you can change dimensions):**
- **FreeCAD** (free, open) and **OpenSCAD** (code-CAD, great for parametric
  brackets). The `openBrushograph` XY-gantry project uses FreeCAD for the gantry
  and OpenSCAD for the Z mechanism — a good template. https://github.com/openBrushograph/openBrushograph_hardware
- **Onshape** (free for public docs, browser-based) and **Autodesk Fusion**
  (free personal tier) if you prefer GUI CAD.

**Ready-made model libraries (download STL/STEP):**
- ⭐ **Printables** (Prusa) — https://www.printables.com — best-curated; search
  "pen plotter", "CoreXY", "camera slider", "phone holder".
- **GrabCAD** — https://grabcad.com — has **STEP** files (editable), incl. NEMA 17
  motors, bearings, extrusion — good for mocking up an assembly.
- **Thingiverse** — https://www.thingiverse.com — largest but noisier.
- **Thangs** — https://thangs.com — good geometric search.

**Hardware catalogs that ship CAD models** (drop real parts into your assembly):
- **McMaster-Carr** (US) and **Misumi** — every screw/bearing/shaft with a
  downloadable STEP. Invaluable for a correct BOM.

---

## 2. Mechanics — linear motion / gantry ecosystems

Our design source of truth (Instructables "Screen Tapping Robot") uses a
lead-screw + 8 mm precision shafts. The **reuse alternative** is a modular
extrusion ecosystem so you buy motion instead of designing it:

- ⭐ **OpenBuilds** — https://openbuilds.com — V-Slot™ / C-Beam™ aluminum
  extrusion, wheels, lead screws, NEMA 17 mounts, gantry plates. CC BY-SA design,
  huge parts market (Maker Store, RatRig, MakerTechStore, etc.).
- ⭐ **OpenBuilds ACRO** — a pen-plotter-sized XY gantry kit, basically our
  machine at the right scale; adaptable to any size. Assembly refs:
  https://makerhardware.net/knowledge-base/build-manuals/cnc-machines/acro-cnc-mechanical-kit-assembly-instructions/ ·
  ACRO pen-plotter build with GRBL + Pi: https://www.instructables.com/ACRO-Openbuilds-Pen-Plotter-Arduino-With-GRBL-and-/
- **openBrushograph** — 3D-printable XY gantry + Z mechanism, FreeCAD/OpenSCAD
  sources. https://github.com/openBrushograph/openBrushograph_hardware
- **CNC pen-plotter repos** for reference geometry:
  https://github.com/DAguirreAg/CNC-pen-plotter ·
  notes/resources: https://github.com/thrly/pen-plotter-resources
- **openbuilds-parts** (OpenSCAD library of OpenBuilds-compatible brackets):
  https://github.com/mhgreen/openbuilds-parts

**Decision to make (noted in `01-hardware.md`):** keep the SoT's shaft+lead-screw
design (cheap, fully 3D-printable frame) **vs.** OpenBuilds extrusion (stiffer,
faster to assemble, costs a bit more). Recommend prototyping on OpenBuilds ACRO
to de-risk motion, since our XY loads are tiny (a stylus).

---

## 3. Motion-control firmware (Arduino / ESP32)

The controller turns "go to X,Y and tap" into stepper/servo motion. **The tap is
a solved problem**: pen-plotter GRBL forks map a **servo Z-axis to pen up/down** —
that's exactly our tap actuation.

- ⭐ **GRBL** (classic, Arduino Uno / Atmega328) — the standard. G-code in, motion
  out. https://github.com/gnea/grbl
- ⭐ **FluidNC** (ESP32; successor to Grbl_Esp32) — YAML config, WiFi/Bluetooth,
  more axes, web UI. Best if we want wireless host↔controller.
  https://github.com/bdring/FluidNC
- **Servo-Z pen forks (our tap layer):**
  - bdring **Grbl_Pen_Servo** — GRBL with pen-servo up/down. https://github.com/bdring/Grbl_Pen_Servo
  - **grbl-servo** (SG90 micro-servo Z for plotters). https://github.com/vankesteren/grbl-servo
  - GRBL build for 28BYJ-48 + servo Z. https://github.com/ArcaEge/grbl-28byj-48-pen-plotter-servo

*Alternative to a servo tap:* a small solenoid or the passive spring-Z stylus
(from Tappy) — but a servo Z gives controlled, repeatable tap depth and reuses all
the pen-plotter tooling for free.

---

## 4. Existing robot + software stacks (biggest reuse win)

- ⭐⭐ **Tapsterbot** (Jason Huggins / `hugs`) — open-source **and**
  open-hardware **mobile-device automation robot**. This is the closest complete
  precedent to our whole project. It includes: a control server (Node), Arduino
  firmware (Firmata), a **browser-based calibration page** (load on the phone,
  register screen↔robot mapping), a control API, and **Appium** integration.
  - Original: https://github.com/tapsterbot/tapsterbot · project site https://tapster.io
  - Maintained fork w/ improvements: https://github.com/pylapp/tapsterbot
  - ⭐ **BrainyBot** — a Tapsterbot fork that **plays Candy Crush / Ball Sort by
    looking at the phone screen (CV) and tapping** — i.e. perception→tap loop
    already demonstrated. https://github.com/DeMaCS-UNICAL/TappingBot
  - Mechanically Tapster is a **delta** (like Tappy), so we keep our gantry SoT —
    but its **software stack (calibration + control + Appium) is reusable
    regardless of the mechanics.**

---

## 5. Host-side control (Raspberry Pi / PC → controller)

The HomeLab host runs the agent and streams G-code to the controller over USB
serial (or WiFi with FluidNC).

- **For programmatic control from our agent (recommended):** thin Python
  `pyserial` G-code streamers with flow control —
  https://github.com/Sam-Freitas/python_to_GRBL ·
  stream w/ buffer management: https://gist.github.com/jonkensta/7a69bb386fc31ebf3a4beeba2491ef51
- **For manual jogging / calibration / GUI:**
  - ⭐ **Universal G-Code Sender (UGS)** (Java, cross-platform) — https://github.com/winder/Universal-G-Code-Sender
  - **bCNC** (Python, runs on a Pi; auto-leveling, web pendant) — https://github.com/vlachoudis/bCNC
  - **gSender** (Sienci; polished, grblHAL) — https://github.com/Sienci-Labs/gSender

---

## 6. Computer vision — camera → screen coordinates

Because the phone is a black box, the camera is the only sensor. Two sub-problems,
both solved with stock OpenCV:

- ⭐ **Homography / four-point perspective warp** — reproject the angled camera
  view of the phone into a flat screen rectangle, then map screen px → gantry XY.
  This is *the* calibration transform in `02-training-and-control.md §2`.
  - Tutorial: https://thelinuxcode.com/perspective-warp-in-python-with-opencv-homography-four-point-mapping-and-real-time-camera-views/
  - `cv2.findHomography` / `getPerspectiveTransform` docs: https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html
  - Homography-from-reference-image example: https://github.com/RaubCamaioni/OpenCV_Position
- **Camera intrinsic calibration** (remove lens distortion first):
  https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html
- **Screen detection** (find the phone rectangle automatically): OpenCV forum
  "Detecting a smartphone screen" https://forum.opencv.org/t/detecting-a-smartphone-screen/6829

---

## 7. Vision "find the button" — reuse models instead of training first

This directly serves `02-training-and-control.md`: **you may not need to train
anything initially** — off-the-shelf GUI-grounding models map "tap the login
button" → screen coordinates.

- ⭐ **UGround** (OSU-NLP; Qwen2-VL based; open weights on HF) — universal visual
  GUI grounding, SOTA on ScreenSpot-Pro. https://github.com/OSU-NLP-Group/UGround ·
  weights: https://huggingface.co/osunlp/UGround
- **OmniParser** (Microsoft) — parses a screenshot into structured elements to
  feed a general VLM (GPT-4V/Claude). https://arxiv.org/html/2408.00203v1
- **SeeClick** — screenshot-only GUI agent + the **ScreenSpot** benchmark, which
  **includes iOS** screens (relevant to us). https://github.com/njucckevin/SeeClick
- **OS-Atlas** — foundation action model + 13M-element open grounding corpus (data
  for fine-tuning later). https://arxiv.org/html/2410.23218v1
- ⭐ **ZonUI-3B** — lightweight grounding model **trainable on a single RTX 4090
  with ~24K samples** — realistic target if/when we do train our own (the "ML
  rig" in D4). https://github.com/Han1018/ZonUI-3B
- **Benchmarks to measure ourselves against:** ScreenSpot / ScreenSpot-Pro.

**Implication:** Phase 2 can use UGround or OmniParser+VLM zero-shot; Phase 3's
training becomes *fine-tuning a small model on our own iPhone captures* (ZonUI-3B
scale), not training from scratch.

---

## 8. YouTubers & communities (for your own digging)

- **How To Mechatronics** — Arduino + steppers + gantry + intro CV; right level.
- **DIY Machines** — 3D-printed motion projects (e.g. robotic camera slider).
- **Ivan Miranda** — large 3D-printed machines / mechanics inspiration.
- **Teaching Tech** / **Thomas Sanladerer** — 3D-printing fundamentals & tuning.
- **Murtaza's Workshop (Robotics and AI)** — practical OpenCV in Python.
- **Communities:** OpenBuilds forum, Hackaday, Hackster.io, r/robotics,
  r/functionalprint.

---

## 9. How the pieces map to our system

| Layer | Reuse (⭐) | Plugs into |
|---|---|---|
| Frame / linear motion | OpenBuilds ACRO / V-slot (or SoT's printed shafts) | `01-hardware.md` |
| Tap (Z) | GRBL pen-servo fork | `01-hardware.md` |
| Motion firmware | GRBL / FluidNC | `01-hardware.md` |
| Whole-robot precedent | Tapsterbot + BrainyBot | charter §, `02` |
| Host bridge | Python `pyserial` streamer + UGS for jogging | `02` control loop |
| Camera→screen | OpenCV homography | `02 §2` calibration |
| Find element | UGround / OmniParser (→ ZonUI-3B to train) | `02 §3` training rig |

**Bottom line:** the novel work isn't the mechanics or motion — those are
commodity. The real work is (a) reliable **calibration** (camera→screen→gantry)
and (b) the **command→action agent** with safe **credential handling**. Everything
else, buy or fork.
