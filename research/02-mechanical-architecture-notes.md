# Track 2 — Mechanical Architecture: Notes

**Status:** Partial — logged from prior general survey. Covers touch physics + several DIY architectures found, but no direct search yet for CoreXY/pen-plotter-specific projects.

**Source:** `../sources/android_control_research.md` Part 3.

---

## How capacitive touch actually works (grounds every mechanical decision)

Modern phones use projected capacitive (PCAP) mutual-capacitance sensing: a grid of ITO electrodes under the cover glass. Each row/column intersection is a small capacitor with a baseline value the controller measures continuously. A grounded conductive object near an intersection draws away local field, reducing measured capacitance — the controller detects the dip and computes a coordinate.

**Grounding is the critical, easy-to-miss variable.** A human finger works because the body is a large, earth/self-capacitance-referenced conductor. A floating, ungrounded conductive tip often registers weakly or not at all. TestDevLab's Tappy build empirically hit this — had to add a dedicated ground wire from the Arduino to the stylus pen before touches registered reliably. **Direct implication for this project's spring-loaded passive-Z stylus hypothesis: the stylus/frame likely needs an explicit ground path back to a common reference, not just a conductive tip touching glass.**

Detection is capacitive, not pressure-based — mechanical force is irrelevant to whether a touch registers (though the actuator still needs consistent, repeatable contact geometry).

Sources: https://www.densitron.com/company/news/projected-capacitive-touch-sensor · https://software-dl.ti.com/msp430/msp430_public_sw/mcu/msp430/CapTIvate_Design_Center/1_83_00_08/exports/docs/users_guide/html/CapTIvate_Technology_Guide_html/markdown/ch_basics.html

## Architecture options found (maps to this project's Architecture A–D framing)

1. **Single solenoid/servo tapper (fixed-point)** — $10–40. Tap only, no swipe without added axes. Simplest possible build. https://hackaday.com/2012/05/04/reaching-out-to-a-touch-screen-with-a-microcontroller/
2. **Delta-robot, spring-loaded passive-Z stylus** — TestDevLab Tappy, ~$80. Tap + swipe confirmed. This is the closest documented analog to this project's "spring-loaded passive-Z" hypothesis, though delta kinematics ≠ this project's proposed Cartesian XY gantry. Needed mechanical iteration (magnet joints, plastic linkages) to kill positioning slop from ball-joint play — a concrete argument *for* a stiffer Cartesian gantry (belts/rails) over a servo-arm/delta design if minimizing calibration drift matters.
3. **XY CNC-style gantry, stepper-driven, capacitive-stylus Z-axis** — inferred $100–300 from typical NEMA17/GRBL/3D-printer-hobby-part pricing; no single documented reference project found with a full build log in the prior pass (flagged gap — this is exactly this project's target architecture and deserves a dedicated search pass: "XY touchscreen robot," "pen plotter touchscreen," "miniature XY gantry," "CoreXY" were in the seed list but not yet searched).
4. **Commercial multi-effector (MATT-class)** — 1–3 independently moving capacitive nibs, true simultaneous multi-touch (pinch/rotate), curved-screen capable. Four-figure-plus, out of DIY range but useful as an upper-bound capability reference.

## Multi-touch feasibility

Single end-effector rigs (the large majority of hobbyist builds found) are limited to one contact point at a time — sequential taps only, no true pinch/rotate. Two-point gestures require two independently movable effectors (mechanical analog of scrcpy's software "virtual finger" trick). True simultaneous multi-touch (MATT-class) needs multiple independently-actuated tips with independent XY(Z) control each — a substantial step up in mechanical complexity/cost from anything in the DIY range reviewed.

## Coordinate accuracy

Gantry/stepper designs can hit sub-millimeter mechanical accuracy — well within Android's own 48dp (several-mm) minimum touch-target guideline, so mechanical precision is rarely the limiting factor. **Calibration accuracy (mapping rig coordinate frame → screen coordinate frame) is the actual bottleneck** — this is why Tappy built a dedicated browser-based calibration step rather than relying on measured/assumed geometry. Servo-arm/delta designs lose some precision to kinematic-transform slop in ball/socket joints versus a true Cartesian gantry.

## Does modern phone hardware make this harder?

- Thinner glass generally **helps** (less capacitive attenuation).
- Edge-to-edge/curved ("waterfall") screens are a *geometric* problem, not electrical — a fixed-angle stylus calibrated for flat center may not contact reliably near curved edges where the surface normal changes (MATT specifically markets curved-screen handling as a differentiator, implying it's nontrivial for simpler rigs). Industry trend as of 2025–2026 is actually back toward flat panels, somewhat reducing this concern for newest flagships.
- No evidence that modern electrode density/sensitivity changes make actuation *harder* — if anything, higher sensitivity (partly driven by glove-touch/stylus support demand) makes reliable triggering easier than on older panels.

## Screen protector interference

Thin properly-applied protectors generally don't meaningfully block capacitive detection (glass itself already sits between electrode grid and finger by design). Thick/air-gapped protectors add attenuation and could push a marginal actuator design (weak grounding, borderline tip conductivity) into unreliable territory. [Inference, not universally confirmed in sources reviewed] — worth testing directly once a prototype exists rather than assuming either way.

## No phone modification required (any physical approach)

Every physical actuator method surveyed treats the phone as a fully opaque black box — no Developer Options, no USB debugging, no accessibility service, no root, nothing installed. This is the core value proposition versus every software method in Track 8/existing Part 1. The only "install" of any kind across all reviewed physical rigs is Tappy's optional browser-based calibration webpage, which leaves no persistent footprint.

## Cost table (as found, not project-specific BOM)

| Build class | Approx. cost | Source |
|---|---|---|
| Single solenoid/servo tapper | $10–40 | Hackaday, Instructables |
| Delta-robot + spring stylus, tap+swipe (Tappy) | ~$80 | TestDevLab |
| XY CNC-gantry, stepper + capacitive stylus Z | ~$100–300 (inferred from generic CNC/3D-printer part pricing, not a specific sourced build) | Inference only |
| Commercial multi-effector (MATT) | Undisclosed, four-figure-plus inferred | Inference |

## Gap flagged for Track 2 / Track 9

Track 2's real target — a documented Cartesian XY gantry (not delta) with passive spring-Z stylus — has **no directly-sourced reference build** in the prior pass. This is the single highest-value follow-up search: "XY touchscreen robot," "CoreXY phone testing," "pen plotter touchscreen," "GRBL phone automation."
