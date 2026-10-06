---
tags: [ios-gambling-detection, behavioral-biometrics, bot-detection, accessibility, ADA, screen-capture, betting-analytics, courtsiding, polymarket, matched-betting]
status: answered
date: 2026-10-05
related:
  - "[[README]]"
  - "[[01-landscape-and-regulation]]"
  - "[[02-geolocation-and-location-integrity]]"
  - "[[03-device-integrity-and-anti-fraud-sdks]]"
  - "[[05-identity-kyc-and-multi-accounting]]"
  - "[[../_side-projects/tennis-modeling/tennis-research]]"
---

# 04 — Behavioral & automation detection — how betting apps profile *how* you tap, and what a tapping robot looks like

## Question

If an automated agent (our gantry or HID rig) drove a stock iPhone running a gambling/betting
app, what behavioral-biometric and anti-automation signals would the app + its fraud vendors
observe — and how do sportsbooks vs. prediction markets (Polymarket) treat bot/API traders?
*Descriptive/educational only — this note maps signals, it does not give evasion advice.*

## Key findings

### 1. Behavioral biometrics — the *how*, not the *what*

- Vendors continuously profile *interaction dynamics*, not credentials. **BioCatch** (Visa agreed
  to acquire it for ~$2.4B, 2026) analyzes "keystrokes, touch gestures, and device handling" across
  thousands of signals to separate humans from fraudsters/bots in real time. `[Documented]`
- **Touch-dynamics features available on iOS (UIKit):** `UITouch.force` (normalized, `1.0` =
  system-average press — *not* user-specific), `UITouch.majorRadius` (contact-patch size in points/
  mm, with a `majorRadiusTolerance`), tap **dwell**, inter-tap **timing**, swipe **velocity +
  curvature**, and full `began→moved→ended` trajectory. (SwiftUI gestures expose only x/y; force +
  radius need UIKit.) `[Documented]`
- **Device-motion coupling:** `CoreMotion` accel/gyro sampled *during* taps. The academic **HMOG**
  (Hand-movement, Orientation, Grasp) line shows the subtle micro-movements from how a user grips
  and taps a phone are individually identifying; broad continuous-auth surveys catalog 140+ methods
  (touch-gesture 29, motion 28, keystroke 20). `[Benchmark]`
- Peers to BioCatch: BehavioSec (LexisNexis), Callsign, Nethone/Mastercard, Darwinium, plus device/
  signal vendors SEON and Fingerprint that bundle behavior with device intelligence. `[Documented]`

### 2. Bot / automation signals

- **Timing regularity is the headline tell.** Scripts emit machine-regular inter-event intervals;
  BioCatch markets detection of "input speed… and timing irregularities that persist **even when
  bots attempt to mimic human traits**." `[Documented]`
- **Missing entropy:** identical landing coordinates, constant-velocity swipes, flat force/radius
  distributions, no hesitation/overshoot/correction.
- **Accessibility status is directly queryable** by any app: `UIAccessibility.isAssistiveTouchRunning`,
  `isSwitchControlRunning`, `isVoiceOverRunning` (+ matching `*StatusDidChangeNotification`). Some
  naïve anti-bot logic keys off these — see §3 for why that is a trap. `[Documented]`
- **Synthetic-touch injection has a signature:** XCTest/WebDriverAgent/Frida-injected touches show
  *sustained zero force* and *zero / "unnaturally stable" radius*; real fingers vary, so a radius-
  tolerance check separates them. (Hobby `ios-touch-gesture-automation-detector` demonstrates the
  WDA verdict exactly.) `[Community]`
- **RASP / app-shielding SDKs** (freeRASP, Appdome, Promon) that betting apps commonly embed detect
  jailbreak, Frida/method-hooking, emulators, debuggers, tampering, parallel instances. These catch
  *software* automation on compromised devices — they say little about a stock, un-jailbroken phone. `[Documented]`

### 3. The ADA / accessibility fairness trap (why §2's accessibility flags are dangerous)

- `isVoiceOverRunning` / `isAssistiveTouchRunning` / `isSwitchControlRunning` are **TRUE for millions
  of legitimate disabled users**. Treating "accessibility active" as a bot/fraud signal penalizes
  assistive-technology users and is both discriminatory and legally exposed.
- Research is explicit: traditional fraud defenses — "CAPTCHA tasks and automated response-time
  analysis — often exclude legitimate participants, particularly those who rely on assistive
  technologies." `[Benchmark]`
- US DOJ/ADA AI guidance and ADA-audit frameworks warn that a system which "misreads assistive
  technology" or blocks it produces unlawful disability discrimination (and immediate legal/
  operational risk). `[Documented]`
- **Takeaway:** accessibility-active is a weak, legally fraught signal; mature vendors use it as
  *context* feeding a behavioral model, never as a standalone block.

### 4. Screen mirroring / recording / remote access

- `UIScreen.isCaptured` (iOS 11+) is `true` when the screen is being recorded, AirPlayed, or mirrored
  to an external display; observe `UIScreen.capturedDidChangeNotification`. FairPlay-protected video
  auto-blacks-out under capture. Betting/banking apps poll this to blur sensitive views. `[Documented]`
- Capture risk vectors enumerated by app-shielding vendors (Approov): screen recording, AirPlay/
  external-display mirroring, background app-switcher snapshots, diagnostic/instrumentation tools. `[Documented]`
- **Remote access:** iOS's sandbox has **no** Android-style accessibility remote-control surface and
  no public API to learn "another process is driving me," so remote operation is inferred only
  indirectly (`isCaptured` + behavioral anomaly), unlike Android (see `[[../ios-control/01-faceid-autofill-accessibility]]`). `[Community]`

### 5. Betting-pattern analytics (account-level, device-independent)

- **Sharp / arbitrage limiting:** books profile *betting behavior* — beating the closing line over
  200+ bets, bet **timing vs. line movement**, odd/precise stake sizes, only taking +EV / stale
  prices — then apply ~7 restriction tiers from stake throttling ("**gubbing**") to closure. Most US
  books name arbitrage in their ToS and limit arbers. `[Community]`
- **Latency / courtsiding:** official in-play feeds run ~5–30 s behind live (broadcast adds +20–45 s);
  an in-venue scout relays an outcome in <1 s, so bets land *after* the event but *before* the price
  moves. Mitigations: tournament bans/arrests, bet-acceptance delays, stake caps, AI-vision feeds. `[Community]`
- **Matched betting / bonus abuse / multi-accounting ("gnoming"):** place offsetting bets to extract
  free-bet promos near risk-free; detected by cross-referencing device fingerprint + payment method +
  IP + even typing patterns to collapse duplicate accounts (SEON, Fingerprint). `[Documented]`

### 6. Sportsbooks vs. prediction markets — opposite stance on bots

- **Sportsbook = your counterparty.** It profits from recreational losses and loses to sharps, so it
  **limits/bans profitable or automated accounts regardless of input method**. `[Community]`
- **Polymarket = non-custodial peer-to-peer CLOB.** You trade other users; the house takes no
  directional risk and earns on flow, so **bots and market-makers are first-class**: an official CLOB
  API with EIP-712-signed orders, public (keyless) data endpoints, and a documented market-maker
  path. It only **geo-blocks** by jurisdiction. `[Documented]`
- **Implication for our tennis track (`[[../_side-projects/tennis-modeling/tennis-research]]`):** Polymarket's API
  is the *sanctioned* automation route, so the physical-robot black-box is unnecessary there — the
  rig matters only for app-only, API-less sportsbooks, which are also the venues that limit winners.

### 7. How *our* robot / HID rig would look to these systems (conceptual, honest)

- **Gantry + conductive stylus makes a REAL capacitive contact** → non-zero `force` and a real
  `majorRadius` (with tolerance) → it does **not** match the zero-force/zero-radius synthetic-injection
  signature of §2; no jailbreak/Frida/hooking → RASP (§2) sees a clean stock device; `isCaptured`
  false; no accessibility flag set. At the *mechanism* layer it is the most finger-like automation. `[Community]`/`[Documented]`
- **But behavioral biometrics (§1) would still see non-human structure:** machine-regular timing,
  repeatable landing points, a narrow force/radius spread (a rigid tip ≠ a compliant fingerpad),
  straight constant-velocity swipes, and — the biggest tell — a **CoreMotion flatline**: a clamped
  phone has no grip micro-tremor or orientation change coupled to each tap, so the HMOG channel that
  fingerprints *humans* is simply absent. `[Benchmark]`
- **HID path** (Pi USB/BT gadget + AssistiveTouch pointer — `[[../yolo-training/15-raspberry-pi-input-converter]]`,
  `[[../yolo-training/13-exposing-device-controls]]`): iOS synthesizes genuine touch events from the
  pointer, so UITouch-level force/radius read as real — **but enabling AssistiveTouch sets
  `isAssistiveTouchRunning = true`**, the exact §2 flag that is *also* the §3 ADA-protected flag. An
  operator literally cannot cleanly separate our rig from a disabled user on that bit.
- The agent "brain" (fixed camera + external compute) is **entirely off-device**; no on-device signal
  observes it. The only on-device footprint is the touch stream itself.
- *(Mapping only — not instructions to defeat any control.)*

## Sources

- [BioCatch — Visa to acquire BioCatch](https://www.biocatch.com/press-release/biocatch-to-join-visa) · [TechTimes $2.4B](https://www.techtimes.com/articles/322888/20260803/visa-acquires-biocatch-24-billion-betting-behavior-catches-what-transactions-miss.htm) · [Bot Attacks](https://www.biocatch.com/use-case/origination/bot-attacks) — behavioral biometrics mainstreamed; timing tells persist under mimicry `[Documented]`
- Apple docs: [UITouch.force](https://developer.apple.com/documentation/uikit/uitouch/force) · [majorRadius](https://developer.apple.com/documentation/uikit/uitouch/majorradius) · [isAssistiveTouchRunning](https://developer.apple.com/documentation/uikit/uiaccessibility/isassistivetouchrunning) · [isSwitchControlRunning](https://developer.apple.com/documentation/uikit/uiaccessibility/isswitchcontrolrunning) · [isVoiceOverRunning](https://developer.apple.com/documentation/uikit/uiaccessibility/isvoiceoverrunning) · [UIScreen.isCaptured](https://developer.apple.com/documentation/uikit/uiscreen/iscaptured) — the exact signal APIs `[Documented]`
- [HMOG (arXiv 1501.01199)](https://arxiv.org/html/1501.01199v3) · [Continuous-auth survey (arXiv 2001.08578)](https://arxiv.org/html/2001.08578v2) — motion/grasp/touch biometrics, method taxonomy `[Benchmark]`
- [ios-touch-gesture-automation-detector](https://github.com/arrrtem22/ios-touch-gesture-automation-detector) — WDA/synthetic touches = sustained zero force + zero/unnaturally-stable radius `[Community]`
- [freeRASP-iOS](https://github.com/talsec/Free-RASP-iOS) · [Appdome emulator/jailbreak fraud](https://www.appdome.com/dev-sec-blog/emulator-jailbreak-fraud-prevention/) · [Approov capture vectors](https://approov.io/knowledge/securing-user-level-functions-in-ios-applications) — RASP + screen-capture risk surface `[Documented]`
- [NIH PMC12354049 — fraud prevention excludes assistive-tech users](https://pmc.ncbi.nlm.nih.gov/articles/PMC12354049/) `[Benchmark]` · [ADA.gov AI & disability discrimination](https://www.ada.gov/resources/ai-guidance/) · [Auditing AI for ADA](https://know-the-ada.com/auditing-ai-systems-for-ada-compliance/) `[Documented]`
- [GammaStack — bookmaker limiting signals/tiers](https://www.gammastack.com/blog/how-to-avoid-bookmaker-limitations/) · [OddsShopper — arb bans](https://www.oddsshopper.com/articles/betting-101/arbitrage-betting-limits-getting-banned) `[Community]`
- [createit — AI-vision vs courtsiding (latency numbers)](https://igaming.createit.com/news/ai-vision-vs-courtsiding-stopping-live-betting-fraud/) · [courtsiders.com — feed/TV delay](https://courtsiders.com/) `[Community]`
- [SEON — multi-accounting/matched betting](https://seon.io/resources/multi-accounting-matched-betting/) · [Fingerprint — gnoming](https://fingerprint.com/blog/multi-accounting-matched-betting/) `[Documented]`
- [Polymarket CLOB intro](https://docs.polymarket.com/developers/CLOB/introduction) · [market-maker trading](https://docs.polymarket.com/developers/market-makers/trading) · [public data quickstart](https://docs.polymarket.com/quickstart) · [geoblock](https://docs.polymarket.com/api-reference/geoblock) — official bot/API path, geo-gated `[Documented]`

## Open questions / follow-ups

- Do the major US sportsbook apps actually embed behavioral-biometric SDKs (BioCatch-class), or only
  device/geo (`[[02-geolocation-and-location-integrity]]`)? Need a traffic/SDK teardown to confirm.
- Can `isCaptured` be triggered by our fixed external *camera*? No — a camera is off-device and never
  sets it; confirm no AirPlay/HDMI capture path is in the perception stack.
- Quantify the CoreMotion-flatline tell: how discriminative is "no motion coupled to taps" alone vs.
  a real seated/propped human whose phone is also near-still? → flag in `questions.md`.
- Does enabling AssistiveTouch for the HID path (`[[../yolo-training/13-exposing-device-controls]]`)
  measurably raise flagging, and is relying on that flag even defensible given §3? Ties to `hid-vs-gantry`.
- Prediction-market terms drift: does Polymarket's ToS/geoblock stance on automated trading hold at
  our target date, and does it differ for its API vs. app surface?
