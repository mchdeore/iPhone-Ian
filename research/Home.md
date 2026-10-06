---
tags: [home, MOC, index]
status: live
date: 2026-10-06
related:
  - "[[Timeline]]"
  - "[[questions]]"
  - "[[../specs/00-charter]]"
---

# iPhone-Ian — Research Vault

Map of Content (MOC). Start here every time you open the vault.

## Project overview

Build a physical robot that drives a **stock, unmodified iPhone** by tapping its screen, controlled by a vision-based AI agent. Full charter: [[../specs/00-charter]].

## What's where

### Core research domains

- [[mechanical/README|Mechanical]] — prior art, touch physics, gantry design, grounding, microcontroller choice
- [[ios-control/README|iOS Control]] — Face ID, autofill, accessibility, AssistiveTouch/HID, cursor calibration
- [[agent-ml/README|Agent & ML]] — AI architecture, VLM GUI agents, vision grounding, fine-tuning strategy
- [[yolo-training/README|YOLO Training]] — dataset recipe, synthetic data, hardware, quantization, pruning, closed-loop trainer

### Project management

- [[Timeline]] — what phase are we in? what's done, what's next?
- [[questions]] — running question log. Check before starting new research.
- [[../specs/00-charter|Charter]] — decisions set in concrete, scope boundary
- [[../specs/01-hardware|Hardware Spec]] — locked v1 design, BOM
- [[../specs/02-firmware-and-software|Firmware/Software Spec]] — architecture, routes, ML pipeline

### Reference

- [[android-control-survey]] — legacy Android survey. Why software-only iPhone control is not viable.
- [[TEMPLATE]] — copy this when creating a new research note.

### Side projects (not the robot)

- [[_side-projects/README|Side Projects]] — tennis modeling, iOS gambling detection. Separate tracks.

## Quick links

- Graph view (`Cmd+G`): see all notes and connections
- Canvas (`exploration.canvas`): visual planning board
- Local graph (`Cmd+Shift+G`): connections for current note only