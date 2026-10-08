---
type: research
status: in-progress
author: marc
date: 2026-10-07
tags: [sports-analytics, machine-learning, cybersecurity, betting, sharp-detection, responsible-gambling, account-profiling, tennis]
---

# Betting — Account-Level Behavior Models

**TL;DR**
- Besides *how you tap*, sportsbooks run two behavior models on *what you bet*: **risk profiling** (find and limit winners) and **harm detection** (required by regulators).
- Both ignore the input device entirely.
- An automated in-play strategy like our tennis fade (many in-play bets, fast, at odd hours) **matches both profiles at once**. That's a strategy-viability issue, not a hardware one.

**Useful for:** Cybersecurity (the account layer above device signals in [[Betting Apps — Behavioral and Automation Detection]]), ML (harm-marker modeling is a real, legitimate classification problem).

## 1. Risk profiling: winners get limited

- **Kaunitz, Zhong & Kreiner (2017).** Bet whenever a book's odds are an outlier against the market-consensus average. It was profitable in simulation and with real money. Within a few months books **capped stakes (some to ~$1) and required "manual inspection"** before accepting bets. William Hill attributed restrictions to bonus abuse and taking "more than their fair share" of enhanced prices. `[Documented]`
- Signals from the parent note: beating the closing line, bet timing vs line moves, precise stakes, only taking stale or +EV prices. `[Community]`
- **For the tennis track** ([[Tennis — In-Play Market Research]]): any book-based version of the break-of-serve fade should budget for a **finite account lifetime**. Polymarket's sanctioned API (parent note §6) doesn't have this counterparty problem.

## 2. Harm detection: required by regulators

- **The UK Gambling Commission requires** operators to monitor at least **7 indicator categories**: spend, spending patterns, time spent, gambling behaviour, customer-led contact, use of management tools, and account indicators. Financial indicators alone aren't enough. Many weak signals can add up to a strong one, and strong indicators need automated processes. `[Documented]`
- **Flagged behaviours** include a **high number of in-play bets**, high staking after a big win, overnight play, deposit velocity, and repeated limit changes. `[Documented]`
- **Enforcement example:** Paddy Power/Betfair systems "were not sensitive enough"; one customer deposited £12,000 in 15 days before manual review. `[Documented]`
- **The overlap:** an automated in-play tennis strategy produces high in-play counts, round-the-clock sessions and rapid bets. That trips *harm* markers even when it's winning, which leads to customer-interaction checks and possible restrictions, independent of the risk team.

## 3. Open data for modeling

- Harvard's Division on Addiction runs **the Transparency Project**, a public repository of de-identified operator transaction data used in sports-betting behavior studies (e.g. 2023 "big wins" paper). Download availability for specific datasets isn't confirmed yet. `[Community]`
- That makes harm-marker prediction a legitimate sports-analytics + ML project: predict later self-exclusion from early betting behavior.

## Pitch in (sports analytics people)

- [ ] Backtest the tennis fade and count in-play bets per day and session hours. How "harm-shaped" is the strategy?
- [ ] Find the Transparency Project dataset pages and record the access terms here.
- [ ] Compare the UK (UKGC) indicator list with Ontario (AGCO) and a US state, since we're Canadian/US based.

## Sources

- [MIT Technology Review — Kaunitz et al.](https://www.technologyreview.com/2017/10/19/67760/the-secret-betting-strategy-that-beats-online-bookmakers/) · [Digit](https://www.digit.fyi/?p=5308) `[Documented]`
- [UKGC — remote customer interaction guidance](https://www.gamblingcommission.gov.uk/guidance/advice-to-the-gambling-commission-on-a-statutory-levy/requirement-5-customer-interaction-guidance-for-remote-gambling-licensees-sr) · [UKGC — spotting harmful gambling](https://www.gamblingcommission.gov.uk/licensees-and-businesses/guide/page/spotting-harmful-gambling) · [UKGC — Paddy Power/Betfair findings](https://www.gamblingcommission.gov.uk/public-and-players/guide/page/paddy-power-betfair-findings) · [iGB — customer interaction](https://igamingbusiness.com/legal-compliance/customer-interaction-alert/) `[Documented]`
- [Division on Addiction](https://divisiononaddiction.org/) · [UNLV abstract — operator data via Transparency Project](https://digitalscholarship.unlv.edu/gaming_institute/2013/may30/14) `[Community]`
