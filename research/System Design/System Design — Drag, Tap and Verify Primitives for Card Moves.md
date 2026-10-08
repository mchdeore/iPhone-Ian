---
type: research
status: in-progress
author: marc
date: 2026-10-07
tags: [system-design, robotics, rl-and-simple-robots, card-games, gestures, gcode]
---

# System Design — Drag, Tap and Verify Primitives for Card Moves

**TL;DR**
- Card games need **three physical primitives**: `tap` (select, deal, buttons), `drag` (move a card or stack), and `wait_stable` (let animations finish).
- **Drag is the hard one:** the stylus must stay in contact through the whole path, start with a short hold so the app recognises a drag, and end with a dwell before lifting.
- Many card apps also support **tap-to-move**, which is far more reliable for a robot. Use it when available.

**Builds on:** [[Gantry — FluidNC Control Interface (Jogging, Soft Limits, Realtime)]], [[iOS Control — Exposing Device Controls to the Agent]], [[System Design — Card-Playing Gantry Rig Architecture]].

## Primitive definitions (screen px in, G-code out)

```
tap(x, y):        move_xy(x,y) → z_down → dwell(t_tap≈80–120 ms) → z_up
drag(path):       move_xy(p0) → z_down → dwell(t_hold≈150–300 ms)      # drag recognition
                  → for p in path: linear move (constant feed, no lift)
                  → dwell(t_drop≈100–200 ms) → z_up
wait_stable():    poll frames until 2 consecutive frames match (or timeout)
```

Timings are starting points, not measurements. Tune them with the bandit/BO loop ([[RL — Bandits and Bayesian Optimisation for Hardware Tuning]]).

## Making drags work on a gantry

- **Contact must be continuous.** Z pressure comes from a spring, so small surface height variations don't break contact. Lift-off mid-path cancels or misplaces the drag.
- **Use plain feed moves (`G1`) for the path, not jogs.** It's one continuous motion, with feed tuned so the app's drag tracking keeps up. Jogs (`$J=`) are for free moves between gestures.
- **Short path with a final settle:** go to the target's centre and drop. Apps usually snap the card to the pile, so precision only needs to be within the drop zone.
- **Stack moves** (drag a run of cards): grab the **top card of the run**, not the bottom. Check the app's convention once.
- **Fallback, tap-to-move:** a single tap auto-moves the card to its best destination in many apps. It's deterministic and much more robust than dragging. Prefer it whenever the game offers it.

## Verify after every primitive

| Primitive | Expected effect | Check |
|---|---|---|
| tap(card) | Card highlighted or auto-moved | Diff in the card's region within 1 s |
| drag(card → pile) | Card now on top of the target pile; source pile changed | State tracker predicts the new board; perception confirms |
| tap(button) | Screen or dialog changes | Template match on the expected next screen |

Retry policy: one retry with re-perceived coordinates → then reset to a known state → else stop and alert ([[System Design — Reliability, Error Recovery and Testing Harness]]).

## Measure

- Drag success rate vs feed speed, hold time and path length; tap success vs dwell.
- Fold the numbers into the actuator-noise model so emulator-trained policies expect real misses ([[RL — Emulator-First Training and Sim-to-Real for the Rig]]).

## Pitch in

- [ ] Robotics: implement `drag()` on the printer-gantry; sweep hold time 100–400 ms × feed 1,000–6,000 mm/min, 20 drags each; post a heatmap.

## Sources

1. [Grbl 1.1 jogging docs (mirror)](https://gitea.psi.ch/motion/ecmc_plugin_grbl/src/branch/master/doc/markdown/jogging.md) `[Documented]`
2. [TapsterBot Robot Framework keywords (tap, swipe, stress gestures)](https://github.com/pylapp/tapsterbot/wiki/07-%5C--Drive-the-robot:-Robot-Framework-keywords) `[Documented]`
3. [Tapster — robot manipulates phone (Tindie)](https://blog.tindie.com/2016/09/tapster-manipulates-phone-automatically) `[Community]`

## Related

- **Summary:** [[State of — System Design]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]]
- **See also:** [[Touch Telemetry — Measuring What the Rig Emits]] · [[System Design — Bare-Minimum iPhone Setup (MVP)]]
