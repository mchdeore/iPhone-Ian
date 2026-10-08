---
type: summary
status: living
author: marc
date: 2026-10-07
updated: 2026-10-07
tags: [cybersecurity, state-of]
---

# State of — Cybersecurity

> Living summary of everything tagged #cybersecurity. **Update this when you add or change a security note**, then bump `updated`.

## Current best answers

- **Biggest risk to us is our own rig:** remote control of the host is remote control of a real phone. The first-pass STRIDE model ranks host access, screen-capture leaks and on-screen prompt injection as the top three → [[Security — STRIDE Threat Model for the Phone Rig]].
- **GUI agents obey the screen:** adversarial pop-ups got ~86% click-through and cut task success by 47%, and "ignore pop-ups" prompts failed. Defences have to be architectural: allowlists, action gating, an independent verifier → [[Security — Prompt Injection and Pop-up Attacks on GUI Agents]].
- **Secrets:** SOPS + age for anything in the repo, plus gitleaks pre-commit, GitHub push protection and CI. Signing keys stay in a hardware wallet or vault → [[Security — Secrets and Key Management for Bots and Rigs]].
- **iOS auth:** the robot always uses the passcode fallback and never Face ID; TOTP over SMS; disable the triple-click Accessibility Shortcut → [[iOS — Face ID, Autofill and 2FA Constraints]].
- **How betting apps detect automation (mapping only, no evasion):** geolocation (GeoComply/Incognia, confirmed everywhere), device integrity/RASP, behavioural biometrics (unconfirmed in sportsbooks), and account-level profiling → [[Betting Apps — Behavioral and Automation Detection]], [[Betting Apps — Detection Vendor and SDK Landscape]], [[Betting Apps — Geolocation Compliance]], [[Betting Apps — Device Integrity and Attestation]].
- **Why the detection stack exists:** licensing, geofencing, KYC/AML and responsible-gambling rules *mandate* it → [[Betting Apps — Regulatory and Responsible Gambling]].
- **Accessibility flags are an ADA trap.** `isAssistiveTouchRunning` is true for millions of disabled users, so it's a weak and legally risky signal.

## Decisions made

- Test phones: no real credentials, payments or messaging apps; notifications off; a dedicated test Apple ID → [[RL — Real-World Training Loop on the Gantry (Resets, Safety, HIL-SERL)]].
- Never train against a VLM judge on apps that can move money or send messages → [[RL — Rewards and Success Detection from the Screen]].
- No VPN use around geo-blocks → [[Markets — Legal Status of Prediction Markets (US and Canada, Oct 2026)]].

## Where sources disagree or we're unsure

- Whether major sportsbooks embed BioCatch-class behavioural SDKs: no public confirmation yet.
- Oracle risk on Polymarket (UMA disputes, whale influence) is documented mostly in secondary sources → [[Markets — Resolution and Oracle Risk on Polymarket (UMA)]].

## Open questions

- USB-only controller link with all remote access through the host (Aria's §7 Q6)? Leaning yes.
- Does AirPlay capture on shared Wi-Fi expose the stream? Use an isolated network or USB.

## Next actions

- [ ] Draw the data-flow diagram in the STRIDE note.
- [ ] Add gitleaks + CI; turn on push protection; fix `.gitignore` so *encrypted* `*.sops.yaml` files can be committed.
- [ ] Port PopupAttack overlays into emulator tasks as a security regression test.
- [ ] Fill the vendor table for 3+ sportsbooks from privacy policies.

## Changelog

- 2026-10-07: first version.

## Other summaries

[[State of — Sports Analytics]] · [[State of — Machine Learning]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]] · [[State of — ML and Sports Markets]] · [[State of — Math]] · [[State of — YOLO]]
