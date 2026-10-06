---
tags: [system]
---

# Software System

Central node for all system-level research. Every note in this cluster feeds into how the software interacts with the iPhone and the gantry.

What we know:

- Robot never triggers Face ID — always uses passcode fallback. Passcode entry is a standard number pad
- Autofill can help (tap suggestion + auth) or hinder (extra UI element). CV must handle both
- VoiceOver is a risk — disable triple-click Accessibility Shortcut
- Password fallback still universal on iOS apps in 2026. "Sign in with Apple" buttons are dead ends
- 2FA is hardest problem: prefer TOTP (offline computation) over SMS
- AssistiveTouch + HID pointer is relative-only on iOS. Visual servoing beats dead reckoning
- Full Keyboard Access most promising for typing; Switch Control needs setup
- Android survey kept as evidence that software-only iPhone control is not viable

iOS constraints: [[iOS Control Constraints — Face ID, Autofill, Accessibility]]
Pointer: [[AssistiveTouch Pointer Mechanics for Robot Control]]
Cursor: [[Relative Cursor Calibration and Visual Servoing]]
Alt inputs: [[Alternative iOS Accessibility Input Paths]]
Legacy: [[Android Software Control Survey (Legacy)]]

## Open decision

HID keyboard for typing vs pure gantry-only. Needs resolution before Phase 1 BOM.