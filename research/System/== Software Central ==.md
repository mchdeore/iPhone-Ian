---
tags: [system]
---

# == SOFTWARE CENTRAL ==

How software interacts with iPhone and gantry. iOS constraints, accessibility paths, HID alternatives.

## Research

- [[iOS Control Constraints — Face ID, Autofill, Accessibility]]
- [[AssistiveTouch Pointer Mechanics for Robot Control]]
- [[Relative Cursor Calibration and Visual Servoing]]
- [[Alternative iOS Accessibility Input Paths]]
- [[Android Software Control Survey (Legacy)]]

## Key decisions

- Robot always uses passcode fallback. Never triggers Face ID
- VoiceOver is a risk. Disable triple-click Accessibility Shortcut
- Password fallback universal on iOS in 2026. "Sign in with Apple" dead end
- 2FA: prefer TOTP over SMS
- AssistiveTouch HID pointer is relative-only. Visual servoing beats dead reckoning
- Full Keyboard Access most promising for typing

## Open

- HID keyboard vs pure gantry for typing. Decide before Phase 1