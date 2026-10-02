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
- **Size:** ~53 × 32 cm footprint, **~5.0 cm tall** (checked in `parts/v2_0_layout.py`: 10 mm under-bridge clearance, every screen corner reachable, no collisions). The minimum height is set by the phones (~9 mm), clearance under
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

## 5. Parts to buy: verified listings (checked 2026-10-01, CAD, before tax)

Every listing was opened and its option and price checked. **Choose the variant shown in "Pick".**

### AliExpress

| Part | Link | Pick | C$ |
|---|---|---|---|
| Controller | [MKS DLC32 V2.1](https://www.aliexpress.com/item/1005003528786927.html) | "MKS DLC32 V2.1" (board only) | 26.85 |
| Drivers | [BIGTREETECH TMC2209 (official)](https://www.aliexpress.com/item/33028050145.html) | 4PCS | 23.21 |
| Motors | [STEPPERONLINE 17HE08-1004S (official)](https://www.aliexpress.com/item/1005004708155105.html) | 1PC ×2 (23 mm, 1 A, 20 mm shaft) | 24.16 |
| Servo | [MG90S](https://www.aliexpress.com/item/1005008626768357.html) | 2 pcs, **180°** (360° = continuous, useless) | 5.89 |
| PSU | [24 V adapter](https://www.aliexpress.com/item/4000521124523.html) | 3A, US Plug, 24V | 10.93 |
| 5 V buck (servo) | [Mini560 **PRO**](https://www.aliexpress.com/item/1005006537133858.html) | 5 V (PRO = 6–30 V in; plain Mini560 can't take 24 V) | 5.07 |
| Endstops | [mechanical, with cable](https://www.aliexpress.com/item/1005007505049085.html) | 3 pcs | 3.97 |
| Rails | [MGN9 (Magic Dragon)](https://www.aliexpress.com/item/1005002721523331.html) | MGN9H: 420mm ×2, 230mm ×1 | 50.07 |
| Bridge | [2020 V-slot (same store)](https://www.aliexpress.com/item/1005003311298946.html) | 240mm, 2020V | 6.39 |
| Belt | [GT2 rubber/aramid](https://www.aliexpress.com/item/1005008463979470.html) | 6mm, 5 meters | 6.16 |
| Motor pulleys | [Mellow 20T 5 mm bore (official)](https://www.aliexpress.com/item/33023279793.html) | For 6mm, 2Pcs | 6.86 |
| Idlers | [GT2 20T 3 mm bore](https://www.aliexpress.com/item/32817328238.html) | "20T W6 B3 GT2 T" ×6, "20T W6 B3 without T" ×4 | 25.62 |
| Heat-set inserts | [M3 brass](https://www.aliexpress.com/item/1005010325121347.html) | M3 | 7.54 |
| Screws | [M3 DIN912](https://www.aliexpress.com/item/1005001785690381.html) | M3 × 8, 12, 16, 20, 25, and 50 (×2, corner idler bolts) | ~14 |
| Nyloc nuts | [M3](https://www.aliexpress.com/item/32798773566.html) | M3 | 2.83 |
| Shim washers | [M3 0.5 mm](https://www.aliexpress.com/item/1005002046188859.html) | M3, 0.5 mm (idler spacing, inner race only) | 2.38 |
| T-nuts | [M3 for 2020](https://www.aliexpress.com/item/4000726230157.html) | M3 | 2.94 |
| Brass tube | [0.25 mm wall](https://www.aliexpress.com/item/1005005307061739.html) | 5 mm OD (4.5 ID fits the stylus tip stem) | ~7.41 |
| Springs | [0.5 mm wire](https://www.aliexpress.com/item/1005005312536098.html) | ~7 mm OD × 20 mm (over the tube) | ~5.28 |
| Wire | [silicone](https://www.aliexpress.com/item/1005006250522147.html) | 26AWG, 5 m | 3.78 |
| Servo extension | [listing](https://www.aliexpress.com/item/1005008268927795.html) | 1to1, 50 cm | 2.29 |
| DC jack adapter | [listing](https://www.aliexpress.com/item/1005007895939239.html) | female 5.5×2.5 | 2.04 |
| **AliExpress total** | | | **~246** (~278 with HST) |

### Elsewhere

| Part | Where | C$ |
|---|---|---|
| Stylus tips, 6 mm mesh with threaded metal stem | [Amazon.ca PATIKIL 5-pack](https://www.amazon.ca/dp/B0FNX4LB7H) (AliExpress only has Apple Pencil nibs, which are active and won't work) | 8.49 |
| Rail risers, 6061 10×20 mm ×2 cut to 430 mm | Metal Supermarkets (Kitchener), or [Amazon.ca COYOUCO 10×20×500](https://www.amazon.ca/dp/B0GS1P1J79) ×2 | ~25–59 |
| Base plate, 3 mm aluminium 530×320 with slotted holes | JLCCNC quote **after** the plate CAD exists | ~60 incl. shipping |

**Whole build ≈ C$340–375 before tax.** Filament is on hand.

**Printed (Centauri, CF-PETG / TPU):** corner idler posts + top plates + side walls, motor clamp bars + legs, motor B spacer,
bridge end blocks + top plates, toolhead plate + lever + stylus sleeve, belt clamp, endstop mounts, 4 phone slots,
cable guides, feet, controller box.

**Assembly notes:**
- Mount motor pulleys **hub-up** (teeth toward the motor) so they line up with the belts.
- Every idler bolt is clamped **top and bottom**. Shim washers touch only the bearing's inner race.
- Confirm on arrival which pin on the DLC32 drives the servo and how the board takes power (barrel jack vs screw terminal).

**Security:** run the controller over USB only, with its Wi-Fi off. Remote access goes through the host (SSH / WireGuard / Tailscale).
FluidNC's network control has no real authentication.

## 6. Sourcing

- **JLCCNC** is the default for metal (price). Bundle the JLCMC rails, pulleys and fasteners into the same order.
- **SendCutSend** only for rush parts.
- **AliExpress** for electronics, motors, motion parts and hardware (one order; rails + extrusion ship together from Magic Dragon).
- **Base from day one is a 3 mm aluminium plate cut by JLCCNC.** Rail-riser, motor and slot holes are **slots, not round holes**,
  so a few mm of CAD error is adjusted out instead of forcing a reorder. Order it only after the assembly is checked in Onshape.
  Later upgrades: a bent aluminium tray (base + raised rail ledges in one part), a bent-channel bridge, motor plates.
  Later, possibly a JLC flex-PCB ribbon to the carriage.
- Keep precision holes on flat sections, not ones that depend on a bend's position.

## 7. Open questions for Marc

1. Do 4 simultaneous screen feeds (USB or AirPlay) work on your setup? This decides the camera question.
2. Bare phones only, or cases too? (The spring absorbs ~3 mm; cases also widen the slots.)
3. OK for me to take over the CAD branch and replace the rod gantry with CoreXY?
4. Budget ceiling and how we split it.
5. Is the hand-off in §3.1 enough for your side?
6. Security: OK with USB-only to the controller and all remote access through the host?
