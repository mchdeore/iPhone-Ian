# Hardware Build Specification

**Scope:** everything physical — the machine, its motion, the tap, the phone
mount, the camera, and the CAD files to build it all. Firmware and code live in
[`02-firmware-and-software.md`](02-firmware-and-software.md).

> All external links are collected with citations in §11. User-supplied CAD links
> are tagged `[user-provided]` and listed in §5.

---

## 🎯 1. Design source of truth (current)

**Instructables — "Screen Tapping Robot"** → https://www.instructables.com/Screen-Tapping-Robot/

Our mechanical baseline. A 3D-printable, stepper-driven **Cartesian XY gantry**
with a stylus that taps the screen — exactly our target architecture, and the
maker reports it working.

**Verified from the build description:**
- **X-axis:** NEMA 17 stepper driving a **lead screw**, riding on **two
  8 mm × 300 mm stainless precision shafts** with **linear ball bearings**; the
  X-axis carries the Y-axis + stylus (built stiff on dual shafts for that reason).
- Cartesian lead-screw motion (not delta, not CoreXY).

**Still to extract from the build page** (Instructables blocks scraping — pull by
hand): Y-axis mechanism + motor, Z/stylus actuation, controller + firmware,
grounding, full BOM, STL/CAD files, work-area dimensions.

---

## 2. System architecture

Five physical subsystems. Each maps to reusable CAD/parts in §4–§5.

| Subsystem | Function | Baseline choice |
|---|---|---|
| **X axis** | Move stylus left/right across screen | NEMA 17 + lead screw on dual 8 mm shafts (SoT) |
| **Y axis** | Move stylus up/down the screen | NEMA 17 + lead screw or belt (TBD from SoT) |
| **Z / tap** | Bring stylus into contact & lift | Servo pen-lift **or** passive spring-Z stylus (§6) |
| **Phone mount** | Hold an iPhone rigidly & repeatably | Adjustable printed clamp (§5) |
| **Camera mount** | Fixed overhead view of the screen (the agent's eyes) | Printed arm / slider rail (§5) |

Design driver: **rigidity + repeatability**, because calibration (camera→screen→
gantry) is the real accuracy bottleneck, not raw motor resolution (§8).

---

## 3. Prior-art lessons we inherit (free knowledge)

From **Tappy / Tapsterbot** (delta-robot phone tappers — different kinematics, same
touch problem). See software spec §2 for their reusable *code*.

1. **Grounding is mandatory — confirmed by multiple builders.** The stylus must be
   electrically tied to the controller/USB ground or the capacitive screen won't
   register touches. Tappy's own docs: *"Make sure that phone recognises stylus
   touches (it must be grounded to arduino GND)."* [guntiss/tappy] **→ We design an
   explicit ground path from day one.**
2. **Joint slop kills accuracy.** Tappy fixed positioning slop by swapping
   ball-joints → neodymium magnets and metal → plastic linkages. A stiff Cartesian
   gantry sidesteps most of this — an argument for our architecture.
3. **Contact is capacitive, not pressure-based** (see
   `../research/02-mechanical-architecture-notes.md`). We only need *consistent*
   contact geometry, not force — so a light, repeatable tap depth is enough.

### 3.4 Tapster design lineage — borrow as much as possible ⭐

Tapster (https://tapster.io, by Jason Huggins — creator of Selenium/Appium) is a
company that has worked on **almost nothing but phone-tapping robots for years**,
and much of it is open. **Policy: reuse their designs wherever we legally can**
(check each repo's license), rather than reinventing.

Their lineage, simplest → most capable:

- **Push Button Robot** — a small-footprint, minimal, ~two-rail/two-track tapper.
  *[user-reported; verify specifics on tapster.io + the `tapsterbot` GitHub org.]*
  **This is our most attractive MVP target:** tiny, few parts, and easy to drive
  deterministically (see sw spec §4.1). Start here, scale up only if needed.
- **Sidekick** — **two independent arms**, each with its own Z-axis servo (the host
  maps left arm = servo `s3`, right arm = servo `s6`). Two effectors ⇒ a path to
  **2-point multi-touch** (pinch/rotate) later. Web controller repo:
  https://github.com/tapsterbot/controller
- **Tapster / Tapster-2** — the flagship **delta** tapper (open hardware + software).
- **Valet** — their **current Raspberry-Pi-based** product. Notable because it puts
  the **Pi as the host** — the same split we plan (Pi/HomeLab host drives a dumb
  controller).
- **BitBeamBot** — the ancestor that started the lineage (built to play Angry Birds).

**Strategy:** prototype at **Push Button Robot** scale/simplicity, reuse Tapster's
open hardware + host stack, and only move to a Cartesian gantry or a two-arm
(Sidekick-style) rig if the task demands larger reach or multi-touch. Links in §11.

---

## 4. Mechanics — reuse ecosystems (don't design linear motion from scratch)

- ⭐ **OpenBuilds** — V-Slot™ / C-Beam™ extrusion, wheels, lead screws, NEMA 17
  mounts, gantry plates. CC BY-SA; large parts market. https://openbuilds.com
- ⭐ **OpenBuilds ACRO** — a pen-plotter-sized XY gantry kit ≈ our machine;
  adaptable to any size. Assembly: [Maker Hardware ACRO manual]; ACRO pen-plotter
  build w/ GRBL + Pi: [ACRO Openbuilds Pen Plotter].
- **openBrushograph** — 3D-printable XY gantry + Z, FreeCAD/OpenSCAD sources.
  https://github.com/openBrushograph/openBrushograph_hardware
- **CNC pen-plotter references** — https://github.com/DAguirreAg/CNC-pen-plotter ·
  https://github.com/thrly/pen-plotter-resources
- **openbuilds-parts** (OpenSCAD brackets) — https://github.com/mhgreen/openbuilds-parts

**Decision to make:** keep the SoT's printed shaft + lead-screw frame (cheapest,
fully printable) **vs.** OpenBuilds extrusion (stiffer, faster to assemble). Our XY
load is a featherweight stylus, so recommend prototyping on **ACRO** to de-risk
motion, then optimize cost.

---

## 5. CAD file library

Ready-to-use models mapped to subsystems. **Editability:** GrabCAD models are often
**STEP** (parametric-editable); Printables are usually **STL** (mesh). Verify
license on each before use.

### 5.1 User-provided links `[user-provided]`

| Part | Use in our build | Link | Notes |
|---|---|---|---|
| Medium-format CNC machine w/ ATC spindle | Reference for a full XY(Z) gantry + mounts | https://grabcad.com/library/custom-designed-medium-format-cnc-machine-with-atc-spindle-1 | Bigger than we need; harvest gantry/mount geometry |
| **SG90 micro servomotor** | The **tap (Z) actuator** model for assembly fit | https://grabcad.com/library/sg90-micro-servomotor-1 | Pairs with ServoEasing in sw spec |
| Rubik's Cube solver (full setup) | Reference: multi-motor + gripper + frame + vision | https://grabcad.com/library/rubik-s-cube-solver-full-setup-1 | Great CV-robot mechanical precedent |
| **Parametric NEMA 14/17 stepper mount** | **X/Y motor mounts** (parametric = resize to our frame) | https://grabcad.com/library/parametric-stepper-motor-nema-14-17-mount-1 | Directly reusable |
| **DSLR slider module** | **Linear axis** reference (carriage + rail) | https://grabcad.com/library/dslr-slider-module-1 | Camera-slider = a single linear axis |
| **Linear sliding system** | **X/Y linear-motion** carriage/bearing block | https://grabcad.com/library/linear-sliding-system-1 | Core motion element |
| **Screw + stepper motor coupling** | Couple NEMA 17 shaft → lead screw | https://www.printables.com/model/404241-screw-and-stepper-motor-coupling | Directly reusable |
| **MK4 Z-screw motor cover** | Tidy/​protect the Z lead-screw + motor | https://www.printables.com/model/454773-mk4-z-screw-motor-cover | Cosmetic/protective |
| **Adjustable tripod phone clamp v2** | The **iPhone mount** (adjustable width) | https://www.printables.com/model/25969-tripod-mobile-phone-clamp-v2 | Directly reusable for phone cradle |

> Status: links recorded as provided; **not yet individually opened/verified**
> (GrabCAD/Printables may gate downloads behind login). Verify geometry, scale, and
> license before printing. Mesh (STL) parts may need re-modeling if dimensions must
> change — prefer the STEP/parametric ones for load-bearing structure.

### 5.2 Model libraries to search for the rest

- **Printables** https://www.printables.com · **GrabCAD** https://grabcad.com ·
  **Thingiverse** https://www.thingiverse.com · **Thangs** https://thangs.com
- **Hardware w/ CAD (for a correct BOM):** McMaster-Carr, Misumi (every
  screw/bearing/shaft as a STEP).

### 5.3 CAD tools

- **FreeCAD** (parametric, open) · **OpenSCAD** (code-CAD; great for parametric
  brackets — openBrushograph uses both) · **Onshape** / **Autodesk Fusion** (GUI).

---

## 6. Tap (Z) actuation — options

The tap is the one truly custom motion. Three routes (hardware side; firmware in sw
spec §3):

1. ⭐ **Servo pen-lift** (SG90 + ServoEasing) — controlled, repeatable tap depth;
   reuses the entire pen-plotter ecosystem (GRBL servo-Z forks). Matches the
   user-provided SG90 CAD.
2. **Passive spring-Z stylus** (Tappy-style) — no Z motor; the XY frame lowers a
   sprung stylus. Simplest, but tap force/engagement is fixed by geometry.
3. **Solenoid tapper** — snappy single taps; poor for press-and-hold/drag.

**Recommendation:** servo pen-lift (route 1). It also enables long-press/drag by
holding Z-down while XY moves — needed for swipes and `type` on the keyboard.

Stylus tip: conductive capacitive stylus tip **with the mandatory ground wire**
(§3.1) back to controller/USB GND.

---

## 7. iPhone-specific mechanical notes

- **Flat vs. curved glass:** a fixed-angle stylus tuned for the flat center may miss
  near curved "waterfall" edges (surface normal changes). Recent iPhones trend
  flat, which helps. Pick a first target model and measure. *(Inference — verify on
  hardware.)*
- **Screen protectors:** thin ones don't meaningfully block capacitive sensing;
  thick/air-gapped ones can. Test with the actual phone + stylus.
- **Reachability:** the work area must cover the **full screen including the
  on-screen keyboard** (bottom edge) for credential typing.

---

## 8. Accuracy target

Sub-mm gantry accuracy is easily achievable and is **well within** iOS's comfortable
touch-target size (~44 pt). As Tappy found, **mechanical precision is not the
limiter — calibration is.** Spend effort on the camera→screen→gantry transform (sw
spec §4), not on exotic motors.

---

## 9. Bill of materials (direction, not final)

| Class | Approx. cost | Basis |
|---|---|---|
| SoT printed frame (delta/gantry + servos/steppers + stylus) | ~$80–150 | TestDevLab Tappy / SoT |
| OpenBuilds ACRO XY gantry (steppers + extrusion + plates) | ~$150–300 | Inferred from kit pricing |
| + overhead camera (USB webcam) + printed phone clamp | +$20–60 | Inference |
| Electronics (Arduino/ESP32 + stepper drivers + servo) | ~$25–60 | A4988/DRV8825 + Uno/ESP32 |

A sourced, quantized BOM is a Phase-1 deliverable once §4's frame decision is made.

---

## 10. Open hardware decisions

- [ ] Frame: printed shaft/lead-screw (SoT) vs. OpenBuilds ACRO extrusion.
- [ ] Z: servo pen-lift (recommended) vs. passive spring-Z vs. solenoid.
- [ ] First target iPhone model (screen size/curvature → clamp + calibration).
- [ ] Camera: fixed overhead webcam spec + mount rigidity.
- [ ] Controller board (ties to firmware route — sw spec §1).

---

## 11. Citations & links

**Design source of truth**
- Screen Tapping Robot — https://www.instructables.com/Screen-Tapping-Robot/

**Prior-art robots (mechanics + grounding lessons)**
- Tapster (Jason Huggins) — https://tapster.io · https://github.com/tapsterbot/tapsterbot
- Tapster product lineage — Push Button Robot / Sidekick / Tapster-2 / Valet / BitBeamBot (see https://tapster.io and the https://github.com/tapsterbot org)
- Sidekick web controller — https://github.com/tapsterbot/controller
- Tapster overview — https://intorobotics.com/tapster-open-source-robot-to-test-mobile-applications-on-a-smartphone/
- Tappy (TestDevLab forks) — https://github.com/guntiss/tappy · https://github.com/merinsTDL/tappy · https://github.com/DeMaCS-UNICAL/tappy-original

**Mechanics ecosystems**
- OpenBuilds — https://openbuilds.com
- ACRO assembly — https://makerhardware.net/knowledge-base/build-manuals/cnc-machines/acro-cnc-mechanical-kit-assembly-instructions/
- ACRO pen-plotter (GRBL + Pi) — https://www.instructables.com/ACRO-Openbuilds-Pen-Plotter-Arduino-With-GRBL-and-/
- openBrushograph — https://github.com/openBrushograph/openBrushograph_hardware
- CNC pen plotter — https://github.com/DAguirreAg/CNC-pen-plotter
- pen-plotter-resources — https://github.com/thrly/pen-plotter-resources
- openbuilds-parts (OpenSCAD) — https://github.com/mhgreen/openbuilds-parts

**User-provided CAD** — see §5.1 table.

**CAD tools & libraries**
- FreeCAD https://www.freecad.org · OpenSCAD https://openscad.org · Onshape https://www.onshape.com
- Printables https://www.printables.com · GrabCAD https://grabcad.com · Thingiverse https://www.thingiverse.com · Thangs https://thangs.com
