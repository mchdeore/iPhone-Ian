---
tags: [index, MOC]
status: live
date: 2026-10-06
related:
  - "[[Home]]"
  - "[[Timeline]]"
---

# Research notes — index

## Start here

- **[[Home]]** — Map of Content. Links to everything in the vault.
- **[[Timeline]]** — Project phases, what's done, what's next, open decisions.
- **[[questions]]** — Running question log. Check before starting new research.
- **[[TEMPLATE]]** — Copy this when creating a new research note.

## Research domains

| Domain | Folder | What's covered |
|---|---|---|
| [[mechanical/README\|Mechanical]] | `mechanical/` | Prior art, touch physics, gantry design, grounding, microcontroller choice |
| [[ios-control/README\|iOS Control]] | `ios-control/` | Face ID, autofill, accessibility, AssistiveTouch/HID, cursor calibration |
| [[agent-ml/README\|Agent & ML]] | `agent-ml/` | AI architecture, VLM GUI agents, vision grounding, fine-tuning strategy |
| [[yolo-training/README\|YOLO Training]] | `yolo-training/` | Dataset, synthetic data, hardware, quantization, pruning, closed-loop trainer |
| [[android-control-survey\|Android Survey]] | `android-control-survey.md` | Legacy. Why software-only iPhone control is not viable. |

## Side projects (not the robot)

| Project | Folder | What's covered |
|---|---|---|
| [[_side-projects/tennis-modeling/README\|Tennis Modeling]] | `_side-projects/tennis-modeling/` | In-play tennis win-probability (imported from SpinSight) |
| [[_side-projects/README\|Gambling Detection]] | `ios-gambling-detection/` | iOS geolocation, device integrity, behavioral detection |

## Specs (decisions made)

- [[../specs/00-charter|Charter]] — goal, decisions, scope, roadmap
- [[../specs/01-hardware|Hardware Spec]] — locked v1 design, BOM
- [[../specs/02-firmware-and-software|Firmware/Software Spec]] — architecture, routes, ML pipeline

## Workflow

1. Open [[Home]] — your landing page in Obsidian.
2. Check [[Timeline]] — what phase are we in?
3. Before researching: scan [[questions]] for duplicates.
4. New research: copy [[TEMPLATE]], fill it in, add to [[questions]].
5. Research → decision → moves to `../specs/`.

## Why `android-control-survey.md` is kept

Documents why software control of a stock phone is hard. On Android, software paths exist (ADB, scrcpy, accessibility). On a stock iPhone, none exist — which is why we go physical. Keep as supporting evidence.