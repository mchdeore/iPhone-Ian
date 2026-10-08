---
type: research
status: in-progress
author: marc
date: 2026-10-07
tags: [machine-learning, cybersecurity, robotics, screen-capture, airplay, uxplay, quicktime, latency]
---

# Rig — iPhone Screen Capture Paths (USB, AirPlay, Multi-Phone)

**TL;DR**
- Hardware v2 drops the overhead camera in favour of **screen capture**. That decision hinges on Aria's open question: *do 2 simultaneous feeds work?*
- **Wired (USB → Mac, QuickTime/AVFoundation)** is the lowest-latency single-phone path.
- **UxPlay** (an open-source AirPlay receiver for Linux) can mirror wirelessly, and its `-m` (random MAC) option suggests **one instance per phone** for concurrency. That isn't proven for two phones, so it needs a test.
- Capture sets `UIScreen.isCaptured = true` on the phone, which camera capture doesn't. That's a detectability trade-off.

**Builds on:** Aria's hardware-concept-v2 §2 (camera decision), [[RL — Emulator-First Training and Sim-to-Real for the Rig]] (screen capture removes most of the visual gap), [[Betting Apps — Behavioral and Automation Detection]] §4.

## Options

| Path | Latency | Multi-phone | Notes |
|---|---|---|---|
| **USB → Mac (QuickTime / AVFoundation device)** | Lowest; avoids wireless lag [1] | Unconfirmed for >1 phone in QuickTime; AVFoundation can enumerate devices (test) | View-only [1]; capturing the QuickTime *window* in OBS added visible lag, so **grab frames from the device directly** [2] |
| **AirPlay → UxPlay (Linux)** | Depends on Wi-Fi | **One instance per phone** with `-m` random MAC (man page: "for concurrent UxPlay's"); `-nohold` controls takeover [3][4] | Same LAN required; `-vsync no` drops A/V sync when only video matters [3] |
| **HDMI adapter → USB capture card** | Low, stable | One card per phone | Lightning/USB-C to HDMI; HDCP-protected content blacks out |
| **Overhead camera** (v1) | Camera + exposure | One camera covers several phones | Needs ~28 cm of height (why v2 dropped it); doesn't set `isCaptured` |

## Detectability and security

- Mirroring/recording sets **`UIScreen.isCaptured`**, and betting/banking apps blur views or flag it ([[Betting Apps — Behavioral and Automation Detection]] §4). For our own test apps that doesn't matter; it's worth knowing when choosing a path.
- AirPlay over shared Wi-Fi exposes the stream to the LAN. Use an isolated network or a USB path ([[Security — STRIDE Threat Model for the Phone Rig]]).

## Test plan (answers Aria's §7 Q1)

1. One phone over USB → Mac: measure glass-to-frame latency (flash app shows a timestamp; capture → OCR → diff).
2. Two phones over USB on one Mac: do both enumerate as AVFoundation devices at once?
3. Two UxPlay instances (`-m`, distinct names and ports) on Linux: stable for 30 minutes?
4. Record latency p50/p95, frame drops and resolution for each.

## Pitch in

- [ ] Robotics: run tests 1–3 and fill the table with measured numbers. This unblocks the camera decision.

## Sources

1. [Dr.Fone — mirror iPhone to PC via USB](https://drfone.wondershare.com/mirror-to-pc/mirror-iphone-to-pc-via-usb.html) `[Community]`
2. [OBS forum — QuickTime capture lag](https://obsproject.com/forum/threads/iphone-mac-facebook-lag.127207/) `[Community]`
3. [UxPlay man page (Ubuntu)](https://manpages.ubuntu.com/manpages/noble/man1/uxplay.1.html) · [Debian man page](https://manpages.debian.org/testing/uxplay/uxplay.1) `[Documented]`
4. [UxPlay (FDH2) on GitHub](https://github.com/fdh2/uxplay) `[Documented]`
5. [Apple — UIScreen.isCaptured](https://developer.apple.com/documentation/uikit/uiscreen/iscaptured) `[Documented]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — Cybersecurity]] · [[State of — Robotics]]
