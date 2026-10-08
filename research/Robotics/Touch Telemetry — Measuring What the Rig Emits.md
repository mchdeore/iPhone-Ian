---
type: research
status: in-progress
author: marc
date: 2026-10-07
tags: [machine-learning, cybersecurity, robotics, touch-dynamics, telemetry, uitouch, coremotion, test-rig, calibration]
---

# Touch Telemetry — Measuring What the Rig Emits

**TL;DR**
- Every claim in [[Betting Apps — Behavioral and Automation Detection]] §7 about what our rig "looks like" is currently reasoned, not measured.
- A small iOS logger app on our own phone can record exactly what any app can see per touch: UITouch fields, CoreMotion, and accessibility flags. Running it with a human, the gantry and the HID path turns those claims into data.
- The same rig doubles as **tap-accuracy QA** for the gantry, which we need anyway.

**Useful for:** ML (training and evaluation data for [[Behavioral Biometrics — Datasets and Bot-Detection Baselines]]), Cybersecurity (evidence for the threat model).

## What to log (per event, CSV)

| Source | Fields | Why |
|---|---|---|
| `UITouch` | timestamp, phase (began/moved/ended), location (pt), `force`, `maximumPossibleForce`, `majorRadius`, `majorRadiusTolerance`, `tapCount`, `type` | The touch-dynamics surface every app has. A rigid stylus vs a fingerpad should show up in radius spread. |
| `CoreMotion` | accelerometer + gyro at 100 Hz, continuous | IMU response around touch-down: the zkSENSE / HMOG channel. |
| `UIAccessibility` | `isAssistiveTouchRunning`, `isSwitchControlRunning`, `isVoiceOverRunning` | The HID path flips AssistiveTouch on; record it, don't assume. |
| `UIScreen` | `isCaptured` | Confirms the perception path doesn't set the capture flag. |

UIKit is required. SwiftUI gestures only expose x/y. `[Documented]`

## Test matrix

**Conditions:** (A) human, phone in hand · (B) human, phone flat on a table · (C) gantry + grounded stylus, phone clamped · (D) HID / AssistiveTouch pointer, phone clamped.
**Tasks:** 5×7 tap grid · type a fixed 40-character phrase · 20 swipes (4 directions).
**Trials:** ≥30 per task per condition; humans spread across 2+ people and 2 sessions.

## Metrics

- **Inter-tap interval:** mean and coefficient of variation. Regular timing is the headline bot tell.
- **Landing scatter:** error from the target in mm, plus repeatability for repeated targets. This is also the gantry accuracy spec.
- **Dwell time** (began→ended) distribution.
- **Force and radius spread** (std, range).
- **IMU energy** in a ±150 ms window around touch-down, against a no-touch baseline.

There's no good published population baseline for tap dwell or contact size. Tap-vs-long-press cutoffs commonly sit around 500 ms, and one accessibility study found individual tap durations ranging from 100–300 ms to over 1 s. That's why condition A/B data from *our own* people is the baseline. `[Benchmark]`

## Ground rules

- The logger only runs **in our own app on our own phone**. It measures what any app could observe and never touches third-party apps.
- The goal is measurement and QA, reported back to the group, not tuning the rig to pass detectors.
- Logger code goes in the repo (e.g. `marc/touch-logger/`), and recordings go in `datasets/`, which is git-ignored. Only results and plots get written up here.

## Pitch in (robotics people)

- [ ] Write the logger as a single-view UIKit app that exports CSV via the share sheet.
- [ ] Build a clamp fixture and a repeatable phone position (ties into Aria's phone slots in hardware v2).
- [ ] Run condition C as soon as the gantry taps, then post the scatter and repeatability results here.

## Sources

- Apple: [UITouch.force](https://developer.apple.com/documentation/uikit/uitouch/force) · [majorRadius](https://developer.apple.com/documentation/uikit/uitouch/majorradius) · [isAssistiveTouchRunning](https://developer.apple.com/documentation/uikit/uiaccessibility/isassistivetouchrunning) · [UIScreen.isCaptured](https://developer.apple.com/documentation/uikit/uiscreen/iscaptured) `[Documented]`
- [User-sensitive mobile interfaces — tap and long-press durations (arXiv 1402.1036)](https://arxiv.org/pdf/1402.1036) `[Benchmark]`
- [zkSENSE — IMU response to touch](https://www.petsymposium.org/popets/2021/popets-2021-0058.php) · [HMOG](https://arxiv.org/pdf/1501.01199) `[Benchmark]`
