# Aria's log (hardware)

Newest first.

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
