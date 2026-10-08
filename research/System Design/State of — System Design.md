---
type: summary
status: living
author: marc
date: 2026-10-07
updated: 2026-10-07
tags: [system-design, state-of]
---

# State of — System Design

> Living summary of everything tagged #system-design: how the pieces fit into a working system. **Update this when you add or change a system-design note**, then bump `updated`.

## Current best answers

- **Reference workload:** a gantry playing a turn-based card game on an iPhone. It's slow, verifiable and visually structured, so it's the best first end-to-end target. **Scope: single-player, offline and play-money games and our own apps. Not real-money multiplayer poker** → [[System Design — Card-Playing Gantry Rig Architecture]], [[System Design — Related Work - Robots and Bots that Play Games]].
- **Architecture:** capture → perceive → state → decide → plan → act → verify, with typed interfaces so each box can be swapped. The state machine, not the screen, is the source of truth → [[System Design — Card-Playing Gantry Rig Architecture]].
- **Bare minimum:** spare iPhone + clamp + grounded stylus on **one of our 3D printers** as an interim gantry + USB capture to a Mac + ~300 lines of Python. A 7-day plan ends with a full verified Solitaire game → [[System Design — Bare-Minimum iPhone Setup (MVP)]].
- **Perception:** on screen capture, **template-match card corners** (no training needed). Use a YOLO detector only for the camera path or varied card art (synthetic-trained mAP50 0.995 but a real-world gap). The hard parts are overlap, face-down cards and animations → [[System Design — Reading Cards from the Screen]].
- **Brain:** search for perfect information, ISMCTS/determinization for hidden cards, CFR for poker against the computer. Klondike's ceiling is ~82% winnable even with full information → [[System Design — Game State and Decision Engines for Card Games]].
- **Actuation:** tap / drag / wait_stable. Drags need continuous contact, an initial hold and a final dwell; **prefer tap-to-move** where the app allows it → [[System Design — Drag, Tap and Verify Primitives for Card Moves]].
- **Reliability:** explicit state machine with timeouts, a RECOVER ladder, SAFE_STOP; test pyramid from replay → simulator → our Flask app → real game → [[System Design — Reliability, Error Recovery and Testing Harness]].

## Decisions made

- Screen-capture path for the MVP (exact pixels, simpler perception); camera support later.
- Moves and gestures are separate layers; every action is verified.
- Episodes are logged in the shared JSONL/LeRobot format, so card runs feed the ML and RL work.

## Where sources disagree or we're unsure

- The BrainyBot/TappingBot prior-art claim couldn't be re-verified.
- Drag timing numbers are starting guesses, not measured.

## Open questions

- Does USB screen capture stay stable while the printer or gantry runs (cabling, EMI)?
- Which offline card app has tap-to-move, no ads, and a fixed layout? (Pick the reference app.)

## Next actions

- [ ] Day 1–7 MVP plan on a printer-gantry.
- [ ] Klondike rules engine + greedy/rollout/ISMCTS comparison in simulation.
- [ ] State-machine skeleton with timeouts, run against the Flask app.

## Changelog

- 2026-10-07: first version.

## Other summaries

[[State of — Robotics]] · [[State of — Machine Learning]] · [[State of — Cybersecurity]] · [[State of — Sports Analytics]] · [[State of — RL and Simple Robots]] · [[State of — ML and Sports Markets]] · [[State of — Math]] · [[State of — YOLO]]
