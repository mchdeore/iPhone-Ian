---
tags: [agent, ML, VLM, index, MOC]
status: live
date: 2026-10-06
related:
  - "[[../Home]]"
  - "[[../Timeline]]"
---

# Agent & ML Research

Perception→planning→action loop for a vision-based AI agent driving a physical iPhone-tapping robot.

| File | Question answered | Status |
|---|---|---|
| [[01-agent-architecture]] | Perception→planning→action loop design? Closest precedent? | Answered |
| [[02-vlm-gui-agent-survey]] | VLM GUI agents state of the art? Vision grounding? Fine-tune vs prompt? | Answered |

## Key decisions made

- Vision-only (no accessibility tree) — validated by literature
- Perception and planning are separate concerns
- Phase 2: zero-shot (UGround/OmniParser) for prototyping
- Phase 3: fine-tune ZonUI-3B (3B params, single RTX 4090) on our iPhone captures
- Planning: off-the-shelf VLMs (GPT-4V, Claude, Gemini)
- Camera-photo grounding is an open research gap — we may contribute

## What feeds into this

- [[../mechanical/README|Mechanical]] — gantry calibration
- [[../ios-control/README|iOS Control]] — CV must handle iOS UI quirks
- [[../yolo-training/README|YOLO Training]] — perception component
- Phase 2/3 of [[../Timeline]]

## What this feeds

- [[../../specs/02-firmware-and-software|Firmware/Software Spec]] — ML pipeline