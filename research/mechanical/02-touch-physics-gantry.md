---
tags: [capacitive, PCAP, grounding, gantry, delta, stylus, calibration, mechanical]
status: answered
date: 2026-10-05
related:
  - "[[mechanical/01-prior-art]]"
  - "[[ios-control/01-faceid-autofill-accessibility]]"
  - "[[mechanical/03-xy-gantry-microcontroller]]"
---

# Mechanical architecture: touch physics, gantry vs delta, grounding

## Question

How does capacitive touch actually work, and what does that mean for our robot's mechanical design? What architecture options exist (delta vs gantry), and what gotchas do we need to design around?

## Key findings

### How capacitive touch works

Modern phones use projected capacitive (PCAP) mutual-capacitance sensing: an ITO electrode grid under the cover glass. Each intersection is a small capacitor. A grounded conductive object nearby draws away local field → the controller detects the capacitance dip → computes coordinate.

**Grounding is the critical variable.** A floating, ungrounded conductive tip often registers weakly or not at all. The human body provides a large earth-referenced capacitance — a robot stylus must replicate this. TestDevLab Tappy empirically confirmed: touches didn't register until they added a ground wire from Arduino to stylus pen. `[Community/empirical]`

Detection is capacitive, not pressure-based. Mechanical force is irrelevant to touch registration — only consistent contact geometry matters.

Sources: https://www.densitron.com/company/news/projected-capacitive-touch-sensor · https://software-dl.ti.com/msp430/msp430_public_sw/mcu/msp430/CapTIvate_Design_Center/1_83_00_08/exports/docs/users_guide/html/CapTIvate_Technology_Guide_html/markdown/ch_basics.html

### Architecture comparison

| Architecture | Cost | Tap | Swipe | Multi-touch | Complexity | Precision |
|---|---|---|---|---|---|---|
| Single solenoid/servo tapper | $10–40 | Yes | No | No | Lowest | Fixed point only |
| Delta-robot (Tappy) | ~$80 | Yes | Yes | No | Medium (inverse kinematics) | Good, but joint slop |
| Cartesian XY gantry (our target) | ~$100–300 | Yes | Yes | Yes (2+ effectors) | Low (linear X/Y, no kinematics) | Best (sub-mm) |
| Commercial multi-effector (MATT) | $1,000+ | Yes | Yes | Yes (true) | N/A (buy, don't build) | Industrial |

**Why Cartesian beats delta for us:**
- No inverse kinematics required — X/Y map directly to screen after affine calibration.
- Stiffer than delta servos → less positioning slop → better calibration stability.
- Scales to two effectors if we ever want multi-touch.
- GRBL firmware directly supports Cartesian — zero custom firmware.

TestDevLab explicitly considered and abandoned a CNC gantry for Tappy: "It was difficult to adapt CNC's configuration and software for touchscreen testing." They went delta, but for general phone testing (not our fixed-mount use case).

### Coordinate accuracy

Gantry/stepper designs hit sub-millimeter mechanical accuracy. Android's minimum touch target is 48dp (several mm), so mechanical precision is rarely the limiting factor. **Calibration accuracy (rig coordinate frame → screen coordinate frame) is the actual bottleneck.** Tappy built a dedicated browser-based calibration page — not relying on measured/assumed geometry.

### Does modern phone hardware make this harder?

- Thinner glass **helps** (less capacitive attenuation).
- Edge-to-edge/curved screens are a geometric problem (stylus calibrated for flat center may not contact near curved edges where surface normal changes). Industry trend 2025–2026 is back toward flat panels — helps us.
- Modern electrode sensitivity (glove-touch/stylus support) makes reliable triggering **easier**, not harder.

### Screen protector interference

Thin, properly-applied protectors don't meaningfully block capacitive detection. Thick/air-gapped protectors add attenuation and could push a marginal actuator (weak grounding, borderline tip conductivity) into unreliable territory. Test directly once a prototype exists.

### Stylus tip materials

- **Conductive silicone** — best. Longest wear life, consistent capacitance. `[Community]`
- **Carbon-fiber composite** — good. Durable, less compliant. Less likely to deform under repeated servo strikes.
- **Conductive foam** — budget. Works but wears out. Standard for DIY builds.
- **Metal/coin** — works but risks scratching screen.
- **Battery negative pole** — crude but functional. Used in one Instructables build.

Wipe tips weekly with isopropyl alcohol. Ask suppliers for cycle-life data (100,000+ actuations target).

### Grounding: universal pattern

Connect GND of microcontroller (Arduino) to conductive stylus tip via wire. This creates the capacitive path that a human body normally provides. No one has documented a better approach than the ground wire. This is mandatory — not optional.

### No phone modification required

Every physical actuator method treats the phone as an opaque black box. No Developer Options, no USB debugging, no accessibility service, no root. The only "install" is Tappy's optional browser-based calibration webpage (no persistent footprint). This is the core value proposition over every software method.

## Sources

- https://www.densitron.com/company/news/projected-capacitive-touch-sensor
- https://software-dl.ti.com/msp430/msp430_public_sw/mcu/msp430/CapTIvate_Design_Center/1_83_00_08/exports/docs/users_guide/html/CapTIvate_Technology_Guide_html/markdown/ch_basics.html
- https://www.testdevlab.com/blog/how-we-built-a-robot-for-automated-manual-mobile-testing
- https://www.allpcb.com/allelectrohub/how-capacitive-styluses-work
- https://www.howtogeek.com/835769/active-vs-passive-styluses-all-the-standards-explained
- https://electronics.alibaba.com/buyingguides/robot-stylus-touch-pen-guide-what-actually-matters — Robot stylus guide (Aug 2026), conductive tip materials, grounding