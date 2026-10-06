---
tags: [gantry, corexy, grbl, arduino, microcontroller, stepper, pen-plotter, mechanical]
status: answered
date: 2026-10-05
related:
  - "[[Prior Art — Touchscreen Robots and Software Agents]]"
  - "[[Capacitive Touch Physics and Gantry Architecture]]"
  - "[[../specs/01-hardware]]"
---

# XY gantry, CoreXY & microcontroller — phone-tapping builds

## Question

What XY/CoreXY gantry builds exist for touchscreen automation? What microcontroller + firmware setup is simplest for a 2-axis Cartesian gantry with a servo Z-axis?

## Key findings

### XY gantry / CoreXY for touchscreen automation

- **No documented CoreXY phone-testing builds found.** CoreXY is popular for 3D printers and pen plotters, but nobody publicly documents using it to tap phone screens.
- **Delta robots dominate** touchscreen testing: Tapster, Tappy, ABB FlexPicker, igus delta.
- **Simple belt-driven Cartesian XY exists** in the pen plotter world — easily adapted. The 1c3d pen plotter: "not CoreXY — for a plotter's light loads, independent X and Y belts driven by their own steppers are simpler to build and tune." `[Community]` https://1c3d.com/projects/build-belt-driven-xy-pen-plotter-grbl-servo
- **TestDevLab explicitly considered and abandoned CNC gantry** for Tappy: "It was difficult to adapt CNC's configuration and software for touchscreen testing." They went delta, but for general phone testing (not our fixed-mount use case).
- **Echo Robot Pen Plotter** uses a spring-loaded pen holder — directly applicable to our Z-axis compliance. `[Community]`
- **Phone-Swiper** (UMN capstone): 2 LIDAR + 2 servo arms, Arduino Nano. Not gantry but adjacent. `[Academic]` https://github.com/bkringlie/Phone-Swiper
- **Touchscreen Testing Robot** (ofer9430): lead screw + A4988 + drawer slide for one axis, SG90 servo for Z. Uses battery negative pole as capacitive tip. `[Community]` https://www.instructables.com/Robot-De-Testeo-Para-Pantalla-Touchscreen/

### Instructables "Screen Tapping Robot" deep dive

Source of truth for our build. By MasterGinger, July 2017. https://www.instructables.com/Screen-Tapping-Robot/

- **Platform:** 9"×12" pattern plate with grommets + standoffs to lock phone
- **X-axis:** Lead screw + NEMA 17 stepper + 2× 8mm×300mm stainless precision shafts with linear ball bearings
- **Y-axis:** Aluminum pulleys + timing belt (explicitly lighter than lead screw — second lead screw "too heavy"). Two channel sliders for stylus mount.
- **Z-axis:** Custom pulley system, standard servo (not stepper). Author initially wanted linear actuator but found it too big/expensive.
- **Electronics:** Raspberry Pi 3 + 2× A4988 stepper drivers. Servo on Pi PWM.
- **Known problems:**
  - Stylus grounding is the #1 problem. Commenter confirms: screen doesn't feel pen when attached to robot, feels it when human holds it. Fix: wire from pen to common 0V.
  - No published code or wiring diagram — reverse-engineering from photos.
  - Polar coordinate system was tried and abandoned ("much less stable").

**What's different from Tappy delta:** 2-motor Cartesian vs 3-motor delta. No kinematics math. Heavier gantry (X carries Y carries Z). Simpler calibration. Slower movement.

### Microcontroller: Arduino Uno + CNC Shield V3 is the answer

**Recommendation:** Arduino Uno clone (~$3) + CNC Shield V3 (~$5) + 2× A4988 (~$3) + MG90S servo (~$3). Total: **~$14.** Flash GRBL 1.1h, set laser mode, wire servo to spindle pin. Done.

| Option | Cost | Complexity | 2-Axis + Servo | Verdict |
|---|---|---|---|---|
| **Arduino Uno + CNC Shield V3 + A4988** | ~$15 | Lowest | Yes (servo on spindle pin via laser mode) | **Simplest. Cheapest.** |
| Arduino Nano + CNC Shield V3 | ~$12 | Low | Same as Uno | Smaller, same limits |
| Arduino Mega + RAMPS 1.4 | ~$30 | Medium | Overkill for 2-axis | Only if more I/O needed later |
| ESP32 + grblHAL / FluidNC | ~$8-15 | Medium-high | Yes + WiFi | Only if WiFi G-code streaming needed |
| Dedicated GRBL board (Protoneer) | ~$25-50 | Medium | All-in-one | Cleaner wiring, more $ |

Key details from ElectricalFlux GRBL guide (Jul 2026): Mainline GRBL 1.1h uses ~28.5KB of ATmega328P's 32KB flash — tight but functional. "For simple 2-axis, Uno is still the correct choice." `[Documented]`

- **Clone shield warning:** Cheap CNC Shield V3 clones often have Z+ limit switch pin incorrectly routed (tied to Spindle Enable). Fix by cutting trace or buying genuine Protoneer.
- **Vref for A4988:** Vref = Imax × 0.8. For NEMA 17 @ 1.5A, set to 1.2V.
- **Servo control:** `$32=1` (laser mode) — GRBL treats spindle PWM pin as dynamic output. Servo needs intermediate driver (GRBL spindle output is 0-5V PWM, not servo signal). 1c3d build confirms this works.

### GRBL approach benefits

Standard G-code interface: `G0 X50 Y80` to move, `M3`/`M5` to tap. Industry standard tooling (UGS, bCNC, Python serial) works out of the box. No inverse kinematics — X/Y map directly to screen coordinates after simple affine calibration.

### Instructables robot used Raspberry Pi — why we shouldn't

Raspberry Pi 3 is heavier, more expensive, requires A4988 drivers wired manually. Uno + CNC shield is cheaper, simpler, all-in-one. The Pi approach also means custom GPIO code instead of battle-tested GRBL. Use the Pi (or Mac) as the host that sends G-code over USB serial; keep the microcontroller simple.

## Sources

- https://www.instructables.com/Screen-Tapping-Robot/
- https://1c3d.com/projects/build-belt-driven-xy-pen-plotter-grbl-servo
- https://electricalflux.com/mcu-general/grbl-on-arduino-compatibility-shield-pinout-guide
- https://github.com/bdring/Grbl_Esp32
- https://www.reddit.com/r/hobbycnc/comments/nhbwz8/gbrlhal_vs_grbl_esp32_pros_and_cons
- https://www.instructables.com/Robot-De-Testeo-Para-Pantalla-Touchscreen/
- https://github.com/bkringlie/Phone-Swiper