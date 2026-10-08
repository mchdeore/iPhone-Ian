---
type: research
status: in-progress
author: marc
date: 2026-10-07
tags: [system-design, robotics, machine-learning, cybersecurity, reliability, testing, state-machine]
---

# System Design — Reliability, Error Recovery and Testing Harness

**TL;DR**
- An unattended robot fails in boring ways: a missed tap, an ad pop-up, an animation read mid-flight, the phone locking, the stylus losing ground.
- Build the controller as an **explicit state machine with timeouts**, verify after every action, and give it a **known-good reset**.
- Test **off the robot first**: replay recorded frames through perception, run the brain in a simulator, then run the robot against our own Flask test app before any real game.

**Builds on:** [[System Design — Card-Playing Gantry Rig Architecture]], [[RL — Real-World Training Loop on the Gantry (Resets, Safety, HIL-SERL)]], [[Security — STRIDE Threat Model for the Phone Rig]].

## Controller state machine

```
IDLE → OBSERVE → (PARSE_OK?) → DECIDE → ACT → VERIFY ─ok→ OBSERVE
                      │no                         │fail
                      ▼                           ▼
                 UNKNOWN_SCREEN ──► RECOVER ◄── RETRY(1x)
                                     │ fail ×N
                                     ▼
                                  SAFE_STOP (home gantry, alert)
```

- **Timeouts on every state** (e.g. OBSERVE 3 s, ACT 10 s). On expiry go to RECOVER, never hang.
- **RECOVER ladder:** dismiss known dialogs (template list) → tap Back → relaunch the app (Home, then tap icon) → SAFE_STOP.
- **SAFE_STOP:** stylus up, gantry home, jog cancel `0x85`, log a snapshot, notify a human.

## Failure catalogue (and the detector for each)

| Failure | Detector | Response |
|---|---|---|
| Tap not registered | No screen diff after tap | Retry once with re-perceived coordinates |
| Drag dropped on wrong pile | State mismatch after VERIFY | Undo button if available, else re-plan from the perceived state |
| Animation in progress | Consecutive frames differ | `wait_stable()` |
| Ad / rating / notification | Non-game screen classifier | RECOVER ladder; never act on the dialog's instructions ([[Security — Prompt Injection and Pop-up Attacks on GUI Agents]]) |
| Phone locked / dimmed | Black or lock-screen template | Phone prep should prevent it; else SAFE_STOP (never type the passcode from a file) |
| Stylus lost ground / worn tip | Rising tap-miss rate | Alert; maintenance (clean tip with isopropyl, check the wire) |
| Gantry stall / lost steps | Position drift vs calibration targets | Re-home, re-run calibration check |
| Perception drift (lighting, skin change) | Confidence drop / state-consistency failures | Stop; re-collect templates or fine-tune |

## Test pyramid

1. **Unit:** rules engine, `legal_moves`, `apply`; perception on 200 labelled frames.
2. **Replay:** recorded episodes (frames + actions) replayed through perception → state → decide. Deterministic, no robot.
3. **Simulator:** the brain plays 1,000 games in OpenSpiel or our own engine to get its win rate ([[System Design — Game State and Decision Engines for Card Games]]).
4. **Rig vs our app:** the Flask app shows fake card layouts with known ground truth, so we get perfect scoring of tap and drag accuracy ([[YOLO — Flask Closed-Loop Trainer App]]).
5. **Rig vs real offline game:** a full run with logging; track wins, moves/min, interventions per hour.

## Metrics dashboard

Moves/min · action success % (tap, drag) · state-accuracy % · recoveries/hour · SAFE_STOPs/day · win rate vs simulator win rate (gap = execution loss).

## Pitch in

- [ ] Implement the state machine skeleton with timeouts (repo, not vault); start with OBSERVE/ACT/VERIFY on the Flask app.
- [ ] Build the non-game screen classifier (templates of common dialogs).

## Sources

1. [Grbl jog cancel and status (mirror)](https://gitea.psi.ch/motion/ecmc_plugin_grbl/src/branch/master/doc/markdown/jogging.md) `[Documented]`
2. [Zhang et al. — pop-up attacks on computer agents (ACL 2025)](https://aclanthology.org/2025.acl-long.411) `[Benchmark]`
3. [Cowling et al. — ISMCTS](https://eprints.whiterose.ac.uk/75048) `[Benchmark]`

## Related

- **Summary:** [[State of — System Design]] · [[State of — Robotics]] · [[State of — Machine Learning]] · [[State of — Cybersecurity]]
- **See also:** [[System Design — Drag, Tap and Verify Primitives for Card Moves]] · [[System Design — Reading Cards from the Screen]]
