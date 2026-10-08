---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [system-design, robotics, rl-and-simple-robots, fluidnc, grbl, mks-dlc32, jogging, soft-limits]
---

# Gantry — FluidNC Control Interface (Jogging, Soft Limits, Realtime)

**TL;DR**
- Hardware v2 runs **FluidNC on an MKS DLC32**. The agent talks to it through Grbl-1.1-style commands.
- Use **`$J=` jog moves** for taps and targets, the **`0x85` jog cancel** to abort, and **`?` status** polling for closed-loop timing.
- **Soft limits** must be enabled **per axis**, need homing, and only survive a reboot if saved with **`$CD=config.yaml`**.
- Prefer USB serial; the telnet (:23) and WebSocket (:80) interfaces are a security surface.

**Builds on:** [[iOS Control — Exposing Device Controls to the Agent]] (GRBL action space) and [[Gantry — XY Builds and Microcontroller Choice]].

## Command set the agent needs

| Need | Command | Notes |
|---|---|---|
| Move to target (absolute, mm) | `$J=G90 G21 X{x} Y{y} F{feed}` | Feed is **required on every jog** (not modal); jogs don't change parser state [1] |
| Relative nudge (visual servo) | `$J=G91 X{dx} Y{dy} F{feed}` | G91 applies to that jog only [1] |
| Machine coordinates | `$J=G53 ...` | Bypasses work offsets [1] |
| Abort motion | realtime byte **`0x85`** (jog cancel) | Flushes queued jogs → Idle. Cleaner than feed hold, which can "stick" if it lands right as a jog finishes [1][2] |
| Status | realtime **`?`** | Reports `Jog` while moving; jogs accepted only in Idle or Jog [1] |
| Tap (Z / servo) | normal G-code or M-code macro (not jog) | Jogs reject M/S/T words [1]; put the servo tap in a macro |

## Soft limits: the lessons others hit

- Configure `soft_limits: true` and `max_travel_mm` **for each axis** in `config.yaml`. One user had them on X only [3].
- **Homing is required** for soft limits to mean anything [3].
- Web-UI edits change the in-memory config only. **Run `$CD=config.yaml`** to persist, or the change disappears on restart [3].
- `$SS` shows startup messages and config errors [3].
- Size the soft limits to the **screen rectangle + margin**, so the stylus physically can't leave the glass area.

## Connections

- FluidNC exposes **Telnet on :23** and **WebSocket on :80** (≥ v4.0; :81/82 before) [4]. Both are unauthenticated control channels on the LAN. Disable Wi-Fi or firewall it ([[Security — STRIDE Threat Model for the Phone Rig]]).
- The DLC32 Max sample config shows `check_limits: true` and per-axis travel (e.g. X 270 mm) [5].

## Host-side driver sketch

`move(x, y)` → send `$J=` → poll `?` until Idle → `tap()` macro → poll → done. Timeout → `0x85` + `?` → report failure. Keep **one writer** to the serial port (a queue) so the agent, a human and the watchdog never interleave commands.

## Pitch in

- [ ] Robotics: write the host driver (pyserial) with a command queue and timeouts; measure move + tap latency for the RL throughput note.
- [ ] Verify each Grbl command above on FluidNC firmware; note any deviations here.

## Sources

1. [Grbl 1.1 jogging docs (mirror)](https://gitea.psi.ch/motion/ecmc_plugin_grbl/src/branch/master/doc/markdown/jogging.md) `[Documented]` (Grbl; FluidNC follows the Grbl protocol, so verify)
2. [Jog cancel note](https://incoherency.co.uk/notes/20240119.html) `[Community]`
3. [OpenBuilds — FluidNC soft limits thread](https://builds.openbuilds.com/posts/141545/) · [V1E forum](https://forum.v1e.com/t/a-bunch-of-dumb-questions/42148) `[Community]`
4. [LightBurn forum — FluidNC connection ports](https://forum.lightburnsoftware.com/t/no-connections-to-fluidnc/187957/3) `[Community]`
5. [FluidNC issue — DLC32 config dump](https://github.com/bdring/FluidNC/issues/1738) `[Community]`

## Related

- **Summary:** [[State of — System Design]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]]
