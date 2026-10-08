---
type: research
status: in-progress
author: marc
date: 2026-10-07
tags: [sports-analytics, cybersecurity, gambling, ios, bot-detection, vendors, osint]
---

# Betting Apps — Detection Vendor and SDK Landscape

**TL;DR**
- Every US sportsbook app is guaranteed to have a **geolocation-compliance** layer (GeoComply or Incognia). Regulators require it.
- Whether these apps also embed a **behavioral-biometrics** SDK (BioCatch/Sardine-class) is **unconfirmed**. It's the biggest unknown in [[Betting Apps — Behavioral and Automation Detection]].
- Below is a public-sources-only method for filling that gap, app by app.

**Useful for:** Sports Analytics (which books will flag automated or sharp play), Robotics (which signals actually matter for the rig), ML (which detector families to benchmark against).

## The four layers and who sells them

| Layer | What it sees | Vendors | Confirmed in sportsbooks? |
|---|---|---|---|
| Geolocation compliance | GPS, Wi-Fi, IP; spoofing, VPN, emulator, root, tampering | **GeoComply**, **Incognia** | **Yes.** FanDuel's 13-year GeoComply partnership was renewed in 2026, covering identity verification and fraud prevention. DraftKings, Caesars and Hard Rock also extended. Incognia entered US iGaming and sports wagering in 2023 and is GLI-tested. `[Documented]` |
| Location behavior | Whether the device's location history matches the account (multi-accounting, proxy betting, bonus abuse) | **Incognia** | Sold for exactly this; operator names aren't public. `[Documented]` (vendor claim) |
| Behavioral biometrics | Typing speed, swipe patterns, touch dynamics, context switching | **BioCatch** (Visa), **Sardine**, BehavioSec, Callsign | **Unconfirmed.** Sardine's public material targets fintech, banking and e-commerce. No sportsbook customer found. `[Community]` |
| RASP / app shielding | Jailbreak, Frida/hooking, debugger, emulator, tampering | Appdome, Promon, freeRASP | Common in betting apps per vendor marketing; per-app confirmation needed. `[Community]` |
| Account linking | Device fingerprint + payment + IP clustering | **SEON**, **Fingerprint** | Marketed for matched betting and "gnoming." `[Documented]` |

**What this means:** location is the *only* layer we know is present everywhere. The location vendors' integrity checks (emulator, root, tampering) catch *software* automation on a modified phone. They say nothing about a physical rig touching a stock phone. Whether anything on the device models *how* the screen is touched depends on the unconfirmed behavioral layer.

## Method: fill the table from public sources only

Stick to sources anyone can read. Don't decompile, bypass certificate pinning, or MITM apps we don't own. That breaks ToS and possibly anti-circumvention law, and it isn't needed.

1. **Privacy policies and processor lists.** GDPR/CCPA disclosures often name "fraud prevention service providers." Search each book's policy for the vendor names above.
2. **Exodus Privacy reports** (Android builds). They list embedded SDK signatures, and clicking a tracker shows every app that uses it. The iOS build usually ships the same vendor SDKs. A DraftKings report hasn't turned up in search yet, so check the site directly. `[Documented]`
3. **App Store privacy labels.** "Data used to track you / linked to you" plus Diagnostics hint at fingerprinting.
4. **Vendor press releases and case studies.** Partnership renewals (like FanDuel/GeoComply) are public.
5. **Job postings.** "Experience with BioCatch/Sardine integration" in a sportsbook trust-and-safety role is a strong signal.

## Pitch in (security people)

- [ ] Pick 1–2 books (DraftKings, FanDuel, BetMGM, Caesars, bet365, theScore) and fill a row per app: vendor, layer, source link, confidence.
- [ ] Check whether Polymarket's app embeds any of these. Its API path is sanctioned, see [[Betting Apps — Behavioral and Automation Detection]] §6.
- [ ] Update this note's status to `answered` once 3+ books are confirmed.

## Sources

- [FanDuel × GeoComply multi-year renewal](https://www.biometricupdate.com/202608/geocomply-signs-mutli-year-renewal-with-fanduel-online-gambling-platform) · [casino.org](https://casino.org/news/canadian-gaming-fanduel-geocomply-partnership) · [LSR — DraftKings × GeoComply](https://www.legalsportsreport.com/6437/draftkings-partners-with-geocomply/) · [GeoComply sports](https://www.geocomply.com/global-sports/) `[Documented]`
- [Incognia iGaming](https://www.incognia.com/igaming) · [Incognia enters iGaming](https://www.incognia.com/newsroom/incognia-enters-the-igaming-space-with-geolocation-compliance-and-account-security-solution) · [SBC Americas](https://sbcamericas.com/2023/04/19/incognia-geolocation-gaming-launch/) `[Documented]`
- [Sardine device and behavior](https://go.sardine.ai/device-intelligence) · [BioCatch vs Sardine](https://www.rfp.wiki/vendors/biocatch/sardine) `[Community]`
- [Exodus Privacy — what it does](https://exodus-privacy.eu.org/en/page/what/) `[Documented]`
