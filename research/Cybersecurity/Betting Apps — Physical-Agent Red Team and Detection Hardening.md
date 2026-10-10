---
type: research
status: answered
author: marc
date: 2026-10-10
tags: [sports-analytics, machine-learning, cybersecurity, robotics, gambling, ios, threat-model, red-team, blue-team]
---

# Betting Apps — Physical-Agent Red Team and Detection Hardening

**TL;DR**
- A **physical phone rig** (gantry + grounded stylus, or HID pointer) is a different threat class than jailbreak, Frida, emulators, or headless API clients. Most **integrity and geo SDKs target software compromise**, not real capacitive contact on a stock device.
- That does **not** mean “invisible.” Weak spots for attackers are gaps in **touch+IMU fusion**, over-reliance on **accessibility flags**, and **account-level** models that may fire late. Strong spots for operators are **server-side betting analytics**, **linking**, and **regulatory harm monitoring** — device-agnostic.
- This note is for **defensive proposals**: what we’d tell a sportsbook CISO/trust team to build or buy. It maps capabilities; it is **not** an evasion playbook.

**Builds on:** [[Betting Apps — Behavioral and Automation Detection]], [[Betting Apps — Detection Vendor and SDK Landscape]], [[Betting Apps — Device Integrity and Attestation]], [[Betting — Account-Level Behavior Models]], [[Security — STRIDE Threat Model for the Phone Rig]], [[System Design — Card-Playing Gantry Rig Architecture]].

---

## 1. Threat actor we’re modeling

| Actor | Goal | Typical stack |
|---|---|---|
| **Script kiddie** | Bonus abuse, multi-account | Emulator + `adb`, shared IPs, stolen cards |
| **Software botter** | Arb / +EV scraping via app or patched client | Frida, WDA, replayed API, VPN + GPS spoof |
| **Physical-agent operator** | Same betting edge, but **app-only**, no tampered binary | Off-device brain + **real touches** on **unmodified** phone |

Our research rig is the third row. It is closest to **Tapster-class QA hardware** plus a **VLM/YOLO perception loop** ([[Prior Art — Touchscreen Robots and Software Agents]], [[System Design — Card-Playing Gantry Rig Architecture]]).

**Legal/ToS:** Real-money automation on regulated sportsbooks violates operator terms and may violate local law. Red-team work belongs under **contract, scoped test accounts, and responsible disclosure** — not production abuse.

---

## 2. How the robot would be built (architecture)

Conceptual stack — same as our v2 design, swapped to a betting app as the “game.”

```
Operator / policy
       │
       ▼
┌──────────────── Host (trusted enclave) ─────────────────┐
│  Odds feed + model  →  bet decision  →  action plan       │
│  Screen capture (USB / AirPlay)  →  VLM/YOLO  →  UI state │
│  px → mm calibration  →  command queue  →  FluidNC USB    │
└───────────────────────────┬───────────────────────────────┘
                            │ G-code / servo Z
                     CoreXY gantry + grounded stylus
                            │
                     Stock iPhone (App Store app, no jailbreak)
```

**Alternative input path:** Raspberry Pi (or similar) as **USB/BT HID** moving the **AssistiveTouch pointer** ([[iOS Control — AssistiveTouch Pointer Mechanics]], [[iOS Control — Raspberry Pi HID Input Converter]]). No gantry; still off-device brain.

**What never touches the phone:** model weights, strategy code, alternate data feeds (scout latency, exchange prices). The app only sees **touch events** and normal **network/API** traffic from a legitimate client.

**Operational extras an adversary might add (still architectural, not a recipe):**
- Phone **clamped** in a fixture (repeatable coordinates).
- **Dedicated device + SIM + payment instrument** per identity (gnoming hygiene).
- **Human-in-the-loop** for KYC, 2FA, geo-sensitive flows ([[iOS — Face ID, Autofill and 2FA Constraints]]).
- **Separate network** for capture (avoid `UIScreen.isCaptured` from AirPlay to a monitor the app might infer).

---

## 3. Detection stack today — what each layer sees

| Layer | Catches well | Blind to physical rig on stock phone |
|---|---|---|
| **GeoComply / Incognia** ([[Betting Apps — Geolocation Compliance]]) | VPN, mock location, emulator, many tamper signals | Legitimate GPS at licensed location; **real device** |
| **App Attest / RASP** ([[Betting Apps — Device Integrity and Attestation]]) | Re-signed app, jailbreak, debugger, Frida, cloned attestation keys | **No** client tamper if binary is store-clean |
| **Synthetic touch heuristics** (zero force/radius) | XCTest/WDA injection | **Real** UITouch from capacitive stylus or HID-synthesized pointer |
| **Accessibility flags** | Naïve “AT = bot” rules | Gantry: flags off. HID: AssistiveTouch **on** — collides with ADA ([[Betting Apps — Behavioral and Automation Detection]] §3) |
| **Screen capture (`isCaptured`)** | AirPlay/recording while betting | Off-device **camera** does not set flag; USB capture may or may not — must not mirror to external display |
| **Behavioral biometrics** (BioCatch-class — **unconfirmed** in books) | Timing entropy, motion coupling, session micro-patterns | **Weakest known gap** if SDK absent or model under-trained on “docked phone” |
| **SEON / Fingerprint linking** | Multi-account clusters | Single well-isolated identity passes until **behavior** correlates |
| **Account-level sharp/harm models** ([[Betting — Account-Level Behavior Models]]) | CLV, stake patterns, in-play velocity, promo abuse | **Does not care** how touch was produced |

**Headline:** Physical automation **moves the fight** from “compromised client” to “is this interaction plausibly human **and** is this account plausibly recreational.”

---

## 4. Why detection has holes (root causes)

### 4.1 Wrong threat model in product requirements

Most RFPs say: emulator, root, VPN, stolen credentials, bonus fraud. Vendors ship **device integrity + geo**. Physical QA robots are filed under “manual testing,” not fraud — so **features aren’t prioritized**.

### 4.2 Client-only signals are observable to the adversary

Anything the app measures to block bots (timing rules, force thresholds) can be **studied in a logger app** on owned hardware ([[Touch Telemetry — Measuring What the Rig Emits]]). Defense needs **server-side fusion** and **non-replayable challenges**, not static thresholds.

### 4.3 IMU channel underused

zkSENSE-class work: real touches create **micro IMU transients**; pure software injection does not ([[Behavioral Biometrics — Datasets and Bot-Detection Baselines]]). A clamped phone produces a **different** motion signature than hand-held — closer to “docked/resting” baselines. Many production apps **don’t sample CoreMotion at touch-down** at all.

### 4.4 Accessibility as a shortcut

`isAssistiveTouchRunning` is **legally toxic** as a hard block. Mature shops use it as **context**. Immature logic creates both **false negatives** (gantry without AT) and **false positives** (disabled users).

### 4.5 Account limits are the real control — but late

Books already **gub** sharp accounts ([[Betting Apps — Behavioral and Automation Detection]] §5). That protects **margin**, not **fairness during the window** when the bot trades. Harm-detection rules can **also** restrict automated in-play volume — but often **after** exposure.

### 4.6 Venue split

**Polymarket** exposes a **sanctioned API**; physical bypass is irrelevant there ([[Betting Apps — Behavioral and Automation Detection]] §6). **App-only sportsbooks** are exactly where a rig would matter — and where **counterparty risk** motivates post-hoc limits, not necessarily pre-bet bot blocks.

---

## 5. What still burns the operator (even with a “perfect” touch mimic)

Not evasion advice — **residual risk for the attacker**, i.e. where defenders should **double down**.

1. **Closing-line value (CLV)** and **stale-line timing** — server logs only.
2. **Cross-account graph** — device farm drift, payment reuse, withdrawal patterns.
3. **Promo / bonus arbitrage** — matched betting signatures.
4. **In-play latency edge** — courtsiding and model-based fades leave **bet timing vs feed** fingerprints ([[Tennis — In-Play Market Research]]).
5. **Regulatory harm triggers** — high in-play count, overnight sessions, velocity ([[Betting — Account-Level Behavior Models]] §2).
6. **Manual review** — KYC, source-of-funds, phone calls.
7. **Market making response** — line moves, personal limits, captcha/step-up on withdrawals.

**Implication for our team:** cybersecurity on the **rig** (host takeover = phone takeover) matters more than tweaking stylus physics ([[Security — STRIDE Threat Model for the Phone Rig]]).

---

## 6. Blue-team proposals — what should change for safer operators

Framed as **security program recommendations** we could put in a consulting memo.

### 6.1 Adopt an explicit “physical automation” threat in the model

- Add STRIDE/LINDDUN-style scenario: **“Benign binary, non-human actuator.”**
- Red-team **contracted** physical taps on staging, with labeled telemetry — same method as [[Touch Telemetry — Measuring What the Rig Emits]].

### 6.2 Touch + IMU attestation at interaction time

- On **high-risk actions** (login, deposit, claim promo, place in-play bet): sample **accelerometer/gyro** in a fixed window around `touchDown`, fuse with **stroke features** (Touchalytics-style: timing, curvature, radius spread).
- Train detectors on **docked-phone humans** and **accessibility users**, not only hand-held lab users — reduces ADA false positives and closes “table prop” false negatives.
- Prefer **challenge–response** (“trace this arc”) over always-on blocking — zkSENSE/BeCAPTCHA line shows feasibility; latency cost must be product-owned.

### 6.3 Stop standalone accessibility blocks

- Policy: accessibility state **never** sole deny; feeds a **calibrated** score with human review path.
- Document in **ADA audit trail** ([[Betting Apps — Behavioral and Automation Detection]] §3).

### 6.4 Server-side session integrity

- Bind **App Attest assertion** to **bet submission** with monotonic counter ([[Betting Apps — Device Integrity and Attestation]] §3).
- Rate-limit **in-play** submissions per device/session; flag **machine-regular inter-bet intervals** server-side (harder to tune against than client-only checks).
- Correlate **client-reported session duration** with **touch event density** — zero touches but API activity ⇒ different fraud class (API abuse), but **touch without scroll/explore** ⇒ bot-like session shape.

### 6.5 Instrument the vendor gap

- Complete [[Betting Apps — Detection Vendor and SDK Landscape]] for top books: confirm whether **behavioral SDK** is embedded.
- If only geo + RASP: **budget line item** for behavioral or build internal stroke+IMU model from first-party logs (with consent/disclosure in privacy policy).

### 6.6 Account-level controls earlier in the funnel

- **Pre-limit scoring:** don’t wait for 200+ bets; score **first-week** CLV proxy, sport mix, stake precision, promo-only play.
- Separate **sharp** workflow from **harm** workflow to avoid wrong restriction type.
- For in-play: **acceptance delay** + **stake cap** as default for new accounts — hurts arb more than recreational UX if tuned.

### 6.7 Integrity of the automation *you* allow

- Where API trading is legal (exchanges, Polymarket): funnel automation to **keys + rate limits**, not screen scraping — reduces attack surface.
- Bug bounty scope: **physical device lab** tier for trusted researchers.

### 6.8 Operator security culture

- Treat **host compromise** of any trading automation as **SEV-1** (same as wallet keys) — aligns with our rig STRIDE findings.

---

## 7. Detection maturity model (summary table)

| Maturity | Characteristics | Physical-agent residual risk |
|---|---|---|
| **L1 — Compliance** | Geo + KYC + App Attest on money moves | **High** on touch mimic; limits come late via CLV |
| **L2 — Integrity** | + RASP, emulator/root, linking SDK | **Medium** — still weak on gantry |
| **L3 — Behavioral** | + touch/IMU fusion, ADA-safe models | **Low–medium** — depends on docked-phone training |
| **L4 — Economic** | + real-time CLV, graph, in-play timing, promo graph | **Low** for sustained profit — account capped or banned |

Most US sportsbooks are **documented at L1–L2** for device signals; **L4** partially exists for winners, not necessarily for bot **classification**.

---

## 8. Research backlog (our team)

| Item | Owner domain | Output |
|---|---|---|
| Run touch telemetry matrix | Robotics | CSV + scatter/repeatability in [[Touch Telemetry — Measuring What the Rig Emits]] |
| Score vs Touchalytics + IMU baseline | ML | AUROC in [[Behavioral Biometrics — Datasets and Bot-Detection Baselines]] |
| Vendor table 3+ books | Cybersecurity | Update [[Betting Apps — Detection Vendor and SDK Landscape]] |
| Tennis fade “harm shape” backtest | Sports analytics | Counts in [[Betting — Account-Level Behavior Models]] |
| STRIDE DFD for host↔phone | Security | Mermaid in [[Security — STRIDE Threat Model for the Phone Rig]] |

---

## 9. One-paragraph “pitch to the company”

> Your geo and RASP stack assumes the enemy **tampered with the client**. A **physical actuator on an honest app** is outside that model: attestation passes, touches look capacitive, and accessibility heuristics either **miss** (gantry) or **punish disabled users** (HID). **Fix:** treat **stroke + IMU fusion** and **server-side economic anomalies** as first-class controls; never block on accessibility alone; red-team with **contracted hardware**; move sharp detection **earlier** in account life. **Account-level** models already catch sustained edge — device biometrics decide whether you catch it **before** payout and promo bleed.

---

## Related

- **Summary:** [[State of — Cybersecurity]] · [[State of — Robotics]] · [[State of — Machine Learning]] · [[State of — Sports Analytics]]
