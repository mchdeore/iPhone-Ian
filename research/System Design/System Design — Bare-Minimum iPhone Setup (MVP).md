---
type: research
status: in-progress
author: marc
date: 2026-10-07
tags: [system-design, robotics, cybersecurity, mvp, iphone, bill-of-materials]
---

# System Design — Bare-Minimum iPhone Setup (MVP)

**TL;DR**
- The smallest setup that plays a card game on a real iPhone: **a spare iPhone, a clamp, a grounded stylus on any XY motion platform, a USB cable to a Mac for screen capture, and ~300 lines of Python.**
- We both have 3D printers, so the **printer itself can be the interim gantry** (it already speaks G-code) while hardware v2 gets built.
- First milestone: tap "New Game", then complete one Solitaire move with verification.

**Builds on:** [[System Design — Card-Playing Gantry Rig Architecture]], Aria's hardware v2 (`aria/hardware-concept-v2.md` in the repo), [[Rig — iPhone Screen Capture Paths (USB, AirPlay, Multi-Phone)]].

## Bill of materials, two tiers

| Item | Tier 0: this week, ~$0–30 | Tier 1: hardware v2 |
|---|---|---|
| Phone | Spare or old iPhone, test Apple ID, no personal accounts | Same, ×2 slots |
| Motion | **Existing 3D printer** (Marlin/Klipper) with a stylus where the nozzle would be | CoreXY on MGN9, MKS DLC32 + FluidNC |
| Z / tap | Printer Z axis (slow but fine for turn-based) | MG90S servo, spring-loaded |
| Stylus | Capacitive stylus tip + **wire to machine ground** (mandatory for PCAP) | Same, conductive silicone tip |
| Fixture | Printed phone cradle bolted to the bed | Phone slots in the base plate |
| Screen in | **USB → Mac**, AVFoundation capture | Same, or UxPlay per phone |
| Host | Mac/PC with Python: `opencv-python`, `pyserial`, `numpy` | + GPU box for models |

Capacitive physics and grounding: [[Gantry — Capacitive Touch Physics and Architecture]]. A Tapster-class delta was ~€250 with an Arduino, 3 servos and printed parts [1]. The printer route is cheaper still, because we own the printers.

## Phone prep checklist

- [ ] Auto-Lock **Never**, brightness fixed, True Tone and Night Shift off (stable colours for perception)
- [ ] Notifications off / Focus on (they cover cards, and they're a prompt-injection channel: [[Security — Prompt Injection and Pop-up Attacks on GUI Agents]])
- [ ] An offline card game installed; ads off if possible
- [ ] Triple-click Accessibility Shortcut disabled ([[iOS — Face ID, Autofill and 2FA Constraints]])
- [ ] Orientation lock on, so the layout doesn't rotate mid-game

## Software, minimum viable (in this order)

1. **`capture.py`:** grab frames from the USB-attached iPhone (AVFoundation) and save PNGs.
2. **`calib.py`:** tap 4 known screen points by jogging, then fit a screen px → machine mm homography ([[Rig — Camera-to-Screen Calibration with ChArUco]]; with screen capture, px are exact).
3. **`robot.py`:** `tap(x, y)`, `drag(path)`; G-code over serial (`G0` for moves, Z down/dwell/up); soft limits = screen rectangle.
4. **`see.py`:** template-match card corners, or a pretrained playing-card YOLO ([[System Design — Reading Cards from the Screen]]).
5. **`play.py`:** state machine + a greedy move picker → plan → act → verify.

## Day-by-day

| Day | Done when |
|---|---|
| 1 | Phone clamped; stylus grounded; one manual G-code tap registers |
| 2 | Frames captured on the Mac at ≥10 fps |
| 3 | Calibration error ≤1 mm across the screen |
| 4 | `tap()` hits "New Game" 20/20 times |
| 5 | `drag()` moves a card between piles 18/20 |
| 6 | Card recognition ≥99% on 200 captured frames |
| 7 | Plays a full Solitaire game with verification, logging each step |

## Pitch in

- [ ] Robotics: printed stylus mount + ground wire for one of our printers; post the Day 1 video.
- [ ] Anyone: test whether USB capture works while the printer runs (cable routing, EMI).

## Sources

1. [TapsterBot overview — cost, design (SlideShare)](https://www.slideshare.net/slideshow/dont-fear-our-new-robot-overlords-a-new-way-to-test-on-mobile/37275458) `[Community]`
2. [TapsterBot GitHub wiki — Robot Framework keywords](https://github.com/pylapp/tapsterbot/wiki/07-%5C--Drive-the-robot:-Robot-Framework-keywords) `[Documented]`
3. [TestDevLab — building a robot for manual mobile testing](https://www.testdevlab.com/blog/how-we-built-a-robot-for-automated-manual-mobile-testing) `[Community]`

## Related

- **Summary:** [[State of — System Design]] · [[State of — Robotics]] · [[State of — Cybersecurity]]
- **See also:** [[Gantry — FluidNC Control Interface (Jogging, Soft Limits, Realtime)]] · [[System Design — Drag, Tap and Verify Primitives for Card Moves]]
