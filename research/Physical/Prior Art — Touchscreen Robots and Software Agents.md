---
tags: [prior-art, touchscreen-robot, capacitive, delta, gantry, agent]
status: answered
date: 2026-10-05
related:
 - ""
---

# Prior art: touchscreen robots & software agents

## Question

What has been built before? Commercial robots, DIY builds, and software agents that drive phones — what exists, what works, what lessons transfer to our physical iPhone-tapping robot?

## Key findings

### Commercial touchscreen robots

- **MATT (Adapta Robotics)** — 1–3 independently-moving capacitive stylus nibs. Tap, swipe, pinch, rotate. Curved/irregular screen support. Four-figure-plus pricing. `[Vendor claim]` https://www.mattrobot.ai/
- **Patent precedent** — WO2017051263A2 covers robot-arm + capacitive effector + coordinate-calibration at industrial/IP level. `[Documented]`

### DIY builds (most relevant to us)

- **TestDevLab "Tappy"** — delta-robot (3× Hitec HS-311 hobby servos), spring-loaded capacitive stylus. ~$80. Tap + swipe confirmed. Key lessons:
 - Grounding was necessary — dedicated ground wire from Arduino to stylus pen.
 - Early ball-joint slop fixed by switching to neodymium magnets + plastic linkages.
 - Browser-based calibration page, no app install needed.
 - Multi-touch not implemented (single end-effector).
 - https://www.testdevlab.com/blog/how-we-built-a-robot-for-automated-manual-mobile-testing

- **Instructables "Screen Tapping Robot"** — our design source of truth. Cartesian XY gantry, 3D-printed, Raspberry Pi 3. Details in . https://www.instructables.com/Screen-Tapping-Robot/

- **Single solenoid/servo tappers** — $10–40, fixed-point tap only. Simplest possible. Two documented builds:
 - https://hackaday.com/2012/05/04/reaching-out-to-a-touch-screen-with-a-microcontroller/
 - https://www.instructables.com/Screen-Tapping-Robot/

- **Touchscreen Testing Robot (ofer9430)** — lead screw + A4988 + SG90 servo, uses battery negative pole as capacitive tip. `[Community]` https://www.instructables.com/Robot-De-Testeo-Para-Pantalla-Touchscreen/

### Software agents (reference only — doesn't work for iPhone)

- **droidrun / mobilerun** — open-source LLM-agent for Android. Accessibility Service + ADB. Perception→planning→action loop. Closest software analog but requires ADB + dev options — dead end for iPhone. https://github.com/droidrun/mobilerun
- **AppAgent, Mobile-Agent, Android MCP wrappers** — thin orchestration layers around ADB/UIAutomator2. Not independent architectures.
- **BrainyBot** — CV robot taps phone to play games. Overlap with our project. `[Academic]` https://github.com/DeMaCS-UNICAL/TappingBot

## Gaps filled (2026-10-05)

Originally flagged gaps: "XY touchscreen robot," "CoreXY phone testing," "pen plotter touchscreen," "mobile GUI agent literature," X/Twitter. Now covered by:

- — dedicated research on XY/CoreXY gantry builds for phone automation
- — full literature survey of VLM GUI agents and vision grounding
- — iOS-specific Face ID, autofill, accessibility behavior

## Sources

- https://www.mattrobot.ai/
- https://www.testdevlab.com/blog/how-we-built-a-robot-for-automated-manual-mobile-testing
- https://www.instructables.com/Screen-Tapping-Robot/
- https://github.com/droidrun/mobilerun
- https://github.com/DeMaCS-UNICAL/TappingBot
- https://patents.google.com/patent/WO2017051263A2/en