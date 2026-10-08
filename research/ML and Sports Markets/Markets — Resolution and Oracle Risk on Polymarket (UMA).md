---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, cybersecurity, ml-and-sports-markets, polymarket, uma, oracle, resolution-risk]
---

# Markets — Resolution and Oracle Risk on Polymarket (UMA)

**TL;DR**
- Polymarket outcomes are settled by **UMA's optimistic oracle**. Someone proposes an answer with a **$750 bond**; if nobody disputes within the window it's final; disputes go to a **UMA token-holder vote**.
- It usually works, but there are documented failures: a ~$7M Ukraine-minerals market resolved YES with no official deal (whale-influence suspected), and a NASCAR dispute ballooned to $60k of bonds on a $10k market.
- For tennis, resolution risk is low (results are unambiguous) **except** for retirements, walkovers and suspended matches. Read each market's rules.

**Builds on:** [[Markets — Polymarket Order Book, Fees and Execution]]. Execution risk is one layer; this is settlement risk.

## How settlement works

- **Propose:** stake a $750 USDC.e bond on an outcome [1].
- **Challenge window:** if no dispute, it settles automatically; the loser of any dispute forfeits their bond [1].
- **Dispute → vote:** UMA holders decide [1]. Settlement takes at least ~2 hours if uncontested, days to weeks if escalated [2].

## Documented failure modes

| Case | What happened | Lesson |
|---|---|---|
| **NASCAR (July)** | A trader posted 40 proposals (one per driver) at $750 each; all 40 were disputed → $60k staked on a $10k market. Voters ruled "Too Early" although UMA docs don't require waiting for inspection [1] | Rules about *timing* are ambiguous |
| **Ukraine minerals (~$7M)** | Resolved YES although reportedly no official agreement existed; a "UMA whale" was suspected [1][3] | Voter concentration; one report claims whales hold up to 7.5M of 20M staked UMA (unverified) [1] |
| **Ambiguous wording** | Holders with positions interpret criteria in their own favour [1] | Wording risk is the biggest driver |

## Cross-venue contrast

Kalshi names **source agencies** in contract terms filed with the CFTC and verifies within hours to ~1 day. The same real-world event can resolve **differently** on the two venues because of wording and timing differences [2][4]. See [[Markets — Cross-Venue Prices - Polymarket, Kalshi and Betfair]].

## Tennis-specific checks (do before trading any market)

- What happens on **retirement mid-match**? (Sportsbooks vary: some void, some settle on advancement. Read the market text.)
- Walkover before the start, a suspended match finishing the next day, a venue change: does the market's end date allow for it?
- Model **resolution risk as a small probability of a 50/50 or void outcome** in the EV calculation for in-play positions held into those edge cases.

## Pitch in

- [ ] Sports: collect the rules text from 10 Polymarket tennis markets; tabulate the retirement and walkover handling.
- [ ] Security: monitor UMA disputes on any market we hold (alert on proposal/dispute events).

## Sources

1. [NexusFi — Polymarket/UMA oracle dispute](https://nexusfi.com/a/prediction-markets/polymarket-uma-oracle-dispute) · [CryptoSlate — NASCAR $60k dispute](https://cryptoslate.com/polymarket-10k-bet-on-nascar-race-turns-to-60k-dispute-following-zelensky-controversy/) · [pm.wiki — UMA](https://pm.wiki/it/data/glossary/uma) `[Community]`
2. [DeFi Rate — how Kalshi and Polymarket settle](https://defirate.com/?p=5575) `[Community]`
3. [Coin360 — oracle vote manipulation](https://coin360.com/news/polymarket-oracle-vote-manipulation-scandal) `[Community]`
4. [Orrery — Polymarket vs Kalshi resolution rules](https://orrery.me/learn/polymarket-vs-kalshi-resolution-rules) `[Community]`
