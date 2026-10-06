---
tags: [hardware]
---

# == Hardware Central ==

PCAP capacitive touch needs grounded conductive stylus. Cartesian XY gantry on GRBL. 3D-printed, ~$14 microcontroller.

## Research

- [[Prior Art — Touchscreen Robots and Software Agents]]
- [[Capacitive Touch Physics and Gantry Architecture]]
- [[XY Gantry Builds and Microcontroller Choice]]

## Key decisions

- Ground wire from Arduino GND to stylus tip is mandatory
- Cartesian XY beats delta: no inverse kinematics, GRBL-native
- Arduino Uno + CNC Shield V3 + A4988 + GRBL 1.1h (~$14)
- MG90S servo Z-axis, NEMA 17 X/Y
- Conductive silicone tip. Wipe with isopropyl alcohol weekly
- Design source: Instructables "Screen Tapping Robot"