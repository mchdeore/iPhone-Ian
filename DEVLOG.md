# DEVLOG — development stage

## 2026-10-01 — Aria (hardware lead): v2 proposal, supersedes the design below

Hardware is now owned by Aria, software by Marc. The full write-up is in **`docs/hardware-concept-v2.md`**.

- **Requirements:**
  - up to 4 iPhones of any model
  - screen inputs only (tap, long-press, swipe)
  - typing at 2–3 taps/s
  - quiet, drawer-height
  - mostly 3D printed, low cost
- **Design:**
  - CoreXY gantry on MGN9 rails over a row of 4 phone slots
  - MKS DLC32 board running FluidNC
  - MG90S servo tap with a spring-loaded, grounded stylus
  - 3 mm aluminium base (JLCCNC)
  - ~53 × 32 × 5.0 cm
- **No overhead camera** (it would need ~28 cm of height). The proposal is screen capture over USB/AirPlay; **Marc to confirm**.
- **Model:** `parts/v2_0_layout.py`. It models both belt paths, idlers bolted top and bottom, and motor clamps. Checks: every
  screen corner is reachable with the carriages on their rails, and nothing collides. Run it from `parts/` with the repo `.venv`.
- **Parts:** verified AliExpress / Amazon.ca links and prices are in doc §5. About C$246 on AliExpress, ~C$340–375 for the
  whole build.
- **Retired:** the v1 rod/oilite gantry parts (1, 3, 4) and `0_assembly_preview.py`, because the heights didn't fit and
  the one-sided Y drive would jam. See doc §4.
- **Next:**
  - base plate CAD with slotted holes, then a JLCCNC quote
  - real printable parts (toolhead, end blocks, idler posts, motor clamps, phone slots)
  - Marc's answers to the doc §7 questions

---

Snapshot for resuming later. Last updated **2026-09-13**.
Branch: `design/hardware-v1-and-cad-scaffold` → PR #1.

## Stage

**CAD modeling of the tapping gantry, in progress (4 of 14 parts done).** Code-CAD
pipeline is working; core moving parts are modeled and verified as single solids.
Nothing built physically yet.

## Locked design

- **Flat twin-rod Cartesian gantry.** Work area = **two iPhones** (`WORK_X=150 × WORK_Y=160 mm`);
  footprint ~23 × 24 cm; height ~1.7 in (driven by the NEMA-17 body).
- **Long axis (Y):** two WIDE rods (`Y_RAIL_X=100`) for a stable bridge.
- **Short axis (X):** two TIGHT rods (`ROD_SPACING=24`) carrying a compact carriage.
- **Bearings:** bronze **oilite** (self-lubricating) bushings on **8 mm steel rod**, in
  printed PETG housings. Rods are **grub-clamped into the brackets** → the rods + brackets
  form one rigid ladder (stiff, quiet).
- **Drive:** each axis its own **GT2 belt + NEMA-17** with a **TMC2209** silent driver;
  Arduino Uno + CNC shield + GRBL over USB (ESP32/FluidNC = wireless upgrade path).
- **Tap (Z):** MG90S servo on the carriage with a **spring-loaded stylus** (spring absorbs
  device-thickness variation → works across bare/cased phones and iPad).
- **Reinforcement standard:** every printed part **SOLID (100% infill)**, PETG, 4–5 walls,
  filleted, heat-set inserts for serviceability. Bought rigid baseplate + rubber feet.

## Toolchain

- `build123d` in a Python 3.12 venv at repo root (`.venv`). Apple Silicon verified.
- Parts live in `parts/` as `N_name.py`; `params.py` is the shared source of truth.
- Aliases (`parts/aliases.zsh`, sourced from `~/.zshrc`):
  `123_part N` (export STL+STEP), `123_viewer` (browser viewer), `123_show N` (view part N).
- Every part carries `assert` sanity checks and is verified as **1 solid / 1 shell** (no voids).

## Task progress (14-part plan)

Done:
1. ✅ Y-carriage bracket — `parts/3_y_carriage_bracket.py`
2. ✅ X-motor bracket variant (NEMA-17 mount) — `parts/4_x_motor_bracket.py`
3. ✅ Compact X-carriage — `parts/1_x_carriage.py`
4. ✅ Stylus/servo holder (FIRST PASS, spring-loaded) — `parts/5_stylus_holder.py`

Remaining:
5. Y-rail end supports
6. Y-motor mount + Y pulley/idler holders
7. X idler holder + belt clamps
8. Screw-adjust belt tensioner
9. X/Y endstop mounts
10. Baseplate interface (bought rigid plate + feet)
11. Overhead camera boom/mount
12. Device cradle / registration stops
13. Rebuild master assembly from all real parts (verify clearances/travel/reach)
14. Reconcile BOM + write print/build sheet

## Open items

- Fit `5_stylus_holder.py` to the REAL MG90S + spring + stylus dimensions (currently first-pass).
- `0_assembly_preview.py` is a schematic; reconcile with real parts in task 13 and update
  `specs/01-hardware.md §0`.
- Renumber parts cleanly at the end (task 14); numbers currently: 0 assembly, 1 carriage,
  3 bracket, 4 motor-bracket, 5 stylus holder.
