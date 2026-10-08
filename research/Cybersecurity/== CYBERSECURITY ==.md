---
type: hub
---

# == CYBERSECURITY ==

Threat models, device integrity and attestation, bot/automation detection, auth (Face ID, passkeys, 2FA), and network exposure.

## Notes

- [[Betting Apps — Behavioral and Automation Detection]] · also Sports Analytics, Robotics, Machine Learning
- [[Betting Apps — Device Integrity and Attestation]] · also Sports Analytics
- [[Betting Apps — Geolocation Compliance]] · also Sports Analytics
- [[Betting Apps — Regulatory and Responsible Gambling]] · also Sports Analytics
- [[Infra — Exposing a Windows Host and Low-Latency Streaming]] · also Robotics
- [[iOS — Face ID, Autofill and 2FA Constraints]] · also Robotics

## From other domains

- [[iOS Control — Alternative Accessibility Input Paths]] · from Robotics
- [[iOS Control — Raspberry Pi HID Input Converter]] · from Robotics

## Exchange

- **Gives others:** threat models and "what will get us flagged" checks for every project; safe ways to expose hosts and handle secrets.
- **Wants from others:** how the robot actually touches and drives devices (→ Robotics); behavioral models that detection systems use (→ Machine Learning).

## Key decisions

- Robot always uses the passcode fallback, never triggers Face ID; password fallback is universal on iOS in 2026, "Sign in with Apple" is a dead end
- 2FA: prefer TOTP over SMS
- Disable the triple-click Accessibility Shortcut (VoiceOver risk)
- Secrets stay in a host-side vault, never in the repo

## Open

- USB-only link to the motion controller, with all remote access going through the host? (Aria's §7 Q6)

## Help wanted (all domains)

```query
[type:request] -[status:answered]
```

## Adding to the pool

- New note → put it in the folder of its **main** domain, add a link to it on this hub, and fill in `domain`, `type`, `status`, `author`, `date`. Copy the frontmatter from any existing note.
- `domain: [ml, sports]`: list **every** domain it could help. Also link it under *"From other domains"* on those hubs. That's how research crosses over.
- Need something researched? Make a note with `type: request`, `status: seed`. It shows up on Help Wanted on every hub. Pick one up by adding `claimed_by: <you>`.
- Start every note with a 3-line **TL;DR**. Domain values: `sports` · `ml` · `security` · `robotics`.
