# Hardware Concept v2: requirements, design, parts

**Author:** Aria (hardware lead) · **Date:** 2026-10-01 · **Status:** proposal for Marc to review

This replaces the hardware direction in `specs/01-hardware.md` §0 and the `parts/` scaffold on
`design/hardware-v1-and-cad-scaffold`. The order is requirements first, then the design, then the parts.

---

## 1. Requirements

| # | Requirement | Drives |
|---|---|---|
| R1 | Up to **4 iPhones of any model** at once (maybe more later), held so they can't budge | Bed size, slot design, expandability |
| R2 | **Screen inputs only:** tap, long-press, swipe/drag. No physical buttons, no multi-touch. Phones are kept awake and charged by other means. | One stylus with hold-down |
| R3 | Typing at **2–3 taps/s** | Motion speed, tap actuator |
| R4 | Lives in a **drawer/cabinet**, runs **quietly**, as **slim** as possible (target: thick laptop) | Height budget, the camera question, drivers |
| R5 | **3D-print as much as possible**, low cost (split between us) | Part strategy, sourcing |

## 2. The camera decision (Marc: this is yours to confirm)

An overhead webcam that sees 4 phones in a row has to sit **~28 cm above them** (a typical ~70° webcam
covering ~360 mm). That fails R4.

**Proposal: no camera.** Get each phone's screen image directly instead:
- **USB capture.** The phones are plugged in for charging anyway, and macOS can capture an iPhone's screen over
  the cable (QuickTime / AVFoundation). The phone only needs a one-time "Trust this computer".
- **AirPlay mirroring** to a receiver on the host (e.g. UxPlay on Linux), one instance per phone.

Both are built into iOS, so nothing is installed on the phone. On top of fixing the height, it gives:
pixel-perfect input for OCR, no glare or lens calibration, and the tap results show up directly in the feed.
Calibration becomes: tap known gantry points on a Safari calibration page and read where they land.

**Fallback if this doesn't work:** a small camera riding on the gantry that scans each screen in several shots.
It fits the height, but it's slower and makes the OCR harder.

**Question for Marc:** can you get 4 simultaneous screen feeds on your setup (Mac and/or HomeLab)?

## 3. Concept

```
 back:  [motor A]━━━━━━━━━━━ belts ━━━━━━━━━━━━[motor B]
        ═══════════════ long rail (MGN9) ═══════════════
        ┃      ┌────┐  ┌────┐  ┌────┐  ┌────┐         ┃
        ┃bridge│ 📱 │  │ 📱 │  │ 📱 │  │ 📱 │         ┃   bridge spans front↔back,
        ┃ +    │    │  │    │  │    │  │    │         ┃   travels left↔right;
        ┃stylus└────┘  └────┘  └────┘  └────┘         ┃   stylus travels along bridge
        ═══════════════ long rail (MGN9) ═══════════════
 front
```

- **Bed:** 4 printed phone slots (~95 mm pitch, fits up to Pro Max), phones face up in portrait.
  - Each slot has TPU corner pads, a spring-loaded end clamp, a **pocket for the camera bump** (so the phone doesn't rock), and a notch for the charging cable.
  - Clamping is at the **corners and ends only**: side jaws would press the power and volume buttons.
  - A 5th phone = longer rails.
- **Motion: CoreXY.** Both motors stay fixed in the back corners. The belts pull **both ends** of the bridge
  evenly, so it can't rack, and nothing heavy rides on the bridge, so it stays thin and quiet.
- **Rails:** MGN9 linear rails. They're low, quiet and don't bind, and they replace printed bushings.
- **Tap (Z):** a micro servo lying flat lifts a lever carrying a **spring-loaded conductive stylus** with a **ground
  wire** to controller GND.
  - The spring absorbs thickness differences between models, so one tap height works for all phones.
  - The servo can hold the stylus down for long-press and swipe.
  - A ~10 mm key-to-key hop plus a tap takes ~0.3 s, which meets R3.
- **Controller:** MKS DLC32 (ESP32) running **FluidNC**: CoreXY kinematics and RC-servo Z are set in a config file, with
  no custom firmware. TMC2209 drivers (StealthChop) keep it quiet. (Uno + stock GRBL would need
  two patched firmware forks merged to do CoreXY + servo.)
- **Size:** ~52 × 32 cm footprint, **~4.8 cm tall** (checked in `parts/v2_0_layout.py`: 10 mm under-bridge clearance, no collisions with the stylus at every screen corner). The minimum height is set by the phones (~9 mm), clearance under
  the bridge, and the bridge itself, so it's thicker than a laptop but fits a deep drawer.

### 3.1 Software ↔ hardware hand-off

The robot exposes only:

```
move(x, y)   tap()   down()   up()   home()
```

These are sent as G-code over USB serial, in mm in the machine frame. Marc builds against this immediately; the
hardware just has to obey it. All intelligence stays on the host.

## 4. Review of the current CAD branch

The `parts/` scaffold (build123d) is a good pipeline, but the design doesn't close:

1. **The heights don't fit together.**
   - The X rods are centred 16 mm up, but phone glass is at ~15 mm (bare) and ~19 mm (cased), so the rods and carriage pass through the phone.
   - The stylus holder hangs 38 mm below the carriage, which puts it through the baseplate.
2. **The Y axis will jam.** One belt drives one side of a ~200 mm bridge riding single 12 mm bushings. That's ~17× the
   bearing length vs the usual ≤2× rule, so it will jam. CoreXY fixes this by driving both ends.
3. **The docs disagree.** `main` says Instructables lead-screw; the branch's §0 says pancake motors, printed bushings and
   a 72 mm X reach; `DEVLOG`/`params.py` say oilite bushings and a 150×160 mm area. The parts-list rod lengths (200/120 mm)
   don't match the model (230/210 mm).
4. **The servo is in two places.** `5_stylus_holder.py` hangs the servo below; the assembly preview mounts it on the side.
5. **Missing:**
   - cable management to the moving carriage
   - grub screws threaded straight into PETG will strip, so they need heat-set inserts or nut traps
6. **The tooling only runs on a Mac:** zsh aliases with hard-coded paths. It needs a cross-platform runner.

**Carries over:** the code-CAD workflow, `params.py` as the single source of dimensions, and the spring-stylus idea.
**Retired:** the rod/bushing gantry parts (1, 3, 4) and the assembly preview.

## 5. Parts to buy (AliExpress / JLCMC, approximate CAD)

| Part | Qty | ~$ |
|---|---|---|
| MKS DLC32 V2.1 controller | 1 | 35 |
| TMC2209 drivers | 3 (1 spare) | 15 |
| NEMA 17 pancake stepper, ~23 mm, ~1 A | 2 | 25 |
| MG90S servo | 2 (1 spare) | 8 |
| 24 V 2–3 A PSU + 5 V 3 A buck converter (servo supply) | 1 + 1 | 18 |
| MGN9H rail + carriage: 450 mm ×2, 250 mm ×1 | 3 | 50 |
| 2020 extrusion (v1 frame + bridge): ~480 mm ×2, ~260 mm ×3 | 5 | 20 |
| GT2 6 mm belt 5 m, 20T pulleys (5 mm bore) ×2, idlers (6 toothed + 4 smooth) | set | 15 |
| Mechanical endstops | 3 | 4 |
| Conductive stylus tips (fibre-mesh), compression spring kit, brass tube | set | 10 |
| M3 heat-set inserts, M3 screws 6–30 mm, 2020 T-nuts | set | 20 |
| 4-core flexible silicone cable, ~1.5 m | 1 | 5 |
| v1 base: 5 mm plywood ~480×300 mm (local) | 1 | 15 |
| **Total** | | **~$240** |

Budget variant ~$190: 8 mm rods instead of MGN9 rails.

**Printed (Centauri, CF-PETG / TPU):** frame corners, motor and idler mounts, bridge end blocks, stylus carriage + lever,
belt clamps, endstop mounts, 4 phone slots, cable guides, feet, controller box.

**Check before ordering:** which DLC32 pin drives the servo and which USB connector it has (listings vary), and genuine TMC2209 parts
(they're often mislabeled).

## 6. Sourcing

- **JLCCNC** is the default for metal (price). Bundle the JLCMC rails, pulleys and fasteners into the same order.
- **SendCutSend** only for rush parts.
- **AliExpress** for electronics and motors.
- **Order of work:** v1 on a hand-drilled plywood base. Once the assembly is validated in Onshape and the hole positions are proven,
  order v2 metal: a bent aluminium tray (base + raised rail ledges in one part), a bent-channel bridge, and motor plates.
  Later, possibly a JLC flex-PCB ribbon to the carriage.
- Keep precision holes on flat sections, not ones that depend on a bend's position.

## 7. Open questions for Marc

1. Do 4 simultaneous screen feeds (USB or AirPlay) work on your setup? This decides the camera question.
2. Bare phones only, or cases too? (The spring absorbs ~3 mm; cases also widen the slots.)
3. OK for me to take over the CAD branch and replace the rod gantry with CoreXY?
4. Budget ceiling and how we split it.
5. Is the hand-off in §3.1 enough for your side?
