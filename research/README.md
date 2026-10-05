# Research notes — index & status

## Workflow (read this first)

Before you research anything:

1. Check [`questions.md`](questions.md) — did we already ask this? If yes, read
   the linked notes. Don't re-research.
2. If the question is new, add it to `questions.md` with status `Researching`.
3. Copy [`TEMPLATE.md`](TEMPLATE.md) into the right subfolder, fill it in.
4. When done, mark the question `Answered` in `questions.md` and link the note.

When research turns into a decision, it moves to [`../specs/`](../specs/).
Research notes stay raw — never polish them. Specs are polished.

---

These notes were seeded from an earlier general survey that was **Android-framed**.
The project has since committed to **iPhone only**. Read them with that pivot in
mind: the *mechanical / touch-physics* findings transfer directly to iOS, but the
*software-control* findings mostly do **not** (see below).

| File | Topic | Transfers to iPhone? | Status |
|---|---|---|---|
| `01-prior-art-notes.md` | Prior art: touchscreen robots (Tappy, MATT) + software agents | Robot prior art: **yes**. Software agents: partial. | Answered |
| `02-mechanical-architecture-notes.md` | Capacitive (PCAP) touch physics, gantry vs delta, grounding, calibration, stylus tips | **Yes, fully** — PCAP physics is identical on iPhone | Answered |
| `05-ai-agent-architecture-notes.md` | Perception→planning→action loop for a phone-driving agent | Loop design: **yes**. droidrun specifics: no (Android). | Answered (filled by VLM survey) |
| `06-vlm-gui-agent-survey.md` | VLM GUI agents, vision grounding, fine-tuning vs prompting, architecture design | **Yes** — iOS-agnostic, camera-photo-specific | Answered 2026-10-05 |
| `07-ios-control-constraints.md` | iOS-specific: Face ID, autofill, accessibility, stylus behavior, app login landscape | **Yes** — iPhone-specific | Answered 2026-10-05 |
| `08-xy-gantry-builds.md` | XY/CoreXY gantry builds, microcontroller choice (Arduino+GRBL), Instructables robot deep dive | **Yes** — mechanical | Answered 2026-10-05 |
| [`yolo-training/`](yolo-training/README.md) | Efficient YOLO training: dataset recipe, synthetic flash-app data, training hardware | **Yes** — iOS-agnostic | Researched 2026-10-04 |
| `android-control-survey.md` | 88 KB survey of Android software/USB control (ADB, scrcpy, accessibility, UHID/AOA) | **Mostly no** — iOS has no equivalent open control surface | Legacy background |

## Reusable parts & resources → now in the specs

The reusable-parts research (CAD libraries, OpenBuilds/ACRO mechanics, GRBL/FluidNC
firmware, Tapster/Tappy stack, OpenCV homography, UGround/OmniParser grounding
models, motor/servo/stepper libraries, YouTubers/communities) has been split into
the two authoritative specs, each with its own citations section:

- Physical build + CAD library → [`../specs/01-hardware.md`](../specs/01-hardware.md)
- Firmware + software + ML → [`../specs/02-firmware-and-software.md`](../specs/02-firmware-and-software.md)

## Why `android-control-survey.md` is kept but demoted

It documents *why software control of a stock phone is hard*, which is the core
argument for the physical-robot approach. On Android there were still several
software paths (ADB, scrcpy OTG/AOA, accessibility `dispatchGesture`). **On a
stock, non-jailbroken iPhone essentially none of these exist** for arbitrary
third-party automation — which is exactly why we go physical. Keep it as
supporting evidence, not as an implementation guide.

## Biggest open research gaps (carried into `specs/00-charter.md`)

- **Cartesian XY-gantry reference build** with a passive spring-Z capacitive
  stylus — **FOUND:** Instructables "Screen Tapping Robot"
  (https://www.instructables.com/Screen-Tapping-Robot/), now the design source of
  truth (`specs/01-hardware.md`), deep-dived in `08-xy-gantry-builds.md`.
- **iOS-specific control constraints** — Face ID / passkey / autofill behavior
  when a robot (not a human) is driving — **ANSWERED** in `07-ios-control-constraints.md`.
- **Vision grounding for iOS screens** — the agent sees the screen through a
  camera (black box), not an accessibility tree — **ANSWERED** in `06-vlm-gui-agent-survey.md`.
  Camera-photo grounding is an open research gap; our approach: Phase 2 zero-shot
  (UGround/OmniParser), Phase 3 fine-tune (ZonUI-3B on our captures).