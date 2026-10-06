---
tags: [mechanical, index, MOC]
status: answered
date: 2026-10-06
related:
  - "[[../Home]]"
  - "[[../Timeline]]"
---

# Mechanical Research

Everything about the physical robot: what exists, how touch works, what to build, what microcontroller to use.

| File | Question answered | Status |
|---|---|---|
| [[01-prior-art]] | What has been built before? Commercial, DIY, software agents | Answered |
| [[02-touch-physics-gantry]] | How does capacitive touch work? Delta vs gantry? Stylus materials? | Answered |
| [[03-xy-gantry-microcontroller]] | XY/CoreXY gantry builds? Arduino Uno + GRBL setup? | Answered |

## Key decisions made

- Cartesian XY gantry (belt-driven), not CoreXY, not delta
- Arduino Uno + CNC Shield V3 + A4988 + GRBL 1.1h (~$14)
- MG90S servo Z-axis with grounded conductive silicone tip
- Design source: Instructables "Screen Tapping Robot"

## What feeds into this

- [[../specs/01-hardware|Hardware Spec]] — locked v1 design, BOM
- Phase 1 of [[../Timeline]]

## What this feeds

- [[../ios-control/README|iOS Control]] — stylus grounding affects phone interaction
- [[../agent-ml/README|Agent & ML]] — calibration maps camera → screen → gantry