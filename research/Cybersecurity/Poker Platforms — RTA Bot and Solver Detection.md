---
type: research
status: answered
author: marc
date: 2026-10-10
tags: [cybersecurity, machine-learning, math, game-theory, poker, rta, bot-detection, behavioral-analytics]
---

# Poker Platforms — RTA Bot and Solver Detection

**TL;DR**
- Poker rooms hunt **three different things:** (1) **full bots** (no human), (2) **RTA** (human clicks but **solver/charts decide**), (3) **illegal software** (HUDs, screen scrapers, hopper tools). Detection is mostly **server-side hand history + timing + client integrity**, not “how you tap.”
- **Solver-shaped play** leaves statistical fingerprints: **pot-fraction bet sizes**, **mixed frequencies** that match equilibrium at **hard nodes only**, and **think times** that don’t scale with tree size.
- **Physical phone rigs** ([[Betting Apps — Physical-Agent Red Team and Detection Hardening]]) do **not** hide strong RTA — operators catch **decisions**, not keystroke physics.
- This note maps signals for **defensive / compliance** understanding. Not evasion guidance.

**Builds on:** [[System Design — Related Work - Robots and Bots that Play Games]], [[Game Theory — Real-Time Poker Under Personal Compute and Time Banks]], [[Betting Apps — Behavioral and Automation Detection]], [[Betting — Account-Level Behavior Models]].

---

## 1. Threat taxonomy (what platforms ban)

| Class | Human at keyboard? | Edge source | Example enforcement |
|---|---|---|---|
| **Poker bot** | No | Automated client or rig | Permanent ban, fund confiscation (GGPoker 2020: 40+ accounts, $1.2M+) [1] |
| **RTA / solver use** | Yes | GTO Wizard, Pio, charts at decision time | PokerStars “zero tolerance” RTA; bans incl. solver use **only at critical moments** [2][3] |
| **Prohibited tools** | Yes | HUDs, RTA overlays, table scrapers | Software scans + ToS [4] |
| **Collusion / chip dumping** | Yes | Shared info, soft play | Graph + timing correlation |
| **Multi-accounting** | Yes | Bonus abuse, gnoming | Device/payment/IP linking (same vendors as sportsbooks — SEON/Fingerprint) |

Our **gantry + VLM** stack, if pointed at **real-money multiplayer**, is class **bot** or **bot+RTA**, not a loophole. Play-money / vs-CPU / own app stays in research scope ([[System Design — Card-Playing Gantry Rig Architecture]]).

---

## 2. Detection layers

### 2.1 Client integrity (desktop-first; mobile growing)

- **Process / window enumeration:** known solver processes, overlay windows, VM hooks.
- **Screen capture / overlay detection:** transparent click-through HUDs.
- **Memory integrity:** injected DLLs, debuggers (same RASP family as [[Betting Apps — Device Integrity and Attestation]]).
- **Mobile:** jailbreak/root, sideload, accessibility automation — plus **no official “solver API”** on apps.

**Gap:** stock phone + physical taps bypass **injection** signals. Poker defense does **not** rely on UITouch alone.

### 2.2 Behavioral analytics on **decisions** (main weapon)

Operators store **complete hand histories** (billions of hands for major sites). Offline ML + rules:

| Signal | Why it fires |
|---|---|
| **Think time vs complexity** | Humans slow down on turn/river multi-way pots; RTA users often **flat** latency or **fast only** when solver pre-loaded |
| **Bet sizing entropy** | Solver menus → clusters at **33/50/66/75/100/125% pot**; repeated exact fractions across sessions |
| **Frequency matching GTO** | Near-equilibrium mix at **high-leverage nodes** (river bluff catch, thin value) while rest of profile is recreational — “solver at critical moments” [2]. Bluff:value ratios per spot type → [[Game Theory — Bluff Frequencies Regimes and How Players Learn Them]] §3.3 |
| **Line conformity** | Same abstract line (check-raise sizing sequences) repeated across stakes/opponents |
| **Multi-table uniformity** | Identical timing/sizing across 4–16 tables — human variance breaks |
| **Preflop chart adherence** | 3-bet/fold frequencies match published charts tighter than population |
| **Deviation under pressure** | Less tilt noise; emotionally flat EV-max patterns |

PokerStars publicly describes **behavioral indicators** across massive samples, not single-hand proof [3].

### 2.3 RTA-specific partnerships

- **GGPoker × GTO Wizard (2025):** “Fair Play Check” — vendor compares play to **solver library**; 31 accounts blocked Feb 2025 [4][5].
- Implication: operators **outsource** “does this look like Pio/GTO Wizard output?” to specialists with **precomputed equilibrium databases**.

### 2.4 Human review and community

- **Hand history requests**, live security sits, reported collusion.
- **Known pro / high-stakes** pools monitored tighter.

### 2.5 Account graph (parallel to sportsbooks)

- Device fingerprint, payment, IP, withdrawal patterns ([[Betting Apps — Behavioral and Automation Detection]] §5).
- **Chip dumping** and **collusion rings** via graph ML.

---

## 3. What **doesn’t** work as primary poker bot defense

| Signal | Problem |
|---|---|
| **Accessibility / AssistiveTouch flag** | ADA exposure; gantry may not set it anyway |
| **Synthetic UITouch (zero force)** | Physical stylus ≠ injection ([[Betting Apps — Behavioral and Automation Detection]]) |
| **CAPTCHA between hands** | UX killer; rarely used mid-session |
| **Blocking all charts off-table** | Unenforceable; they target **in-session** RTA |

---

## 4. Attacker capability vs detector (conceptual)

| Attacker setup | Client integrity | Decision analytics | Typical outcome |
|---|---|---|---|
| Desktop + Pio + overlay | **High** catch risk | **High** if sizes/freqs match solver | Ban wave |
| Phone + chart on second device | Lower client signal | **Medium** — timing gaps if human transcribes | Review / ban on volume |
| Full bot (software clicker) | Medium | **High** — multi-table + timing | Fast ban |
| **Gantry + model on host** | Low on stock iPhone | **High** — still solver/bot EV signature | Ban when CLV/winrate flags |
| Strong human, no tools | Clean | Low | Allowed |

**Takeaway for cybersecurity research:** poker anti-cheat is **economic + statistical**, like **sharp betting limits** ([[Betting — Account-Level Behavior Models]]), not device attestation alone.

---

## 5. Blue-team recommendations (operator / vendor)

1. **Model RTA and bots separately** in the threat model — different features, same sanctions.
2. **Invest in hand-history ML:** complexity-adjusted latency, sizing cluster detection, node-critical GTO distance metrics.
3. **Partner or internalize solver libraries** for “distance from equilibrium” scoring (GGPoker path).
4. **Time-to-act telemetry** on every action with street, players, pot size, legal action count — feed **anytime** anomaly detectors.
5. **Don’t rely on touch biometrics** for poker; optional for **account sharing** (same device, two humans) only.
6. **Honeypot nodes:** rare line combinations where recreational players deviate but **RTA always balances** — high precision flags for review.
7. **Transparency:** publish banned tool list and appeal process — reduces ADA/false-positive fights on accessibility.

---

## 6. Links to our ML/math work

- **Personal-machine solver** ([[Game Theory — Real-Time Poker Under Personal Compute and Time Banks]]) produces **exactly** the sizing/frequency clusters detectors hunt — another reason to keep experiments in **sim / play-money / OpenSpiel**.
- **Exploit discipline** (node lock only with evidence) reduces *some* uniformity but not latency/size tells under automated lookup.
- **Rig STRIDE** ([[Security — STRIDE Threat Model for the Phone Rig]]): host compromise = attacker runs **any** policy on your hardware — operator sees outcomes, not your tailnet.

---

## Open questions / follow-ups

- [ ] Quantify “GTO distance” metrics used commercially (papers vs marketing).
- [ ] Mobile app integrity: do major apps run App Attest per session like sportsbooks ([[Betting Apps — Device Integrity and Attestation]])?
- [ ] Compare detection **false-positive** rate for strong regs vs RTA — public data scarce.

---

## Sources

1. [Pokerfuse — GGPoker reimbursements after RTA enforcement](https://pokerfuse.com/news/poker-room-news/211765-ggpoker-reimburses-over-4000-players-following-recent-rta/) `[Documented]`
2. [PokerNews — PokerStars battle against RTA](https://www.pokernews.com/news/2023/10/pokerstars-battle-against-real-time-assistance-44628.htm) `[Documented]`
3. [Pokerfuse — inside PokerStars' RTA arsenal](https://pokerfuse.com/news/poker-room-news/219952-inside-pokerstars-arsenal-how-it-combats-rta/) · [PokerNews — how PokerStars deals with bots](https://www.pokernews.com/news/2020/04/how-does-pokerstars-deal-with-bots-37068.htm) `[Documented]`
4. [PokerNews — GGPoker and GTO Wizard team up](https://www.pokernews.com/news/2025/03/ggpoker-and-gto-wizard-team-up-to-keep-poker-fair-48110.htm) `[Documented]`
5. [Pokerfuse — GGPoker RTA blocks (2025)](https://pokerfuse.com/news/poker-room-news/) — verify latest wave when updating `[Community]`

## Related

- **Summary:** [[State of — Cybersecurity]] · [[State of — Math]] · [[State of — Machine Learning]] · [[State of — System Design]]
