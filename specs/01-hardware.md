# 01 — Hardware Spec (the robot)

**Decision (D3):** start from the TestDevLab **"Tappy"** build (~$80) and improve
it for our iPhone-only, credential-typing use case.

See `research/02-mechanical-architecture-notes.md` for the underlying
capacitive-touch physics — all of it applies to iPhone unchanged.

---

## 1. What Tappy is (baseline)

- A **delta robot** using 3× hobby servos (Hitec HS-311).
- A **spring-loaded, pen-style capacitive stylus** as the end effector (passive Z:
  the spring provides consistent contact force).
- ~€70/~$80 in parts; ~10× cheaper than commercial rigs.
- **Confirmed working:** tap **and** swipe, after mechanical iteration.
- **Two known hard-won lessons** we inherit for free:
  1. **Grounding is mandatory.** A floating conductive tip registers weakly or
     not at all. Tappy needed a dedicated ground wire from the controller to the
     stylus. **We will design an explicit ground path from day one.**
  2. **Joint slop kills accuracy.** Tappy fixed positioning slop by switching
     ball-joints → neodymium magnets and metal → plastic linkage rods.

## 2. Where we improve on it ("a little better")

Ordered by expected value. Not all are committed — this is the menu.

| Upgrade | Why | Cost/effort |
|---|---|---|
| **Cartesian XY gantry instead of delta** | A stiff belt/rail gantry avoids the kinematic-transform slop that plagued Tappy's ball-joints, and calibration math is simpler (linear, not delta trig). This is the project's target architecture. **Reference build is the #1 research gap** — search "CoreXY phone testing", "pen plotter touchscreen", "GRBL phone automation". | $$ |
| **Steppers + GRBL controller** | Repeatable, homeable positioning; standard, cheap 3D-printer ecosystem (NEMA17 + control board). Host talks G-code over USB serial. | $$ |
| **Designed-in stylus grounding** | Turn Tappy's afterthought fix into a first-class, reliable ground reference. | $ |
| **Fixed iPhone cradle + overhead camera mount** | Rigid, repeatable phone position is what makes calibration hold. Camera is the agent's only "eyes" (black box). | $ |
| **Passive spring-Z stylus (keep from Tappy)** | Consistent contact force without a controlled Z axis; simplest thing that works. Contact is capacitive, not pressure-based, so we only need *consistent* contact, not *measured* force. | $ |

## 3. iPhone-specific mechanical notes

- **Flat vs. curved glass.** A fixed-angle stylus calibrated for a flat center may
  not contact reliably near curved/"waterfall" edges (the surface normal
  changes). Recent iPhones trend flat, which helps. Pick a first target model and
  measure. *(Inference — verify on real hardware.)*
- **Screen protectors.** Thin, well-applied protectors don't meaningfully block
  capacitive sensing. Thick/air-gapped ones can push a marginal design into
  unreliable territory — test with the actual phone.
- **Reachability.** The gantry work area must cover the full screen **including
  the on-screen keyboard**, since credential typing taps individual keys near the
  bottom edge.

## 4. Accuracy target

- Gantry mechanical accuracy of sub-millimeter is achievable and is **well within**
  iOS's comfortable touch-target size (Apple's ~44pt / several-mm minimum). So,
  as Tappy found, **mechanical precision is not the limiting factor —
  calibration is.** Budget effort accordingly (see `02-training-and-control.md`
  §calibration).

## 5. Rough BOM direction (not final)

| Class | Approx. cost | Source of estimate |
|---|---|---|
| Tappy-as-is (delta + servos + stylus) | ~$80 | TestDevLab (documented) |
| XY gantry (steppers + GRBL board + rails/belts + stylus) | ~$100–300 | Inferred from generic 3D-printer/CNC part pricing — **not a sourced build** |
| + overhead camera + phone cradle | +$20–60 | Inference |

A finalized, sourced BOM is a Phase-1 deliverable once the gantry reference build
question is settled.
