---
tags: [physical]
---

# Physical Build

Central node for all physical research. Every note in this cluster feeds into the physical design.

What we know:

- PCAP capacitive touch requires a grounded conductive stylus — ground wire from Arduino GND to tip is mandatory
- Cartesian XY gantry beats delta for our use case (no inverse kinematics, stiffer, GRBL-compatible)
- Instructables "Screen Tapping Robot" is the design source of truth
- Arduino Uno + CNC Shield V3 + A4988 + GRBL 1.1h = ~$14 microcontroller setup
- Conductive silicone tip > carbon fiber > conductive foam. Wipe with isopropyl alcohol weekly
- MG90S servo for Z-axis, NEMA 17 steppers for X/Y
- Sub-millimeter mechanical accuracy; calibration is the actual bottleneck

Design source: [[Prior Art — Touchscreen Robots and Software Agents]]
Touch physics: [[Capacitive Touch Physics and Gantry Architecture]]
Build plan: [[XY Gantry Builds and Microcontroller Choice]]