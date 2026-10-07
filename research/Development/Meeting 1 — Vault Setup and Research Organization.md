---
tags: [meeting, storyline]
date: 2026-10-07
related:
  - "[[== STORYLINE ==]]"
---

# Meeting 1 — Vault Setup and Research Organization

## Attendees

- mchdeore
- teammate

## What we did

- Set up Obsidian research vault in `research/` with 5 independent clusters: Physical, ML, System, Storyline (was Development), Games Research
- Each cluster has one central node (`== NAME ==`) acting as truth aggregate. All research branches off central node only — no cross-cluster edges
- Cleaned up old README.md, DEVLOG.md, DEVELOPMENT.md — content moved into vault nodes
- Moved specs/ (00-charter, 01-hardware, 02-firmware-and-software) into Development area, linked to central node
- Merged sports-research and gambling-research into one Games Research cluster

## Current state

- Hardware: XY gantry design locked. 4 of 14 CAD parts done in build123d. Grounded capacitive stylus approach confirmed.
- ML: YOLO nano pipeline researched. Flask flash app + ArUco fiducials for synthetic data. ZonUI-3B fine-tuning planned.
- System: iOS constraints mapped. AssistiveTouch HID pointer mechanics understood. Passcode fallback, no Face ID.
- Build: nothing physical yet. CAD in progress on branch `design/hardware-v1-and-cad-scaffold`.

## Next steps

- Decide HID keyboard vs pure gantry for typing
- Pick first target iPhone model
- Continue CAD parts 5-14
- Stage 0 fail-fast: prove grounded stylus registers on iPhone