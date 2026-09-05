# Development Pipeline

How we build `iPhone-Ian`, stage by stage. Each stage has a **goal**, what to
**build/reuse**, a **Definition of Done** (the exit criterion), the **key risk**,
and **the one check** that proves it works before moving on.

**North star:** a laptop command like `login` makes a dumb, deterministic robot
physically drive a stock iPhone — vision + ML decide *what* to tap, the hardware
only knows *move here, tap*.

Cross-references: decisions in [`specs/00-charter.md`](specs/00-charter.md),
hardware in [`specs/01-hardware.md`](specs/01-hardware.md), firmware/software/ML in
[`specs/02-firmware-and-software.md`](specs/02-firmware-and-software.md).

---

## Your proposed stages (for the record)

1. Build the two axes and the click mechanism — something that moves and registers
   touch points on a plane.
2. Develop deterministic input.
3. Add video input to the computer and let the computer steer the movement.
4. Do everything from the laptop — a deterministic moving platform the software
   fully drives.

**Verdict: agreed on the backbone.** The ordering (mechanics → deterministic
control → vision-guided → autonomy) is correct and low-risk. Below is the same
plan, sharpened: one fail-fast test pulled to the front, calibration made explicit,
and Stage 4 split into "AI steers" vs. "real tasks + credentials."

---

## Stage 0 — Fail-fast: prove the touch registers ⚡ (½ day, ~$15)

*Do this before building anything mechanical.* The biggest unknown isn't motion —
it's whether a **robot-held capacitive stylus even registers on the iPhone**. Tappy
had to add a ground wire before touches worked at all.

- **Build:** a capacitive stylus tip on a stick, wired to a common ground
  (USB/Arduino GND), pressed by hand onto the iPhone. Nothing motorized.
- **Reuse:** Tappy's grounding note (hardware spec §3.1).
- **DoD:** the iPhone reliably registers taps from the grounded stylus, and *fails*
  when ungrounded (proving grounding is the variable).
- **Risk:** stylus tip/grounding won't trigger PCAP sensing → whole approach at risk.
- **The one check:** open the iPhone Notes app; the grounded stylus draws, the
  floating one doesn't.

> If this fails, stop and solve grounding/tip conductivity — everything else depends
> on it.

---

## Stage 1 — Two axes + tap: motion on a plane (your Stage 1)

- **Goal:** a rig that moves a stylus to any (x, y) over the phone and taps.
- **Build:** the simplest workable frame — start at **Tapster "Push Button Robot"**
  simplicity or a small 2-axis gantry (hardware spec §3.4, §4). Add the servo/​spring
  tap (§6). Rigid, repeatable phone mount (printed clamp, §5).
- **Reuse:** Tapster/OpenBuilds designs, printed CAD from the library (§5).
- **DoD:** by hand-jogging, the stylus can reach every corner of the screen **and
  register a tap** at each (Stage 0 grounding carried through).
- **Risk:** frame flex / backlash; stylus can't reach screen edges (esp. keyboard).
- **The one check:** jog to the four screen corners + center; all five register a
  touch in a calibration app.

---

## Stage 2 — Deterministic input: the dumb, known-good interface (your Stage 2)

- **Goal:** the rig accepts simple coordinate commands from the laptop and executes
  them **repeatably**. Firmware holds *no logic*.
- **Build:** pick a control route (firmware/software spec §4.1):
  - ⭐ **GRBL/FluidNC + G-code** (`G0 X.. Y..` then a tap) for steppers, or
  - **Firmata + pyFirmata** (Tapster's way) for a servo-based rig.
  - Home the axes so the coordinate frame is repeatable across power cycles.
- **Reuse:** GRBL / pyFirmata / python_to_GRBL streamer.
- **Minimal contract:** `move(x, y)`, `tap()`, later `down()/up()`. That's it.
- **DoD:** a laptop script commands `move(x,y); tap()` and the same input lands on
  the same spot every run (repeatability, not yet screen-aware).
- **Risk:** non-repeatable positioning (lost steps, no homing); host↔board comms.
- **The one check:** script taps the same target 20× from a cold start; all 20 hit
  within a small tolerance (e.g. < 2 mm) — a tiny assert-based test.

---

## Stage 3 — Vision + calibration: the computer sees and steers (your Stage 3)

*This is where the real work is — calibration is the accuracy bottleneck.*

- **Goal:** an overhead camera lets the laptop map a **screen pixel → robot (x, y)**,
  so software can say "tap *there*" from an image.
- **Build:**
  - Fixed overhead camera — **just a USB webcam** with locked focus + a rigid mount
    (hardware spec §9.1; camera specs barely matter, mount rigidity + glare do).
  - **Software-first (do before the rig is finished):** prototype the OpenCV
    homography against a **static photo** of the phone on the bench — proves the
    screen-pixel → coordinate math with zero moving parts.
  - **Build the target-practice trainer app here** (software spec §5.1): a local web
    page flashes a target, the robot taps, the page reports where the tap actually
    landed. It *is* your calibration data source **and** your accuracy score. No app
    install — it runs in mobile Safari (Tapster's browser-calibration trick).
  - **Calibration:** OpenCV homography (camera px → screen rect → gantry XY) refined
    from the trainer app's hits (software spec §5, §5.1).
- **Reuse:** OpenCV `findHomography`; Tapster calibration page; CV-robot references.
- **DoD:** click a point in the camera feed on the laptop → the stylus taps that
  exact point on the phone. Closed loop is *human-in-the-loop* here (you pick the
  point, computer steers the motion).
- **Risk:** calibration drift, lens distortion, parallax; the hardest stage.
- **The one check:** click 10 random points in the live camera view; the physical
  taps land on them (verified by an on-screen grid). Median error logged.

---

## Stage 4 — Autonomy: the agent decides what to tap (first half of your Stage 4)

- **Goal:** replace the human-picking-points with a model. Give a command, the
  system finds the target on screen and taps it — end to end from the laptop.
- **Build:** perception + planning loop (software spec §6, §7):
  - Off-the-shelf **UGround / OmniParser + VLM** (zero-shot — no training yet) turns
    "tap the login button" into a screen coordinate.
  - Wire it to Stage 3's calibration + Stage 2's motion contract.
  - Verify each action against the next camera frame; retry/abort on mismatch.
- **Reuse:** UGround / OmniParser / SeeClick; BrainyBot as a working precedent
  (it already plays games by looking + tapping).
- **DoD:** commands `open <app>`, `tap <label>`, `enter` work autonomously on a
  couple of real screens.
- **Risk:** grounding-model accuracy on iOS screens; latency.
- **The one check:** from a cold home screen, `open Settings` → `tap Wi-Fi`
  succeeds unattended, 5/5 times.

---

## Stage 5 — Real tasks + credentials + hardening (second half of your Stage 4)

- **Goal:** the actual product — `login`, with secrets pulled from a vault, safely.
- **Build:** command vocabulary (software spec §8) + the credential path (§9):
  - Host-side vault (Keychain / 1Password CLI / `sops`+`age`); agent requests the
    specific secret at the moment of use; **never logs or stores it**.
  - Scrub any training capture that shows a secret.
- **Reuse:** existing secret managers — don't build one.
- **DoD:** `login <target>` types credentials into a real login form and submits,
  with zero secret material in logs, screenshots, or git.
- **Risk (security-critical):** credential leakage; iOS biometric/passkey-only
  logins the robot can't satisfy (scope `login` to typeable flows).
- **The one check:** run `login`; grep all logs/artifacts afterward — the secret
  never appears.

---

## Cross-cutting threads (true in every stage)

- **Keep firmware dumb.** All intelligence lives on the laptop/host. This is the
  whole reason the plan de-risks: hard problems stay in fast-to-iterate software.
- **Calibration is the bottleneck**, not motor precision — invest effort in Stage 3.
- **Security is not a final bolt-on** — the "no secrets in repo / vault-only" rules
  hold from day one (`.gitignore` already enforces the repo side).
- **Prefer reuse** (Tapster, OpenBuilds, GRBL, OpenCV, UGround) over building.

## Fail-fast order (prove the scary things early)

1. **Grounding / touch registers** (Stage 0) — cheapest, most fundamental.
2. **Positioning repeatability** (Stage 2 check).
3. **Calibration accuracy** (Stage 3 check).
Everything after those is iteration, not existential risk.

## Mapping to the charter roadmap

| DEVELOPMENT.md | charter §7 phase |
|---|---|
| Stage 0–1 | Phase 1 — Mechanical prototype |
| Stage 2 | Phase 1/2 — control |
| Stage 3 | Phase 2 — perception + calibration |
| Stage 4 | Phase 2/3 — agent + (optional) training |
| Stage 5 | Phase 4 — commands + credentials |
