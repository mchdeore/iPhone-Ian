# iPhone Accessibility Robot (`iPhone-Ian`)

A physical robot that operates a **stock, unmodified iPhone** by tapping its
touchscreen, driven by a vision-based AI agent. You give it high-level commands
like `login`, `enter`, or `exit`, and it locates the right on-screen targets,
moves a capacitive stylus to them, and taps — pulling secrets (e.g. login
credentials) from a host-side vault so you never hand-type them again.

> Working title. The repo name (`iPhone-Ian` → "iPhonian") is a placeholder we
> can rebrand later.

## Why a physical robot (and not software)

The phone is treated as an **opaque black box**: no jailbreak, no MDM, no
developer provisioning, nothing installed on it. On a stock iPhone there is no
ADB-style control surface, so a physical actuator that just *touches the glass*
is the most general way to automate an arbitrary device. See
[`specs/00-charter.md`](specs/00-charter.md) for the full rationale.

## The three things set in concrete

1. **Target device: iPhone, 100%.** iOS-only. (The Android survey in
   `research/` is legacy background — see note below.)
2. **Actuation: a tap robot, borrowing heavily from Tapster + the Instructables
   "Screen Tapping Robot."** Reuse existing open designs (Tapster's Push Button
   Robot / Sidekick lineage, the 3D-printable Cartesian gantry) rather than
   reinventing. See [`specs/01-hardware.md`](specs/01-hardware.md).
3. **Training: an ML rig / data-collection app** so the agent learns to drive
   the phone reliably. See [`specs/02-firmware-and-software.md`](specs/02-firmware-and-software.md).

## Repository layout

Split by owner so each of us can find the other's work. Shared material stays at the top.

| Who | Owns | Start here |
|---|---|---|
| **Aria** | Hardware: CAD, parts + sourcing, assembly | [`aria/README.md`](aria/README.md) |
| **Marc** | Software: OCR/vision, training loop, agent, host control, credentials | [`marc/README.md`](marc/README.md) |

```
iPhone-Ian/
├── README.md                      # this file
├── DEVELOPMENT.md                 # staged build pipeline (shared)
├── specs/                         # original specifications (shared)
│   ├── 00-charter.md              # scope, decisions, security, roadmap
│   ├── 01-hardware.md             # hardware research + citations (v2 design: aria/)
│   └── 02-firmware-and-software.md# firmware + software + ML
├── research/                      # background research notes (shared)
├── aria/                          # HARDWARE (Aria)
│   ├── hardware-concept-v2.md     # requirements, design, parts list w/ links, open questions
│   ├── LOG.md                     # dated decisions + to-dos
│   └── cad/v2_0_layout.py         # CoreXY layout model (build123d)
└── marc/                          # SOFTWARE (Marc)
    ├── DEVLOG.md                  # Marc's dev log
    └── parts-v1/                  # v1 gantry CAD (retired by v2)
```

> The research is split into two parts, matching the two specs: **hardware /
> physical build** (`01-hardware.md`) and **firmware / software / ML**
> (`02-firmware-and-software.md`). All reusable-parts research and citations now
> live inside those two docs.

## Relationship to HomeLab

[HomeLab](https://github.com/mchdeore/HomeLab) is the separate, overarching
project: the permanent home PC / Linux server and its CI/CD. This accessibility
robot is intended to be *built on top of* that server (the host that runs the
agent and holds the credential vault lives there), but its research and design
live here, on their own.

## Status

Design stage (2026-10-02). Hardware v2 is proposed: a 2-phone CoreXY gantry, ~34 × 32 × 5 cm, ~C$325 + tax, with
1 phone first for testing. See `aria/hardware-concept-v2.md`. Software planning is under way in `marc/`.
Nothing is built yet.
