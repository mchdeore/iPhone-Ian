---
type: research
status: answered
author: marc
date: 2026-10-05
tags: [sports-analytics, machine-learning, tennis]
---

> Imported verbatim from SpinSight `docs/TENNIS_RESEARCH.md`. The canonical copy lives in SpinSight; this is a snapshot. Companion: [[Tennis — Player and Matchup Modeling]].

# Freddy Kruger — Tennis In-Play Research & Checklist

**Target:** live in-play tennis win markets on Polymarket, faded on the single-break-of-serve overreaction. **Philosophy:** win on *creative new tech and signals the market doesn't use*, not on low-latency C++. This doc is (1) the model/data background, (2) the strategy-mapping (use / don't use each approach), (3) the creative-tech frontier, and (4) the research checklist.

---

## 1. The core inefficiency (why this market, quantified)

**Brown (Economic Journal 2014):** in-play tennis mispricing is **~10× higher than pre-match, averaging a 5.3% discrepancy**, driven mainly by **overreactions to single breaks of serve** that "vanish within minutes." A single mid-set break converts to a set win only **~70–75%** of the time, yet odds swing violently. That gap — panicked market price vs. true ~72% conversion — is the edge.

**The key structural truth (from the model research):** the classic tennis win-probability model is *deliberately unmoved by momentum* — it recomputes win-prob purely from the new score. **Momentum is empirically small** (~7% next-point bump, and even that is partly strategic effort allocation, and it's killed by the between-games rest). So when the market re-prices a break by *more* than the pure score-change justifies, it's pricing in momentum that the data says barely exists. **That's the fade.**

---

## 2. How tennis win-probability models are built (the prior)

The whole hierarchy runs on two numbers: **p** = P(player A wins a point on serve), **q** = P(player B wins a point on serve). Everything propagates up:

- **point → game → set → match** via closed-form / Markov equations (O'Malley 2008; Klaassen-Magnus give the exact *in-play win-prob-from-any-score* recursion — the function we need for live pricing).
- **Key fact:** match win-prob depends mainly on the *difference* p − q, not absolute levels.
- **Assumption:** points i.i.d. — *false but only mildly* (tested on ~90k Wimbledon points); good enough as the baseline fair value.

**Getting p, q per player:**

- **Surface-blended tennis Elo** (Sackmann): 50/50 blend of surface-specific + overall Elo (surface-only alone predicts worse); best-of-5 conversion *widens* the favorite; K-factor scales with match count.
- **Barnett-Clarke serve/return adjustment:** f_ij = f_t + (f_i − f_av) − (g_j − g_av) → matchup-specific serve-win prob feeding the Markov chain.
- **Modern SOTA:** Ingram's Bayesian hierarchical point-based model; in-match **empirical-Bayes updating** of p,q as the match reveals today's form.

**Honest limitations to code around:** surface non-comparability (serve edge much bigger on grass than clay); best-of-3 vs best-of-5 branching; **five-set fatigue** (serve speed/points-won decline late — constant-p over-prices the server); **retirement tail risk** (unmodeled, can gap the market); weather. Calibrate everything by **Brier score**; note Elo is still slightly worse than betting odds — the market is usually efficient, edges are *episodic* (the spikes around breaks).

---

## 3. What tennis data/stats are tracked

**Free / open (Jeff Sackmann — the backtest fuel):**

- tennis_atp / tennis_wta — match results + per-match stats back to 1960s–70s.
- tennis_pointbypoint — sequential point-by-point, good ATP/WTA coverage since ~2012.
- **Match Charting Project** — crowdsourced *shot-by-shot* (type/direction/depth/error) for 5,000+ matches. Nothing else like it publicly.

**Live / paid (for the actual product):** Sportradar Tennis API (live scores + point-by-point where available, paid); tennis-api.com (cheaper REST point-by-point). *The Markov model only needs "who won each point," so a cheap live scoreboard feed suffices.*

**Stats — predictive vs. noise:**

- **Predictive (they ARE p,q):** return points won %, 1st/2nd-serve points won %, Dominance Ratio. Break points saved/converted % (clutch) — but high-variance in one match, use shrinkage.
- **Noise:** total points won ("most useless stat"), raw serve speed / winner counts without context. Box scores don't encode *point importance* — a double fault at 40–0 ≠ at break point.

---

## 4. Strategy-mapping — USE / DON'T USE each approach we discussed

| Approach (from our earlier work) | Tennis fit | Verdict |
| :-- | :-- | :-- |
| **Bayesian filter (prior + measurements)** | The tennis win-prob model IS a rigorous, independent prior — better than any market we considered. Filter maintains fair value; measurements update p,q live. | **USE — core.** Best-fit market for the filter precisely because a real structural prior exists. |
| **Overreaction detector / fade** | The whole thesis. Market moves > score-change-justified after a break = the flag. | **USE — the strategy itself.** |
| **Adaptive/learned gain** | Learn how much to trust each novel signal (grunt, fatigue-CV) by its historical hit-rate vs. outcomes. | **USE — later.** Great home for the learned-trust idea once signals exist. |
| **News aggregation (Track C)** | Tennis is barely news-driven intra-match; pre-match news (injury withdrawals) matters but is a different game. | **DON'T USE intra-match.** Keep for pre-match injury/withdrawal only. |
| **Live radio/audio speech (Track B)** | No spoken market-moving info in a match — BUT broadcast *audio* has grunts/crowd (see §5). Repurpose the audio *pipeline*, not speech-scoring. | **REPURPOSE — audio yes, speech no.** |
| **Tiny-N significance discipline** | Tennis gives thousands of breaks/matches → N is huge. The discipline still applies but the problem inverts. | **USE — and it finally has power.** |
| **Point-in-time / leak guards, event-sourcing, config-per-market engine** | All directly applicable; each match is an "event stream." | **USE — unchanged.** |
| **Maker-only execution, time-stops, paper-trade first** | Still mandatory — fade via limit orders into the panic; exit as fair value reconverges. | **USE — unchanged.** |
| **Low-latency C++ race** | You'd lose to Betfair bots on pure speed; the edge here is base-rate mispricing (persists seconds-to-minutes) + novel signals. | **DON'T USE — deliberately.** Win on signal, not speed. |

---

## 5. The creative-tech frontier (what makes this YOURS, ranked by value × feasibility)

Legend: **[PROVEN]** published+reproducible · **[PLAUSIBLE]** research support, unvalidated for this exact use · **[MOONSHOT]** speculative.

The market's proven weakness is overreacting to breaks that mean little. **These signals aim to detect who is *actually* tiring/tightening BEFORE the next break — the exact window to fade the overreaction.** A normal tennis model has none of these.

1. **Time-between-points + timeout events** — **[PROVEN], do first, zero GPU.** Progressive lengthening = documented choke/fatigue tell (timestampable from the broadcast clock, no CV). Medical/bathroom timeouts *causally* raise the odds of the timeout-taker winning the next set (Blything 2024) — a tradeable event, not noise.
2. **Serve-speed rolling decline vs. match baseline** — **[PROVEN physiology], high feasibility.** Serve speed provably drops with fatigue; the broadcast overlay often shows it — scrape it. Market underweights it.
3. **Grunt pitch (F0) trend** — **[PROVEN research], high feasibility, genuinely novel.** Grunt pitch rises through a match; the SCORE! dataset+CRNN (Stappen/Schuller) predicts stroke success from a 1-second grunt. Broadcast-audio-only, reuses the audio pipeline. *Nobody is trading this.*
4. **Facial-emotion / body-language state** — **[PLAUSIBLE], the differentiated moonshot with a real precedent.** Kovalchik-Reid (MIT Sloan 2018) predict seven pro emotional states from broadcast faces. The leap — "visible emotion at game N predicts games N+1..N+3" — is unvalidated, and *that gap is the edge if it holds.*
5. **Movement efficiency / court-coverage shrinkage** — **[PLAUSIBLE], medium.** Fatigue shrinks court coverage and slows change-of-direction; extractable from the CV pipeline (TrackNet + pose + homography to a top-down mini-court).
6. **Crowd-noise sentiment + commentator NLP** — **[PLAUSIBLE], medium, weaker.** Crowd emotion classifiable from spectrograms; commentator sentiment via RoBERTa. Noisier link to individual next-games perf.
7. **VLM → calibrated win-prob end-to-end** — **[MOONSHOT].** Use a vision-language model as a *feature extractor* ("rate visible fatigue 0–10 this changeover") feeding a simple model — NOT as an oracle.

**The CV foundation is a solved, open-source problem:** TrackNet (ball, 99.7% precision on broadcast), YOLO (players), ResNet court-keypoints + homography to a top-down court (TennisProject, TRACE, Roboflow tutorial), mmpose/YOLO-Pose (body pose). All run on a single GPU from a broadcast stream. Ranks 1–4 are buildable solo *today*.

**The strategic point:** ranks 1–3 are cheap, physiologically-grounded *leading* fatigue indicators; rank 4 is the differentiated moonshot with published precedent. This is precisely the "push new tech creatively" edge — signals the sharps' pure-price models don't ingest.

---

## 6. RESEARCH CHECKLIST

### A. Validate the core inefficiency (make-or-break, do first)
- Reproduce Brown's overreaction on **Polymarket** specifically: pull in-play tennis price history (CLOB /prices-history), align to point-by-point score, measure how far the price overshoots after a single break vs. the ~72% base rate, and how much reverts within minutes.
- **Polymarket vs. Betfair vs. model** efficiency: is Polymarket's *retail* in-play flow less efficient than Betfair's (where the sharks are)? This decides whether the edge survives.
- Overshoot-vs-spread: does the reversion beat Polymarket's 0.75% fee + the bid-ask? Maker-fill realism.

### B. Build the prior (the fair-value model)
- Implement Klaassen-Magnus win-prob-from-any-score recursion (the in-play engine).
- Build p,q estimation: surface-blended Sackmann Elo + Barnett-Clarke serve/return adjustment.
- Add in-match Bayesian updating of p,q (empirical-Bayes) so today's form is reflected.
- Calibrate on Sackmann tennis_pointbypoint (2012+); score by Brier; handle best-of-3/5, surface, retirement tail.

### C. Data pipeline
- Historical: ingest Sackmann tennis_atp/wta + pointbypoint + Match Charting Project.
- Live score feed: evaluate Sportradar vs tennis-api.com vs free scoreboards (need who-won-each-point, fast enough).
- Broadcast stream capture for the CV/audio signals (which streams, legality, quality).

### D. Creative signal R&D (the fun part — prove each adds lift over the pure model)
- **Time-between-points + timeout detector** (do first, no CV) — does it lead breaks?
- **Serve-speed decline** — scrape overlay / read radar; rolling vs. match baseline.
- **Grunt F0 tracker** — librosa/openSMILE + the SCORE! pipeline; does rising pitch lead fatigue?
- **Facial-emotion / body-language** (Kovalchik-Reid style) — FER model or VLM feature; test "emotion at game N → games N+1..N+3."
- **CV movement/court-coverage** (TrackNet + pose + homography) — coverage shrinkage as fatigue.
- For EACH signal: measure incremental predictive lift over the base model (encompassing test), rank-IC, and whether it *leads* the market's break-overreaction.

### E. Strategy & risk
- Fade rule: threshold on (model fair value − market price) right after a break; size by the gap.
- Time-stop / exit as score-driven fair value and market reconverge; avoid holding into retirement risk.
- Restrict to ATP/WTA main tour (skip ITF/Challenger: integrity + liquidity).
- Paper-trade maker-only; gate every signal on rolling rank-IC across matches before it trades.

### F. Creative moonshots to scope (if the base works)
- VLM-as-feature-extractor per changeover (fatigue/frustration 0–10).
- Multimodal fusion: pose + grunt + face + score into one learned in-play state.
- "Pre-break predictor": can the novel signals flag an *impending* break before it happens (front-run the overreaction)?

---

## 7. Why this is the right creative project

It has a **rigorous prior** (so the filter is grounded), a **documented, quantified inefficiency** (Brown's 5.3%/10×), a **discrete trigger** (the break — no NLP ambiguity), **massive sample** (kills tiny-N), and — uniquely — a **deep bench of novel signals with real published precedent** (grunt acoustics, facial emotion, fatigue biomechanics) that the pure-price sharks don't use. It's the market where "push new tech creatively" is not a gimmick but the actual edge.

*Full citations: RESEARCH.md Part VIII (market pick) + the model/CV research feeding this doc. Strategy machinery: FINDINGS.md. Companion doc: `TENNIS_PLAYER_MODELING.md` (player & matchup modeling notes).*

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — Machine Learning]]
