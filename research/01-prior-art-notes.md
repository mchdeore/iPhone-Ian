# Track 1 — Prior Art & Literature: Notes

**Status:** Logged from a prior general-survey research pass (Android software/USB control + physical actuator landscape). Not a fresh pass against this project's specific search-term list in RESEARCH_PIPELINE.md §4 — treat as a head start, not track-complete.

**Source:** Full original report at `../sources/android_control_research.md` (this project's parent research session, Sept 2026).

---

## Commercial / documented physical touchscreen robots

- **MATT (Adapta Robotics)** — commercial touchscreen-test robot using 1–3 independently-moving capacitive stylus "nibs" as interchangeable end effectors. Explicitly supports tap, swipe, pinch, and rotate (genuine multi-touch via multiple independently-actuated contact points). Markets specific handling of curved/irregular screens without device modification. Pricing not publicly disclosed; inferred four-figure-plus (commercial test-automation hardware class). [Developer/researcher report / vendor claim] — https://www.mattrobot.ai/

- **TestDevLab "Tappy"** — DIY delta-robot (3× Hitec HS-311 hobby servos) with spring-loaded pen-style capacitive stylus end effector. Full build write-up, most relevant single prior-art project for this project's XY/spring-Z hypothesis. Key details:
  - Cost: ~€70 (~US $80) in parts, explicitly noted as ~10x cheaper than a pre-built rig.
  - Calibration: two-stage — kinematic delta-arm calibration + browser-based screen-calibration page (loads a calibration webpage on the device under test, no app install needed).
  - Iteration history: early builds had moving-platform/ball-joint reliability problems; switching bearing balls→neodymium magnets and metal→plastic linkage rods fixed it.
  - **Grounding was necessary**: added a dedicated ground wire from the Arduino to the stylus pen for the phone to reliably register contact — direct empirical confirmation that capacitive actuators need a ground reference, not just conductive contact.
  - Confirmed working: tap AND swipe, after mechanical redesign.
  - Multi-touch: not implemented (single end-effector).
  - https://www.testdevlab.com/blog/how-we-built-a-robot-for-automated-manual-mobile-testing

- **Single solenoid/servo "tapper" builds** — simplest documented class, single fixed-point tap only (no swipe without added axes). $10–40 in parts.
  - https://hackaday.com/2012/05/04/reaching-out-to-a-touch-screen-with-a-microcontroller/
  - https://www.instructables.com/Screen-Tapping-Robot/

- **Patent precedent** — WO2017051263A2, "Robot arm for testing of touchscreen applications." Documents a robot-arm + conductive/capacitive effector + coordinate-calibration architecture at an industrial/IP level; consistent with the general pattern above. https://patents.google.com/patent/WO2017051263A2/en

- Secondary trade-press coverage of automated touchscreen accuracy testing devices (general validation that this equipment category exists commercially): https://phonearena.com/news/Automated-touchscreen-test-device-shows-off-the-accuracy-of-smartphones_id10418

## Software-side prior art relevant to the "AI agent" and "arbitrary phone" framing

- **droidrun / mobilerun** — open-source LLM-agent framework for Android. Installs an on-device "Portal" app running an Accessibility Service that exposes the UI tree + screenshots to a host-side agent; agent issues taps/swipes/text/app-launch based on LLM reasoning over observed UI state. This is the closest *software* analog to the project's "vision-based AI agent operating an arbitrary phone" goal — worth comparing against as the all-software alternative to the physical-dock approach. Requires ADB install + manual accessibility-service enable (Android 15 Restricted Settings friction if sideloaded). https://github.com/droidrun/mobilerun
- Related LLM-driven mobile agent wrappers noted but not deep-dived: AppAgent, Mobile-Agent, assorted "Android MCP server" tool wrappers — architecturally thin wrappers around ADB/UIAutomator2, not independent mechanisms. Worth a dedicated literature search (arXiv/ACM/IEEE) for the academic "mobile GUI agent" / "vision-language mobile agent" line — **not done in the prior pass**, flagged as a gap.

## Gaps against this project's actual search-term list (not covered by the prior pass)

The prior research was framed around *software Android control + physical actuator survey*, not this project's specific angle. It did **not** search: "phone GUI agent," "embodied mobile agent," "physical computer-use agent," "smartphone accessibility robot," "miniature XY gantry," "CoreXY," "pen plotter touchscreen," Google Scholar/arXiv/ACM/IEEE academic literature, or X/Twitter. Track 1 should still be treated as open for a dedicated pass against those terms.
