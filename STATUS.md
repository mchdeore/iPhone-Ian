# STATUS — conversation handoff

Snapshot for picking this project up with another agent. Last updated
**2026-09-07**. Repo: https://github.com/mchdeore/iPhone-Ian (public, `main`).

---

## TL;DR

Building a **physical robot that taps a stock iPhone's touchscreen**, driven by a
vision-based AI agent that responds to commands like `login` / `enter` / `exit` and
pulls credentials from a host-side vault. The phone is treated as a **black box**
(no jailbreak, no install). Currently in **research + spec** stage — **nothing
built, no code written yet.** All work so far is documentation.

Read these in order: `README.md` → `specs/00-charter.md` →
`specs/01-hardware.md` + `specs/02-firmware-and-software.md` → `DEVELOPMENT.md`.

## Decisions set in concrete (see `specs/00-charter.md`)

- **D1 — iPhone / iOS only.** (The Android research in `research/` is legacy
  background.)
- **D2 — Physical actuation**, phone is a black box (no software on the phone).
- **D3 — Design source of truth:** Instructables "Screen Tapping Robot" (3D-printed
  Cartesian XY gantry), **borrowing heavily from Tapster** (Push Button Robot /
  Sidekick lineage — see `01-hardware.md` §3.4).
- **D4 — An ML training rig / data-collection app is a first-class deliverable.**
- **D5 — Command-driven + credential-aware** (`login` is the flagship command).

## Chosen hardware direction (cheap + quiet + not-janky, ~$50 over rock-bottom)

Per the user's priority (cheap, but pay ~$50 for **quiet / reliable / easy**, does
**not** need power/features/accuracy). See `specs/01-hardware.md` §9.1–§9.1.1.

- **NEMA 17 steppers + TMC2209 "silent" drivers** (StealthChop2; drop-in on the CNC
  shield; GRBL standalone). **Avoid the 28BYJ-48** — it's the janky option.
- **Arduino Uno + CNC Shield V3 + GRBL**, driven from the **laptop over USB**
  (G-code). Raspberry Pi, if used, is the *host*, not the motor controller.
- **SG90 servo for the tap (Z)** — own 5V supply + detach when idle to kill buzz.
- **Just a USB webcam** for vision (rigid mount + locked focus + glare control
  matter; camera specs don't).
- Spend the ~$50 on: TMC2209 ×2 → MGN9 linear rails → regulated 12V PSU.
- Precision is intentionally cheap because **the camera closes the loop** and
  corrects positioning (see `02-firmware-and-software.md` §5.1).

## Development pipeline (see `DEVELOPMENT.md`)

- **Stage 0** — fail-fast: prove a *grounded* stylus registers touches on the iPhone.
- **Stage 1** — two axes + tap: move a stylus anywhere on the screen and tap.
- **Stage 2** — deterministic input: dumb firmware, `move(x,y)`/`tap()` over serial.
- **Stage 3** — vision + calibration (the hard part): webcam + OpenCV homography;
  build the **target-practice trainer app** (a no-install web page that flashes
  targets and scores hits — doubles as calibration data + accuracy benchmark).
- **Stage 4** — autonomy: UGround/OmniParser grounding model picks what to tap.
- **Stage 5** — real tasks + credentials + security hardening.

## ⏳ Open threads / where we left off

1. **Shopping list not yet built.** The immediate next task the user was deciding
   on: turn `§9.1.1` into a real parts list (specific products + links + running
   total). **Blocked on one choice: belt-driven vs lead-screw** for the two axes.
   (Agent's default suggestion: lead-screw — quieter/simpler for a small slow rig.)
2. **Instructables SoT details not fully extracted** (site blocks scraping) —
   Y-axis mechanism, Z/stylus, controller, BOM, STLs still to pull by hand
   (`01-hardware.md` §1 checklist).
3. **User-provided CAD links recorded but not individually verified**
   (`01-hardware.md` §5.1) — GrabCAD/Printables may gate downloads; verify
   geometry/scale/license before printing.
4. **Push Button Robot specifics unverified** — described from user report; confirm
   footprint/part count on tapster.io + the `tapsterbot` GitHub org.

## Guardrails for whoever continues

- **No secrets in the repo, ever.** Credentials live in a host-side vault (Keychain
  / 1Password CLI / `sops`+`age`); `.gitignore` already excludes env/keys/vault/
  datasets. Scrub any training capture that shows a secret.
- **iOS reality:** Face ID / passkey-only logins can't be driven by a robot; scope
  `login` to credential-typeable flows.
- **Keep firmware dumb, host smart** — all intelligence on the laptop/host.
- **HomeLab is a separate repo** (home server / CI-CD). This repo is only the phone
  robot.

## Repo map

```
README.md                         # project overview
STATUS.md                         # this handoff
DEVELOPMENT.md                    # staged build pipeline
specs/00-charter.md               # scope, decisions, security, roadmap
specs/01-hardware.md              # HARDWARE: build, CAD library, parts, citations
specs/02-firmware-and-software.md # FIRMWARE + SOFTWARE + ML: control, CV, agent
research/                         # background notes (README indexes them)
```

## Latest commit at handoff

`609b7b3` — "Tune parts guidance for cheap + quiet + not-janky priority".
