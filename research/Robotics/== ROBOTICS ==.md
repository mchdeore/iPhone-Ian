---
type: hub
---

# == ROBOTICS ==

Mechanisms, motion control, firmware, CAD, and how a machine drives a device: touch physics, HID, accessibility input paths.

## Notes

- [[Android Control Survey (Legacy)]] *(stale)*
- [[Gantry — Capacitive Touch Physics and Architecture]]
- [[Gantry — XY Builds and Microcontroller Choice]]
- [[Prior Art — Touchscreen Robots and Software Agents]] · also Machine Learning
- [[iOS Control — Alternative Accessibility Input Paths]] · also Cybersecurity
- [[iOS Control — AssistiveTouch Pointer Mechanics]]
- [[iOS Control — Exposing Device Controls to the Agent]] · also Machine Learning
- [[iOS Control — Raspberry Pi HID Input Converter]] · also Cybersecurity
- [[iOS Control — Relative Cursor Calibration and Visual Servoing]] · also Machine Learning

## From other domains

- [[Agents — Architecture and Perception Loop]] · from Machine Learning
- [[YOLO — Flask Closed-Loop Trainer App]] · from Machine Learning
- [[YOLO — Synthetic Data and Flash Training App]] · from Machine Learning
- [[YOLO — Training Hardware and Capture Rig]] · from Machine Learning
- [[Betting Apps — Behavioral and Automation Detection]] · from Cybersecurity
- [[Infra — Exposing a Windows Host and Low-Latency Streaming]] · from Cybersecurity
- [[iOS — Face ID, Autofill and 2FA Constraints]] · from Cybersecurity

## Exchange

- **Gives others:** physical rigs that generate data and run models in the real world; CAD and parts know-how.
- **Wants from others:** vision and control models (→ Machine Learning); what makes automation detectable (→ Cybersecurity).

## Key decisions

- **Hardware v2 (Aria, 2026-10-02):** CoreXY on MGN9 rails, MKS DLC32 + FluidNC, MG90S servo tap with a spring-loaded grounded stylus, 3 mm aluminium base, 2 phones (~34 × 32 × 5 cm, ~C$325). Full design: [hardware-concept-v2](https://github.com/mchdeore/iPhone-Ian/blob/main/aria/hardware-concept-v2.md). It supersedes the v1 Arduino/GRBL rod gantry.
- A grounded conductive stylus is mandatory for PCAP screens
- AssistiveTouch HID pointer is relative-only, so visual servoing beats dead reckoning
- Full Keyboard Access is the most promising path for typing

## Open

- HID keyboard vs pure gantry for typing
- Overhead camera vs screen capture over USB/AirPlay (do 2 simultaneous feeds work?)
- Bare phones only, or cases too?

## Help wanted (all domains)

```query
[type:request] -[status:answered]
```

## Adding to the pool

- New note → put it in the folder of its **main** domain, add a link to it on this hub, and fill in `domain`, `type`, `status`, `author`, `date`. Copy the frontmatter from any existing note.
- `domain: [ml, sports]`: list **every** domain it could help. Also link it under *"From other domains"* on those hubs. That's how research crosses over.
- Need something researched? Make a note with `type: request`, `status: seed`. It shows up on Help Wanted on every hub. Pick one up by adding `claimed_by: <you>`.
- Start every note with a 3-line **TL;DR**. Domain values: `sports` · `ml` · `security` · `robotics`.
