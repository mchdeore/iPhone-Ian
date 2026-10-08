---
type: summary
status: living
author: marc
date: 2026-10-07
updated: 2026-10-07
tags: [robotics, state-of]
---

# State of — Robotics

> Living summary of everything tagged #robotics. **Update this when you add or change a robotics note**, then bump `updated`.

## Current best answers

- **Hardware v2 (Aria, 2026-10-02)** is the current design: CoreXY on MGN9 rails, MKS DLC32 + FluidNC, MG90S servo tap with a spring-loaded grounded stylus, 3 mm aluminium base, 2 phones (~34 × 32 × 5 cm, ~C$325). It supersedes the v1 Arduino/GRBL rod gantry. The full design doc is `aria/hardware-concept-v2.md` in the repo.
- **Touch physics:** PCAP screens need a **grounded conductive stylus** → [[Gantry — Capacitive Touch Physics and Architecture]]. Cartesian/CoreXY beats delta (no inverse kinematics) → [[Gantry — XY Builds and Microcontroller Choice]].
- **Controller interface:** Grbl-style `$J=` jogs, `0x85` jog cancel, `?` status. Soft limits must be set per axis, need homing, and must be saved with `$CD=config.yaml` → [[Gantry — FluidNC Control Interface (Jogging, Soft Limits, Realtime)]].
- **Software control paths:** the AssistiveTouch HID pointer is **relative-only**, so visual servoing beats dead reckoning; Full Keyboard Access is the most promising for typing → [[iOS Control — AssistiveTouch Pointer Mechanics]], [[iOS Control — Relative Cursor Calibration and Visual Servoing]], [[iOS Control — Alternative Accessibility Input Paths]].
- **Calibration (if there's a camera):** ChArUco, with intrinsics first, then show a ChArUco on the phone itself to get the screen-plane pose → [[Rig — Camera-to-Screen Calibration with ChArUco]].
- **Where learning fits:** classical control for motion and targeting, **bandits/BO for tap parameters**, RL only for the agent policy → [[RL — Where RL Helps a Gantry Robot (and Where It Doesn't)]], [[RL — Bandits and Bayesian Optimisation for Hardware Tuning]].

## Decisions made

- Screen inputs only (tap, long-press, swipe); typing at 2–3 taps/s; quiet; drawer height (Aria's requirements).
- No overhead camera in v2 (it needs ~28 cm of height). Screen capture is proposed, **pending confirmation**.
- Android work is legacy → [[Android Control Survey (Legacy)]].

## Where sources disagree or we're unsure

- **Camera vs screen capture** is still open. USB → Mac is lowest-latency for one phone; two simultaneous feeds are **unproven** (UxPlay with one instance per phone is the best guess) → [[Rig — iPhone Screen Capture Paths (USB, AirPlay, Multi-Phone)]].
- What the rig "looks like" to apps is reasoned, not measured → [[Touch Telemetry — Measuring What the Rig Emits]].

## Open questions

- HID keyboard vs pure gantry for typing.
- Bare phones only, or cases too (the spring absorbs ~3 mm)?
- Can FluidNC Wi-Fi be fully disabled on the DLC32 (security)?

## Next actions

- [ ] Run the screen-capture tests 1–3 (unblocks the camera decision).
- [ ] Host driver for FluidNC with a single-writer command queue; measure move + tap latency.
- [ ] Build the touch-telemetry logger app; run condition C (gantry) once it taps.
- [ ] Base-plate CAD → JLCCNC quote; printable parts (Aria).

## Changelog

- 2026-10-07: first version.
