---
type: research
status: in-progress
author: marc
date: 2026-10-07
tags: [cybersecurity, robotics, threat-model, stride, iot]
---

# Security — STRIDE Threat Model for the Phone Rig

**TL;DR**
- STRIDE (Microsoft) walks through each component and data flow, asking six questions: **S**poofing, **T**ampering, **R**epudiation, **I**nformation disclosure, **D**enial of service, **E**levation of privilege.
- Applied to the rig, the top risks are: (1) **remote control of the host** = remote control of a real phone, (2) **screen captures leaking secrets**, (3) **on-screen prompt injection** steering the agent.
- This note is the first-pass model; refine it once hardware v2's data flows are final.

**Builds on:** [[Infra — Exposing a Windows Host and Low-Latency Streaming]], [[Security — Prompt Injection and Pop-up Attacks on GUI Agents]], [[Security — Secrets and Key Management for Bots and Rigs]].

## Method

STRIDE (Garg & Kohnfelder, Microsoft) is applied to a data-flow diagram of processes, data stores, flows and trust boundaries [1][2]. It has been extended for IoT and used on smart-home and industrial systems [3][4].

## Data flows (v2 baseline)

`Operator → (Tailscale/tunnel) → Host PC → USB → MKS DLC32/FluidNC → gantry → phone glass`
`Phone → (USB capture / AirPlay) → Host → VLM agent → action → FluidNC`
`Host ↔ dataset store ↔ git/GitHub`

Trust boundaries: internet ↔ host; host ↔ controller (USB); host ↔ phone (capture link); agent ↔ on-screen content.

## STRIDE table

| Threat | Where | Example | Mitigation |
|---|---|---|---|
| **Spoofing** | Remote access to host | A stolen tunnel token lets an attacker drive the robot | Per-person identity (Tailscale ACLs), no shared tokens, MFA. IoT lesson: one shared token compromises the whole fleet [5] |
| **Spoofing** | FluidNC Wi-Fi/web UI | Anyone on the LAN can send G-code over telnet :23 or WebSocket [6] | **Disable FluidNC Wi-Fi**; USB-only control (Aria's §7 Q6) |
| **Tampering** | Agent input | Pop-up or notification injects instructions | Allowlist + action gating + verifier |
| **Tampering** | Firmware/config | A modified `config.yaml` removes soft limits | Config in git; checksum on boot; e-stop |
| **Repudiation** | Who ran what | An unknown person triggers actions on a shared host | Append-only action log (who, task, every command), time-synced |
| **Info disclosure** | Captures and datasets | Screenshots contain codes, emails, balances | Test accounts only; redaction pass; `captures/` and `datasets/` git-ignored |
| **Info disclosure** | Stream | Low-latency stream exposed publicly | Stream only inside the tailnet; never a public port without auth |
| **DoS** | Controller | Flooding G-code or a jog storm; motor stall | Rate-limit commands host-side; jog cancel 0x85 [7]; watchdog |
| **Elevation** | Agent → phone | The agent wanders into Settings and changes accessibility or account options | Blocked screens; reset to a known state; no admin apps on the test phone |

## Pitch in

- [ ] Security: draw the DFD (Mermaid in this note) and add any boundary missing above.
- [ ] Robotics: confirm whether FluidNC Wi-Fi can be fully disabled on the DLC32 build.

## Sources

1. [STRIDE (security) overview](https://oreil.ly/rNmPN) `[Documented]`
2. [Practical Industrial IoT Security — STRIDE](https://iread.qq.com/read/1036699616/72) `[Documented]`
3. [Smart-home botnet threat modelling with STRIDE (arXiv 2101.02147)](https://arxiv.org/pdf/2101.02147) `[Benchmark]`
4. [IoT smart home STRIDE analysis (iJIM)](https://online-journals.org/index.php/i-jim/article/view/52377) `[Benchmark]`
5. [Trustworthy Smart Band threat modelling (arXiv 1812.02361)](https://arxiv.org/pdf/1812.02361) `[Benchmark]`
6. [LightBurn forum — FluidNC ports (Telnet 23, WebSocket 80/81/82)](https://forum.lightburnsoftware.com/t/no-connections-to-fluidnc/187957/3) `[Community]`
7. [Grbl 1.1 jogging docs (mirror)](https://gitea.psi.ch/motion/ecmc_plugin_grbl/src/branch/master/doc/markdown/jogging.md) `[Documented]`

## Related

- **Summary:** [[State of — Cybersecurity]] · [[State of — Robotics]]
