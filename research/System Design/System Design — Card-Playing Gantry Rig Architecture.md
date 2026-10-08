---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [system-design, robotics, machine-learning, card-games, architecture]
---

# System Design — Card-Playing Gantry Rig Architecture

**TL;DR**
- A gantry that plays a card game on a phone is **five services in a loop**: capture → perceive → track state → decide → act, with a verify step closing the loop.
- Card games are **turn-based**, so latency barely matters. That makes them the ideal first real workload for the rig: slow, verifiable, and visually structured.
- **Scope:** single-player and offline games (Solitaire, card games played against the computer, play-money tables) and our own test app. **Not** real-money multiplayer poker: that takes money from other players, breaks every operator's rules, and they actively hunt bots ([[System Design — Related Work - Robots and Bots that Play Games]]).

## The loop

```
┌────────── host PC (Python) ──────────────────────────────────────────┐
│ 1 CAPTURE   USB/AirPlay frame (or camera)       → frame + timestamp   │
│ 2 PERCEIVE  card detector + OCR + layout        → cards, piles, buttons│
│ 3 STATE     game-state tracker (rules engine)   → typed GameState      │
│ 4 DECIDE    solver / search / policy            → Move (from, to)      │
│ 5 PLAN      move → primitives (tap/drag/wait)   → screen px path       │
│ 6 ACT       px → mm (calibration) → G-code      → FluidNC over USB     │
│ 7 VERIFY    new frame → expected state?          → ok / retry / reset  │
└───────────────────────────────────────────────────────────────────────┘
        ▲ USB/AirPlay capture                         │ USB serial
     iPhone ◄──────── stylus (grounded) ◄──── CoreXY gantry + servo Z
```

## Interfaces (keep them typed and logged)

| Boundary | Contract | Why |
|---|---|---|
| Capture → Perceive | `Frame{img, t_capture, source}` | Swap camera ↔ screen capture without touching anything downstream |
| Perceive → State | `Detections{cards[rank,suit,box,face_up], piles[], buttons[]}` | Perception can be YOLO, templates or a VLM ([[System Design — Reading Cards from the Screen]]) |
| State → Decide | `GameState` (game-specific dataclass) + `legal_moves()` | The solver never sees pixels |
| Decide → Plan | `Move{from_pile, to_pile, n_cards}` | Game logic stays separate from physical actions |
| Plan → Act | `Primitive{tap(x,y) \| drag(path) \| wait(ms)}` in **screen px** | Matches the agent action API ([[iOS Control — Exposing Device Controls to the Agent]]) |
| Act → Robot | G-code / `$J=` jogs in **mm** | [[Gantry — FluidNC Control Interface (Jogging, Soft Limits, Realtime)]] |

## Design principles

- **The state machine is the source of truth, not the screen.** Perception *updates* the believed state; a mismatch triggers re-observation, never a blind action.
- **Every action is verified** before the next one ([[System Design — Reliability, Error Recovery and Testing Harness]]).
- **Swap any box independently.** Start with the dumbest version of each (template matching, a greedy solver) and upgrade one box at a time.
- **Log everything** as episodes (frame, detections, state, move, primitives, result) in the same JSONL and LeRobot format as the rest of the rig ([[RL — Imitation Learning from Logged Taps (BC, ACT, LeRobot)]]).

## Latency budget (Solitaire move)

Capture ~50–150 ms + perception ~20–100 ms + solver ~1–1,000 ms + drag execution ~1–3 s + animation settle ~0.3–0.8 s → **~2–5 s per move**. That's fine for any turn-based game. The gantry dominates, as the YOLO and RL notes concluded.

## Sources

1. [Tapster / TapsterBot — robot-driven mobile testing (Tindie blog)](https://blog.tindie.com/2016/09/tapster-manipulates-phone-automatically) `[Community]`
2. [Cowling, Powley & Whitehouse — Information Set MCTS (2012)](https://eprints.whiterose.ac.uk/75048) `[Benchmark]`
3. [Blake & Gent — Winnability of Klondike (JAIR)](https://jair.org/index.php/jair/article/view/17167) `[Benchmark]`

## Related

- **Summary:** [[State of — System Design]] · [[State of — Robotics]] · [[State of — Machine Learning]]
- **See also:** [[System Design — Bare-Minimum iPhone Setup (MVP)]] · [[System Design — Game State and Decision Engines for Card Games]] · [[System Design — Drag, Tap and Verify Primitives for Card Moves]]
