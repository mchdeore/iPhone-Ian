# Research notes — index & status

These notes were seeded from an earlier general survey that was **Android-framed**.
The project has since committed to **iPhone only**. Read them with that pivot in
mind: the *mechanical / touch-physics* findings transfer directly to iOS, but the
*software-control* findings mostly do **not** (see below).

| File | Topic | Transfers to iPhone? | Status |
|---|---|---|---|
| `01-prior-art-notes.md` | Prior art: touchscreen robots (Tappy, MATT) + software agents | Robot prior art: **yes**. Software agents: partial. | Partial |
| `02-mechanical-architecture-notes.md` | Capacitive (PCAP) touch physics, gantry vs delta, grounding, calibration | **Yes, fully** — PCAP physics is identical on iPhone | Partial |
| `05-ai-agent-architecture-notes.md` | Perception→planning→action loop for a phone-driving agent | Loop design: **yes**. droidrun specifics: no (Android). | Barely started |
| `android-control-survey.md` | 88 KB survey of Android software/USB control (ADB, scrcpy, accessibility, UHID/AOA) | **Mostly no** — iOS has no equivalent open control surface | Legacy background |

## Why `android-control-survey.md` is kept but demoted

It documents *why software control of a stock phone is hard*, which is the core
argument for the physical-robot approach. On Android there were still several
software paths (ADB, scrcpy OTG/AOA, accessibility `dispatchGesture`). **On a
stock, non-jailbroken iPhone essentially none of these exist** for arbitrary
third-party automation — which is exactly why we go physical. Keep it as
supporting evidence, not as an implementation guide.

## Biggest open research gaps (carried into `specs/00-charter.md`)

- **Cartesian XY-gantry reference build** with a passive spring-Z capacitive
  stylus — no directly-sourced build found yet (highest-value hardware search).
- **iOS-specific control constraints** — Face ID / passkey / autofill behavior
  when a robot (not a human) is driving; what "login" can and cannot mean.
- **Vision grounding for iOS screens** — the agent sees the screen through a
  camera (black box), not an accessibility tree, so screen→coordinate grounding
  and calibration is the crux.
