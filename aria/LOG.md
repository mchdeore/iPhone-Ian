# Aria's log (hardware)

Newest first.

## 2026-10-08 (later): AliExpress order placed

**Ordered (~C$381 tax-in, after dropping the inserts + screw box).** Paid by Aria; split with Marc.

Bought (21 lines): MKS DLC32 V2.1 (board only), TMC2209 ×4, 2× NEMA17 17HE08-1004S, MG90S ×2 (180°), 24 V 3 A PSU, Mini560 PRO 5 V, endstops ×3, **MGN9H 230 mm ×3**, 2020V extrusion 240 mm, 20T pulleys ×2 packs (1 spare pair), M3 nyloc nuts, M3×5 0.5 mm shim washers, brass tube OD5 300 mm, springs 0.5 mm 7 mm-OD ×20 mm, 26 AWG wire, servo extension, DC jack ×2, **GT2 6 mm PU steel-core belt 5 m** (upgraded from rubber — original sold out), **idlers 7 toothed + 5 smooth** (Mellow, bearing-type; original listing sold out), M3 T-nuts for 2020.

Substitutions vs BOM: belt → PU steel-core; idlers → Mellow bearing (pricier but quieter/stiffer); both because the §5 listings went sold-out/no-ship to CA.

**Reused from Olyntia's Amazon set (not re-bought):** M3 heat-set inserts, initial M3 screws.

Still to buy later:
- **Base plate** — JLCCNC, after the plate CAD.
- **M3×50 idler-axle bolts + exact-length screw top-up** — after printed parts are designed.
- **Amazon: stylus tips + 6061 rail bar** — confirm these went in (rail bar is the ~3-week long-lead item).

## 2026-10-08: plan, pipeline, BOM; prices rechecked

- Read Marc's merged `research/` vault. Hardware v2 is now the "current design" on `main`.
- Added three shared root docs: `PLAN.md` (big steps), `PIPELINE.md` (detailed, wired to Marc's research), `BOM.md` (orderable parts list).
- **Workflow change: we work on `main` directly now — no owner branches.** Equal partners.
- FluidNC Wi-Fi question answered: use the `noradio` build (no radios compiled in).
- Rechecked prices into Waterloo N2J:
  - Amazon stylus tips C$8.49 (only 6 in stock), free ship over $35.
  - Amazon rail bar C$26.64 **+ C$5.54 ship**, slow (Oct 30–Nov 20) — order early.
  - AliExpress ships free to Canada, HST added at checkout. Per-item prices are promo/variant/account-dependent, so cent-exact verification isn't meaningful; §5 baseline holds, confirmed at my own checkout.
  - **All-in estimate ~C$370 (tax in), ~C$185 each** before work-sourcing. Full breakdown in `BOM.md`.

## 2026-10-02 (later): until the next sync

- **Next sync: Wednesday 2026-10-07.**
- Both of us are doing research before then.
- **Screen input is undecided and on hold:** webcam vs screen capture.
- **Hardware impact:** a fixed webcam over 2 phones needs ~14 cm above the glass, so the machine grows from ~5 cm to ~16 cm tall.
  The alternative is a small camera riding on the gantry. Until this is decided, the hardware stays camera-agnostic: reserve mount points at the back edge for a camera mast.

## 2026-10-02: call with Marc

**Decisions:**
- **2-phone capacity, 1 phone to start testing.** The CAD is now 2 phones (`N_PHONES = 2`): ~34 × 32 × 5.0 cm.
- **Budget:** split the ~C$325 (+tax) build between us.
- **Repo:** split into `aria/` (hardware) and `marc/` (software and his v1 CAD). Shared docs stay at the top.
- **Parts list:** Marc is OK with it. He'll check what he can get through work; the sourcing columns in `hardware-concept-v2.md` §5 are for that.
- Both of us have 3D printers and essentially free filament.

**Marc's action items (from his notes):**
- what from the parts list he can get from work
- how to code and train the OCR and the reinforcement loop
- an overview of the parameters each side exposes
- a high-level functional diagram
- organize the research (game theory, ML)
- the end goal: a real architectural design and final physical design
- list what we each have at work and home
- nuke the database

**Aria's action items:**
- parts I can get from work
- base plate CAD with slotted holes, then a JLCCNC quote
- printable parts

## 2026-10-01: v2 proposal (supersedes Marc's v1 rod gantry)

Hardware is now owned by Aria, software by Marc. The full write-up is in **`hardware-concept-v2.md`**.

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
- **Model:** `cad/v2_0_layout.py`. It models both belt paths, idlers bolted top and bottom, and motor clamps. Checks: every
  screen corner is reachable with the carriages on their rails, and nothing collides. Run it from `cad/` with the repo `.venv`.
- **Parts:** verified AliExpress / Amazon.ca links and prices are in doc §5. About C$246 on AliExpress, ~C$340–375 for the
  whole build.
- **Retired:** the v1 rod/oilite gantry parts (1, 3, 4) and `0_assembly_preview.py`, because the heights didn't fit and
  the one-sided Y drive would jam. See doc §4.
- **Next:**
  - base plate CAD with slotted holes, then a JLCCNC quote
  - real printable parts (toolhead, end blocks, idler posts, motor clamps, phone slots)
  - Marc's answers to the doc §7 questions
