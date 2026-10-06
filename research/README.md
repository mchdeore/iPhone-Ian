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

- **[[Home]]** — Map of Content
- **[[Timeline]]** — Project phases, done/next, open decisions
- **[[questions]]** — Running question log. Check before new research.
- **[[TEMPLATE]]** — Copy for new notes.

## Research by domain

### Physical Build (`physical-build/`)
| File | What |
|---|---|
| [[Prior Art — Touchscreen Robots and Software Agents]] | Tappy, MATT, Instructables, droidrun |
| [[Capacitive Touch Physics and Gantry Architecture]] | PCAP physics, grounding, stylus tips, delta vs gantry |
| [[XY Gantry Builds and Microcontroller Choice]] | CoreXY ruled out, Arduino+GRBL setup, BOM |

### Machine Learning (`machine-learning/`)
| File | What |
|---|---|
| [[AI Agent Architecture and Perception Loop]] | Perception→planning→action loop design |
| [[VLM GUI Agents and Vision Grounding Survey]] | Mobile-Agent, OS-Atlas, ZonUI-3B, fine-tune vs prompt |
| [[YOLO — Efficient Dataset Recipe]] | Dataset size, augmentations, splits, minimal recipe |
| [[YOLO — Synthetic Data and Flash Training App]] | Domain randomization, flash app, homography labeling |
| [[YOLO — Training Hardware and Capture Rig]] | GPU tiers, Colab T4, camera rig, hardware ranking |
| [[YOLO — Training on Different Hardware]] | Args per device: CPU/MPS/Colab/low-VRAM/Pi |
| [[YOLO — Quantization]] | PTQ vs QAT, FP16/INT8, export commands |
| [[YOLO — Flask Closed-Loop Trainer App]] | SSE flash+act, Safari pointer, JSONL episodes |
| [[YOLO — Pruning]] | Structured vs unstructured, verdict: skip |
| [[YOLO — Other Optimization Techniques]] | Change detection, screen ROI, native runtimes |
| [[YOLO — Detection Grouping and Class Taxonomy]] | Class list, row/list grouping, dedupe |
| [[YOLO — Knowledge Distillation]] | KD on low-VRAM, pseudo-labeling alternative |
| [[YOLO — Quantization by Hardware]] | Hardware × precision matrix |
| [[YOLO — Efficient Training Strategy]] | Quickest plan, commands, hour estimates |
| [[YOLO — Exposing Device Controls to Model]] | Action API, screen→gantry→GRBL, HID alternative |
| [[YOLO — Windows Public Port and Streaming]] | Tailscale, Cloudflare, WebRTC, hardening |
| [[YOLO — Raspberry Pi Input Converter]] | Pi serial bridge, USB/BLE HID, BOM |

### Software System (`software-system/`)
| File | What |
|---|---|
| [[iOS Control Constraints — Face ID, Autofill, Accessibility]] | Face ID lockout, autofill flows, VoiceOver risk, app login |
| [[AssistiveTouch Pointer Mechanics for Robot Control]] | HID pointer, lock screen behavior, UIAccessibility |
| [[Relative Cursor Calibration and Visual Servoing]] | Dead reckoning, PID, visual servoing |
| [[Alternative iOS Accessibility Input Paths]] | FKA, Switch Control, Voice Control, Back Tap |
| [[Android Software Control Survey (Legacy)]] | Why software-only iPhone control is not viable |

### Side Projects
| File | What |
|---|---|
| [[_side-projects/README|Tennis Modeling]] | In-play tennis win-probability (SpinSight) |
| [[../ios-gambling-detection/README|Gambling Detection]] | iOS geolocation, device integrity |

## Specs

- [[../specs/00-charter|Charter]] — goal, decisions, scope, roadmap
- [[../specs/01-hardware|Hardware Spec]] — locked v1 design, BOM
- [[../specs/02-firmware-and-software|Firmware/Software Spec]] — architecture, routes, ML

## Workflow

1. Open [[Home]] in Obsidian.
2. Check [[Timeline]] for current phase.
3. Before research: scan [[questions]] for duplicates.
4. New research: copy [[TEMPLATE]], fill in, add to [[questions]].
5. Research → decision → moves to `../specs/`.