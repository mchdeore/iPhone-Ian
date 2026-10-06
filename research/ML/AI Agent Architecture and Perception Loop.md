---
tags: [agent, VLM, perception, planning, action-loop, droidrun]
status: answered
date: 2026-10-05
related:
  - "[[== ML CENTRAL ==]]"
---

# AI agent architecture — perception→planning→action loop

## Question

How should the perception→planning→action loop work for a vision-based AI agent driving a physical iPhone-tapping robot? What's the closest existing precedent?

## Key findings

### droidrun / mobilerun — closest existing software analog

Open-source framework wrapping Accessibility Service + ADB with an LLM-agent control loop. Installs on-device "Portal" app exposing UI tree + screenshots to host-side agent. Agent reasons over observed state (vision + structured tree) and issues taps/swipes/text/app-launch. `[Documented]` https://github.com/droidrun/mobilerun

Architecturally a perception→planning→action loop in software-only form. The perception and planning halves (VLM/tree-grounding + action planning) are largely reusable — regardless of whether action is `dispatchGesture` or a physical stylus moving to XY.

### Architecture for our physical agent

See full survey in . Summary:

```
Camera photo of iPhone screen
    │
    ▼
 [Perception] — UGround / OmniParser (Phase 2) → ZonUI-3B fine-tuned (Phase 3)
    │ bounding boxes + element descriptions
    ▼
 [Planning] — VLM (GPT-4V / Claude / Gemini) reasons over UI state
    │ "Tap the login button" → action: tap(x=342, y=518)
    ▼
 [Action] — screen coordinate → gantry coordinate → G-code → tap
    │
    ▼
 [Verification] — next camera frame → did it work? → retry or continue
```

**Perception and planning are separate concerns.** Perception benefits from fine-tuning on our domain (iPhone camera photos). Planning works fine with off-the-shelf VLMs.

### Key references (full details in )

- Mobile-Agent v3.5 / GUI-Owl-1.5 — 56.5 OSWorld, multi-agent architecture
- OS-Atlas — open-source GUI grounding foundation model
- ZonUI-3B — our fine-tuning target (3B params, single RTX 4090)
- GUI-Primitives — VLMs understand instructions but can't locate precisely (60-92% miss)

## Open questions / follow-ups

- What's the retry/error-recovery strategy when a tap misses?
- How do we handle dynamic content (loading spinners, animations, popups)?
- Sequential navigation RL — only after perception + calibration are solid (per existing note in `specs/02-firmware-and-software.md` §5.1).

## Sources

- https://github.com/droidrun/mobilerun
- See for full VLM/grounding sources