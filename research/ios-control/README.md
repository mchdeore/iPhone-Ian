---
tags: [ios, index, MOC]
status: live
date: 2026-10-06
related:
  - "[[../Home]]"
  - "[[../Timeline]]"
---

# iOS Control Research

Everything about what happens when a robot taps an iPhone: biometrics, autofill, accessibility features, AssistiveTouch/HID alternatives.

| File | Question answered | Status |
|---|---|---|
| [[01-faceid-autofill-accessibility]] | Face ID lockout? Autofill behavior? VoiceOver risk? App login landscape? | Answered |
| [[02-assistivetouch-pointer]] | AssistiveTouch pointer mechanics, HID mouse/keyboard, lock screen behavior | Answered |
| [[03-relative-cursor-calibration]] | Relative cursor calibration, dead reckoning, visual servoing, PID | Answered |
| [[04-alternative-input-paths]] | Full Keyboard Access, Switch Control, Voice Control, Back Tap, Guided Access | Answered |

## Key decisions made

- Robot never triggers Face ID — always uses passcode fallback
- Disable triple-click Accessibility Shortcut (VoiceOver risk)
- Password fallback still universal on iOS apps in 2026
- "Sign in with Apple" buttons are dead ends for robot
- 2FA is hardest problem: prefer TOTP over SMS

## Open tension

HID keyboard for typing (via AssistiveTouch) vs pure gantry-only typing. See [[../yolo-training/13-exposing-device-controls]], [[../yolo-training/15-raspberry-pi-input-converter]], [[04-alternative-input-paths]]. Needs a decision in [[../../specs/]].

## What feeds into this

- [[../mechanical/README|Mechanical]] — stylus grounding, touch physics
- Phase 0 of [[../Timeline]]

## What this feeds

- [[../agent-ml/README|Agent & ML]] — CV must handle autofill QuickType bar
- [[../../specs/00-charter|Charter]] — iOS constraints shape the entire project