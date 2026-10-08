---
type: research
status: answered
author: marc
date: 2026-10-05
tags: [sports-analytics, cybersecurity, gambling, ios]
---

# Geolocation compliance — how do iOS gambling apps prove you're physically in a legal jurisdiction?

## Question

How does regulated online-gambling geolocation compliance work on iOS — why it's required, which
vendors provide it, how GeoComply's device-native stack fuses signals, which Core Location APIs it
leans on, how VPN/proxy/remote-desktop use is detected *conceptually*, and what failure modes
legitimate players hit. **Descriptive/educational only** — this note explains detection mechanisms,
not evasion. (Separate research track from the robot, like `sports-research/`.)

## Why it's regulated

- **US gambling is regulated per-state**, not federally. Each state licenses operators, sets rules,
 and requires that *every wager originate from inside its borders*. "Account registered in a legal
 state" is insufficient — physical presence is checked at wager time. `[Documented]`
- **Wire Act (1961):** bars using interstate wire communication to transmit sports bets; reinforces
 the need to prove a NJ-licensed bet actually came from NJ, not a neighboring state. `[Documented]`
- **UIGEA (2006):** prohibits gambling businesses from *knowingly accepting payments* for bets
 "unlawful under any federal or state law" — pushes liability onto operators/processors, so they
 must positively establish lawful location before accepting funds. `[Documented]`
- **Example state rules:** NJ (13:69Q-1.3) — operator must *affirmatively locate* the patron in-state
 at wager time and file a *schedule of intervals* for re-checks during a session; CT (§12-865-9) —
 "dynamically and consistently monitor" location *throughout the session*; MI — a geofencing system
 must "reasonably detect the physical location" before a wager. Ontario (AGCO) mandates real-time
 verification for all iGaming. `[Documented]`
- **UKGC contrast:** Great Britain has a *single national* licence (Gambling Act 2005 ss.33/36 — serving
 remote gambling to GB without a UKGC licence is a criminal offence for the operator), so geolocation
 is used to confirm *in-country* presence + enforce **GAMSTOP** national self-exclusion and age checks,
 **not** intra-national geofencing. Offshore (Curaçao/Malta/Anjouan) sites sit outside GAMSTOP by design. `[Documented]`
- **Polymarket as context:** after a 2022 CFTC settlement ($1.4M) it *geo-blocked US users* for ~3 yrs
 (international arm, crypto, VPN-evadable); it relaunched a **separate KYC'd US arm** (CFTC-licensed
 exchange acquisition) in late 2025 and began actively blocking VPN/residential-proxy access. Shows the
 US-vs-international split and why IP-only blocking is weak. `[Community]`

## Vendors (the compliance layer operators buy, not build)

| Vendor | Model / note | `[tag]` |
|---|---|---|
| **GeoComply** | Category incumbent (founded 2011); US regulators standardized around it. Products: **Core** (location+device+identity checks), **GeoGuard** (VPN/proxy IP DB, ~270M IPs, hourly-updated, claims ~98–99% spoof detect), **PinPoint** (on-property beacon geofencing), **IDComply** (KYC). Legacy per-ping pricing. Lost core anti-spoof patent Nov-2024. `[Documented]` |
| **Xpoint (Verify / "Lightning")** | Challenger (2019) that *won* the Federal Circuit patent case invalidating GeoComply's anti-spoof patent; ~28 US jurisdictions + Ontario; bet365/PrizePicks wins. `[Community]` |
| **Radar** | SDK-first (2016), embedded in the operator's own iOS/Android/React-Native app; **per-user** (MAU) pricing vs per-check, so operators can verify on *every* wager/deposit/withdrawal cheaply. `[Community]` |

All three advertise **300–350+ checks per transaction**, cross-referencing IP + GPS + Wi-Fi + cell +
device integrity simultaneously — the thesis being "fake one signal and the others disagree." `[Benchmark]`

## How GeoComply's iOS SDK works (high level)

- **Device-native SDK** embedded in the operator's app; on iOS it reads location *natively* from device
 sensors (vs desktop, which needs a browser plugin / standalone app because PCs lack GPS). `[Documented]`
- **Multi-source fusion:** combines **GPS** (satellite lat/long, few-meter precision — primary on mobile),
 **Wi-Fi positioning** (scans nearby SSIDs/BSSIDs, cross-refs a location DB; works indoors, even if not
 joined), **cell-tower** triangulation (coarse backup), and **IP** (secondary consistency check only —
 IP alone "can't be trusted"). Then **authenticates** the data points (tamper/mask/spoof detection) to
 derive a *true* location, not just a reported one. `[Documented]`
- **Cadence = "geo-check" gates:** a check runs at **login/session start**, **before each wager** ("place
 a bet" is gated on a fresh pass), and at **regulator-approved periodic intervals** during an active
 session (NJ "schedule of intervals"; CT continuous). The SDK returns a pass/fail + reason to the operator
 backend; a fail suspends betting until re-verified. `[Documented]`
- **Boundary buffers:** operators pull the accepted zone *inward* from the state line by a buffer sized to
 the location's uncertainty — if the horizontal-accuracy radius straddles a border, the wager is rejected
 rather than risk an out-of-state bet (ties directly to iOS `CLLocation.horizontalAccuracy`). `[Community]`

## iOS frameworks involved (Core Location)

- **`CLLocationManager`** — the entry point. App requests `requestWhenInUseAuthorization()` (betting
 happens foreground); `Info.plist` needs `NSLocationWhenInUseUsageDescription`. `[Documented]`
- **Precise vs approximate (iOS 14+):** `accuracyAuthorization` is `.fullAccuracy` or `.reducedAccuracy`.
 Under `.reducedAccuracy`, setting `desiredAccuracy` beyond `kCLLocationAccuracyReduced` **does nothing**
 and **region monitoring/beacon ranging are unavailable** — fatal for compliance. Apps call
 `requestTemporaryFullAccuracyAuthorization(withPurposeKey:)` to prompt the user to turn **Precise
 Location** on; without it the geo-check cannot pass. `[Documented]`
- **Anti-spoof signal — `CLLocation.sourceInformation` (iOS 15+):**
 - `isSimulatedBySoftware` → `true` when the system *generated* the fix via on-device software simulation
  (Xcode GPX / Developer-Mode simulated location). A compliance app can reject fixes where this is `true`
  outside debugging. `[Documented]`
 - `isProducedByAccessory` → `true` when the fix came from an **external accessory** (MFi GPS dongle,
  CarPlay) rather than the device's own hardware — relevant because external NMEA feeds are a classic
  spoof surface. `[Documented]`
 - **Honest caveat:** these are *hints*, not guarantees — developers report `isSimulatedBySoftware`
  missing some third-party spoofing tools; this is exactly *why* vendors layer dozens of signals rather
  than trust one flag. `[Community]`
- **`startMonitoringSignificantLocationChanges` / region monitoring (`CLCircularRegion` geofence):** used
 to notice jurisdiction crossings between discrete geo-checks (e.g., session drifts over a state line)
 and to re-trigger verification. `[Documented]`
- **Device integrity (jailbreak, hooking, mock providers)** is adjacent and lives in [[Betting Apps — Device Integrity and Attestation]]
 (DeviceCheck / App Attest); identity-level signals in [[Betting Apps — Device Integrity and Attestation]].

## VPN / proxy / remote-desktop detection (conceptual)

- **VPN/proxy:** compared against curated IP databases (GeoGuard) + **IP-vs-device-location mismatch**
 (device GPS says state A, IP egress says state B → flag), plus latency/connection-pattern and
 residential-proxy-abuse heuristics. On iOS the *app* mostly reads device location; VPN/IP correlation is
 largely **server-side** (the SDK can observe connection type via Network framework but the verdict is
 computed on the backend). `[Documented]`
- **Remote desktop (RDP/VNC):** a user drives a PC physically in-state from out-of-state. Countered by
 detecting **active remote-desktop processes/sessions**, **input-latency** anomalies, and device
 fingerprinting/session-behavior analysis (overlaps [[Betting Apps — Behavioral and Automation Detection]]). `[Documented]`
- **Other flagged vectors (detection targets, non-exhaustive):** rooted/jailbroken devices, emulators/VMs,
 reverse-tethering, DNS-proxy spoofing, device farms (shared IP/SSID clusters). GeoComply reports a new
 spoofing variant ~every 18h across 25.6B checks/yr — hence the arms-race framing. `[Community]`

## Failure modes legitimate players hit

- **Location Services off / Precise Location off** → `.reducedAccuracy` → geo-check can't pass (most common). `[Documented]`
- **Wi-Fi disabled** → loses Wi-Fi positioning, degrades indoor accuracy, triggers "can't verify." `[Documented]`
- **VPN/corporate proxy on** → IP/device mismatch flags even for an in-state player. `[Documented]`
- **Near a state line** → accuracy radius overlaps the border → buffer rejects the wager. `[Community]`
- **RDP/VNC running in parallel** (even for legit screen-share) → "cannot verify with an RDP running." `[Community]`
- **Developer Mode / simulated location** left on → `isSimulatedBySoftware` trips a reject. `[Documented]`
- **Permission prompt fatigue / battery** → operators tout low-latency, low-drain SDKs to minimize this. `[Community]`

## Sources

- [GeoComply Core](https://www.geocomply.com/anti-fraud-and-geolocation-solutions/geocomply-core/) · [GeoGuard VPN/proxy](https://www.geocomply.com/anti-fraud-and-geolocation-solutions/geoguard/) · [Compliance-readiness playbook (spoofing-vector list, IP-not-trusted)](https://www.geocomply.com/blog/compliance-readiness-playbook-why-your-geolocation-signal-is-the-foundation-under-every-compliance-control/) — vendor's own mechanism + detection-target descriptions `[Documented]`
- [GeoComply IETF IP-geolocation workshop slides](https://www.ietf.org/slides/slides-ipgeows-paper-geocomplycom-00.pdf) — Wi-Fi+GPS+cell+IP fusion statement `[Documented]`
- [Partnerkin: GeoComply vs Xpoint vs Radar (2026)](https://partnerkin.com/en/b2b/gaming-geolocation-compliance/) — vendor models, patent case, pricing, footprints `[Community]`
- [OddsIndex: how sports-betting geolocation works + troubleshooting](https://oddsindex.com/guides/sports-betting-geolocation) — signal types, login+periodic cadence, failure modes `[Documented]`
- [Nerdbot: geolocation spoofing / casinos (Mar 2026)](https://nerdbot.com/2026/03/30/how-geolocation-spoofing-is-becoming-the-biggest-headache-for-online-casinos/) — 350+ checks, RDP/VPN counters, Ontario real-time `[Community]`
- Regulations: [NJ 13:69Q-1.3 (affirmative in-state + interval schedule)](https://www.law.cornell.edu/regulations/new-jersey/N-J-A-C-13-69Q-1-3) · [CT §12-865-9 geofencing (continuous)](https://www.law.cornell.edu/regulations/connecticut/Regs-Conn-State-Agencies-SS-12-865-9) · [MI geofencing spec](https://www.michigan.gov/documents/mgcb/Geofencing_Specifications_TB_-_08-06-20_699090_7.pdf) · [UIGEA (FDIC FIL-35-2010)](https://www.fdic.gov/news/financial-institution-letters/2010/fil10035a.pdf) `[Documented]`
- Apple Core Location: [`sourceInformation`](https://developer.apple.com/documentation/corelocation/cllocation/sourceinformation) · [`isSimulatedBySoftware`](https://developer.apple.com/documentation/corelocation/cllocationsourceinformation/issimulatedbysoftware) · [`isProducedByAccessory`](https://developer.apple.com/documentation/corelocation/cllocationsourceinformation/isproducedbyaccessory) · [`accuracyAuthorization`](https://developer.apple.com/documentation/corelocation/cllocationmanager/accuracyauthorization) — exact API semantics `[Documented]`
- [Apple Developer Forums: isSimulatedBySoftware reliability gap](https://developer.apple.com/forums/thread/803179) — flag misses some spoof tools `[Community]`
- [Polymarket geographic restrictions](https://help.polymarket.com/en/articles/13364163-geographic-restrictions) · [US relaunch 2025](https://winnersandwhiners.com/reviews/polymarket/legal-guide) · [VPN crackdown](https://gizmodo.com/polymarket-cracks-down-on-vpn-users-as-legal-pressure-intensifies-in-dozens-of-countries-2000765379) — US/international split context `[Community]`
- [UK Gambling Commission](https://www.gamblingcommission.gov.uk/) — national licensing model (contrast to US state geofencing) `[Documented]`

## Open questions / follow-ups

- Exact iOS SDK **re-check interval** operators file with regulators (NJ "schedule of intervals") — minutes? per-wager only? → likely per-operator, not public.
- Does the SDK read **`CLLocation.horizontalAccuracy`** directly to size the border buffer, or compute buffer server-side? Confirm against a vendor integration guide.
- How is `.reducedAccuracy` handled UX-wise — hard block vs. degraded prompt loop? Ties to failure-mode friction.
- Where does Core Location **anti-spoof** end and **device attestation** begin → split cleanly with [[Betting Apps — Device Integrity and Attestation]].
- Network framework (`NWPathMonitor`) VPN visibility on iOS vs server-side IP correlation — how much is on-device? → flag in `questions.md` if tracked.

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — Cybersecurity]]
