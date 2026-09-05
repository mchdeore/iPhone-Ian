# 00 — Project Charter

**Project:** iPhone Accessibility Robot (`iPhone-Ian`)
**Status:** Research + spec. Nothing built yet.
**Owner:** mchdeore

---

## 1. One-sentence goal

Build a physical robot that drives a **stock, unmodified iPhone** by tapping its
screen, controlled by a vision-based AI agent that responds to high-level
commands (`login`, `enter`, `exit`, …) and pulls any needed secrets from a
host-side vault.

## 2. Decisions set in concrete

These are fixed for now. Everything else is open for iteration.

| # | Decision | Notes |
|---|---|---|
| D1 | **Target is iPhone / iOS only.** | No Android. The Android research is demoted to background. |
| D2 | **Physical actuation** — the robot touches the glass. | No jailbreak, no MDM, no developer provisioning, nothing installed on the phone. Black box. |
| D3 | **Base platform: TestDevLab "Tappy" (~$80), improved.** | Start from the documented build, then stiffen/upgrade. See `01-hardware.md`. |
| D4 | **An ML training rig / data-collection app is a first-class deliverable.** | We explicitly invest in training the agent to perform well, not just scripting it. See `02-training-and-control.md`. |
| D5 | **Command-driven, credential-aware.** | Accepts intents like `login`/`enter`/`exit`; retrieves credentials automatically so the human never hand-types them. |

## 3. Scope boundary vs. HomeLab

- **HomeLab** = the permanent home PC / Linux server + CI/CD. That is where the
  *host* runs — the machine that executes the agent, holds the credential vault,
  and talks to the robot's controller. HomeLab's repo keeps all server/CI-CD
  content.
- **This repo (`iPhone-Ian`)** = everything about making a robot control the
  phone: research, hardware design, the agent, the training rig. It is *built on
  top of* HomeLab but versioned separately.

Rule of thumb: **if it would exist without the robot, it's HomeLab. If it only
exists to drive the phone, it's here.**

## 4. Why physical, on iPhone specifically

A stock iPhone offers no general third-party control surface:

- No ADB equivalent for arbitrary input injection.
- Apple's automation surfaces are constrained: Shortcuts (only app-exposed
  actions), Accessibility (Voice Control / Switch Control / AssistiveTouch),
  XCUITest (needs a paired Mac + developer provisioning), MDM (enterprise
  enrollment). None satisfy "arbitrary, zero-install, on any phone I set it in
  front of."
- Therefore: **touch the glass like a human would.** The capacitive-touch
  physics (`research/02-mechanical-architecture-notes.md`) apply identically to
  iPhone, so that research transfers fully.

*(This is the project's central bet. If the black-box / zero-install constraint
were relaxed, a Mac + XCUITest path would be far cheaper — worth a conscious
re-check before committing hardware money. Labeled as the key assumption to
validate.)*

## 5. iOS-specific constraints to design around

- **Biometrics for login.** Many iOS logins now prefer Face ID / passkeys /
  iCloud Keychain autofill — a robot can't present a face or fingerprint. So
  "`login`" means: **type username + password into fields** for sites/apps that
  still accept typed credentials, or trigger an autofill flow the human then
  approves. Passkey-only logins are out of scope for the robot.
- **No accessibility tree.** Because the phone is a black box, the agent cannot
  read iOS's view hierarchy. Perception must be **camera-based** (an overhead
  camera) + OCR / vision grounding. This makes calibration (camera px → screen
  coord → gantry coord) the crux — consistent with the Tappy team's finding that
  *calibration, not mechanical precision, is the bottleneck*.
- **Text entry** happens by tapping the on-screen keyboard, key by key (slow but
  universal), unless a paste/autofill shortcut is available.

## 6. Security (non-negotiable)

Credential handling is the highest-risk part of this project.

- **No secrets in this repo. Ever.** `.gitignore` excludes `.env`, `secrets/`,
  keys, and vault files.
- Credentials live in a **real secret store on the HomeLab host** (candidates:
  macOS Keychain, 1Password CLI, or `age`/`sops`-encrypted files). The agent
  requests a secret at the moment it's needed and never logs its value.
- The robot **types** secrets onto the phone; secrets should not be persisted in
  action logs, screenshots, or training data. Screenshots captured for training
  must be scrubbed of any frame where a secret is visible in a field.
- Treat the credential-retrieval command path as a trust boundary: validate
  which secret is being requested for which target before releasing it.

## 7. Roadmap (phased)

**Phase 0 — Research close-out (here, now).**
- [ ] Dedicated search for a **Cartesian XY-gantry** reference build (highest-value gap).
- [ ] Confirm the iOS control constraints above (biometrics/autofill behavior under robot control).
- [ ] Decide: is the black-box constraint hard? (the §4 assumption check).

**Phase 1 — Mechanical prototype.**
- [ ] Build/adapt a Tappy-class rig; add the grounding path (known Tappy gotcha).
- [ ] Rig a fixed iPhone mount + overhead camera.
- [ ] Nail the calibration routine (camera → screen → gantry).

**Phase 2 — Perception + control loop.**
- [ ] Off-the-shelf VLM/OCR grounding → tap coordinates (no training yet).
- [ ] Implement the `tap`/`swipe`/`type` primitives against the gantry.

**Phase 3 — Training rig.**
- [ ] Data-collection app: record (screen image, command, action, outcome).
- [ ] Fine-tune / evaluate a grounding model; close the loop with success metrics.

**Phase 4 — Commands + credentials.**
- [ ] Intent vocabulary (`login`/`enter`/`exit`/…) → action sequences.
- [ ] Vault integration with the security rules in §6.

## 8. Open questions

- Repo/brand name — `iPhone-Ian` is a placeholder.
- Which specific iPhone model(s) are the first targets (screen size/curvature
  affects the mount and calibration)?
- Host↔controller link: USB serial to a microcontroller (GRBL-style) vs. a
  Raspberry Pi driving steppers directly?
