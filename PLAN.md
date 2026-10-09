# iPhone-Ian — Project Plan (big steps)

How the project matures, no hard dates. Two tracks run in parallel — **hardware** (Aria) and **software/model** (Marc) — and merge once the robot moves. Detailed breakdown in `PIPELINE.md`.

**What it is:** a CoreXY gantry that taps a real iPhone's screen, driven by a local vision model running on Marc's PC. Scope is our own and offline/play-money apps, plus a commissioned app we are authorized to test under its ToS and our engagement agreement.

---

## The stages

**1. Define** — purpose, requirements, scope, ToS/authorization boundary.
*Hardware requirements locked. Concept scope mostly set.*

**2. Design** — hardware drawings + BOM; software architecture; the fixed interface between them (`move / tap / down / up / home` over USB).
**← we are here.** Hardware ~90% (base plate + printed parts left). BOM done.

**3. Build & bring-up — "get it moving."** Order, print, assemble. The robot homes, moves, and taps on command. No intelligence yet.
*Gate: a manual command produces a registered tap on the phone.*

**4. Simple test app** — a minimal app/harness to exercise the robot's basic abilities (tap a target, drag, confirm it worked) and to start logging runs.
*Gate: the robot reliably hits targets we point it at, end to end.*

**5. Train the model** — stand up the local vision model on Marc's PC and tune it to read the screen and act naturally and reliably (human-like interaction quality). Runs against the test app.
*Gate: the model drives the robot through the test app on its own.*

**6. Teach it poker (parallel to 5)** — game-theory research: hands, plays, betting conventions, decision engine.
*Gate: a decision engine that plays correctly in simulation.*

**7. Offline poker test** — run the trained model + engine on an **offline** poker game. First look at real performance.
*Gate: it completes games unattended and we can measure how well it plays.*

**8. Optimize** — tune model, motion, and reliability against what we saw in stage 7. Error recovery, speed, unattended runtime.
*Gate: we're happy with accuracy, speed, and stability.*

**9. Commissioned app** — only once optimized: test the authorized target app, within its ToS and the engagement agreement.
*Gate: runs the agreed test.*

**10. Scale & refine (ongoing)** — 2nd phone slot and beyond; quieter/slimmer v3 hardware; the drawer enclosure.

---

## Ownership
- **Aria:** all hardware — CAD, BOM, sourcing, assembly, bring-up, calibration rig; plus the physical/actuation side of "natural interaction" (motion smoothness, timing, touch telemetry).
- **Marc:** software, the local model, training/optimization, and the poker decision engine. He owns the compute tuning on the 1080.
- **Shared:** the move/tap interface, the test app spec, scope and ToS guardrails.

## Guardrails (carried through every stage)
- Authorized/commissioned and offline/play-money targets only. No real-money multiplayer poker.
- No work on evading bot detection, geofencing, or identity/biometric checks — detection is mapped for understanding only (Marc's `research/Cybersecurity`), never defeated.
- Test phones carry no real credentials, payments, or messaging apps.
- Controller runs USB-only, Wi-Fi off (FluidNC `noradio` build); all remote access goes through the host.
