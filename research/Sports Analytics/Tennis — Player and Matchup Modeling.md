---
type: research
status: answered
author: marc
date: 2026-10-05
tags: [sports-analytics, machine-learning, tennis]
---

> Imported verbatim from SpinSight `docs/TENNIS_PLAYER_MODELING.md`. The canonical copy lives in SpinSight; this is a snapshot. Strategy spec: .

# Freddy Kruger — Player & Matchup Modeling Notes

**Purpose:** A running research log of *what tennis actually measures* — the full stat taxonomy, what separates elite from average (and best-in-category from great), and why some matchups are lopsided while others are formalities. Everything here is filtered through one question: **what can we model, and does it plausibly give us an edge the pure-price market doesn't already have?**

Companion to [[Tennis — In-Play Market Research]] (the strategy spec). That doc is the *how we trade*; this doc is the *what we can know about players* that feeds better priors and better fade signals. Cross-reference tags: **[PRIOR]** improves fair-value, **[SIGNAL]** candidate live fade signal, **[FILTER]** helps decide when NOT to fade.

---

## 0. The one-paragraph mental model

Everything in tennis collapses to two numbers per match: **p** = server-A's point-win-on-serve, **q** = server-B's. But *those two numbers are not constants* — they're the output of serve quality, return quality, surface, matchup interaction, fatigue, and pressure-state. This doc is a catalog of the levers that move p and q, so we can (a) start with a sharper prior than a naive Elo, and (b) know which live observations should actually update p/q vs. which are noise the market wrongly reacts to.

---

## 1. The stat taxonomy — everything players/analysts track

Organized by whether it's **predictive** (it *is* p/q, or moves it), **contextual** (matters conditionally), or **noise** (market reacts to it, we shouldn't).

### 1a. The single most predictive stat: Dominance Ratio (DR) **[PRIOR]**
- **Definition:** (return points won %) ÷ (service points *lost* % = opponent's return points won %). It's essentially a signal-to-noise ratio for a performance — points won relative to points lost, normalized.
- **Why it matters:** In a Random Forest on ATP match outcomes, DR carried **~76% of the feature importance** — it dominates every other box-score stat. DR > 1.0 almost always means you won; the rare DR>1 losses are the "played well, lost anyway" matches.
- **The deep insight for us:** DR captures the *break-conversion efficiency* that raw serve/return percentages miss. A player can win 65% of service points and still lose if their return game collapses at the wrong moment — DR exposes that. **Modeling use:** a DR-based in-match estimate is a cleaner "who's actually winning independent of scoreline" number than the score itself — exactly the kind of thing that tells us a break was *deserved* (don't fade) vs. *a blip* (fade).

### 1b. Serve stats
- **1st-serve points won %, 2nd-serve points won %** — these ARE the serving half of p. Predictive. 2nd-serve-points-won is the more revealing one (it strips out the free aces and shows the real rally-starting quality).
- **Aces / service speed / 1st-serve %** — mostly **noise in isolation**. Aces are surface- and matchup-dependent; raw speed without placement is empty. The market (and casual bettors) overweight aces.
- **Serve +1** — the serve and the *very next shot* treated as one tactical unit. ~a quarter of all points end in the 2-3 shot window that contains the Serve+1. Elite servers aren't just fast — they're *setting up* a putaway. **[SIGNAL]** candidate: a decline in Serve+1 effectiveness (having to play more balls after the serve) is a *leading* fatigue/pressure tell before the raw serve % drops.

### 1c. Return stats
- **Return points won %** — the return half of q, and per the ATP predictive-variable work, **return performance is a fundamental driver of outcomes across all players**, not just returners. Underweighted by casual markets that fixate on serving.
- **Return depth / return aggression** — the best return strategy is to *induce an unforced error*, and it's surface-sensitive: works ~17% of the time on clay vs ~15% grass vs ~13% hard. Return quality is where clay upsets are born.

### 1d. Pressure / clutch stats **[SIGNAL] [FILTER]**
This is the richest vein for us because it's where the market's momentum-overreaction and reality diverge most.
- **Break point conversion %** — tour avg ~40%; elite returners >45%. High single-match variance → **use shrinkage** (a 3/4 BP-conversion day is mostly luck).
- **Break points saved %** — the serving-side clutch mirror.
- **Pressure Points** — a *specific enumerated set* of high-leverage scores: 0-30, 15-30, 30-30, 0-40, 15-40, 30-40, 40-40, 40-AD (serving = defending; returning = attacking). Performance here "often outperforms overall stats" for mentally strong players and collapses for weak ones.
- **Why this is our sweet spot:** a break that happens *on* a pressure point by a known clutch player is more "real" (repeatable) than a break gifted by a couple of loose points from the favorite. **A clutch profile per player lets us distinguish a deserved break (don't fade) from a variance break (fade hard).** This is a direct upgrade to the fade rule in `TENNIS_RESEARCH.md §E`.

### 1e. Rally / shot-quality stats
- **~70% of points end within 4 shots.** Tennis is mostly a first-strike game, not a grinding game. Winners of matches average ~18 winners vs ~14 for losers — **aggression beats attrition** even at elite level.
- **Winner-to-unforced-error ratio** — cleanest single indicator of "consistent AND aggressive." A player whose W:UE ratio craters mid-match is genuinely declining (real), vs one whose *scoreline* dipped on a couple of net cords (noise).
- **Rally-length distribution as a fingerprint** — some players' win-prob is concentrated in short points (big servers), others in long points (grinders). This matters for matchup modeling (§3).

### 1f. Noise (market reacts, we resist)
- **Total points won** — famously "the most useless stat": you can win more total points and lose the match, because points aren't equally important (a double fault at 40-0 ≠ at break point). Box scores don't encode *point importance*.
- Raw serve speed, raw winner/ace counts without context, momentum narratives ("he's on fire").

---

## 2. What separates elite from average — and best-in-category from great

The through-line: **elite tennis is far more predictable than it looks.** Sinner/Djokovic win ~55% of *points* but ~80% of *matches* — tiny per-point edges compound massively through the scoring hierarchy. That non-linearity is *why* the Markov prior works and why the market overreacts (small score events feel bigger than they are).

### 2a. Serve — best-in-category
Not speed. It's **Serve+1 setup + placement + unpredictability**. The best servers win free-ish points not with raw pace but by making the return defensive, then ending it on the next ball. Measurable proxy: 2nd-serve points won and Serve+1 conversion, not ace count.

### 2b. Return — best-in-category **[interesting, novel-signal-adjacent]**
The differentiator is **anticipation / visual search**, and it's *measurable in research settings*: international-level returners adjust their visual-search strategy to each server, reading the ball toss and the final phase of the service motion; national-level players don't adapt as well. ML models can classify return quality from gaze fixation location/duration. → This is a genuine best-in-class differentiator that is *biomechanical and pre-contact*, which rhymes with the CV/pose signal bench in `TENNIS_RESEARCH.md §5` (a returner whose split-step/movement-initiation timing degrades is tiring — potential **[SIGNAL]**).

### 2c. Movement — best-in-category
Elite movement = **efficient court coverage + fast change-of-direction + recovery position**, and it's the *first thing fatigue degrades* (ties directly to the movement/court-coverage-shrinkage signal in the spec). Ground-stroke direction dictates movement patterns measurably on hard courts. → **[SIGNAL]** court-coverage shrinkage as a leading fatigue indicator.

### 2d. Mental / clutch — best-in-category
The pressure-point over-performers (§1d). This is a *stable player trait* over a career but *high-variance in one match*. Model as a **shrunk per-player prior**, not a live-updated number.

### 2e. Consistency (the underrated one)
W:UE ratio and the ability to hold a performance level across 3-5 sets. The 222-players-in-28-years framing (rare statistical achievements) underlines how few players sustain elite consistency. Fatigue is the enemy of consistency → and fatigue is exactly what the whole signal bench is trying to detect early.

---

## 3. Why some matchups are lopsided and others a formality

This is arguably the biggest **[PRIOR]** upgrade available: **matchup interaction effects determine win-prob beyond overall ranking.** A pure-Elo prior misses this; a matchup-aware prior doesn't.

### 3a. The lefty effect (the cleanest, most modelable interaction)
- **Mechanism:** a lefty's slice serve breaks *right-to-left* (into a righty's backhand on the ad court, especially on break points) — the mirror of what righties are used to. Spin patterns and serve targets are systematically unfamiliar.
- **Exposure asymmetry:** only ~10% of players are left-handed, so lefties practice constantly against righties while righties rarely face lefties — a *structural, persistent* edge, not a one-off.
- **Modeling use:** handedness interaction is a **free, always-available prior adjustment.** Lefty-vs-righty (especially lefty serving on ad-court pressure points) should shift p/q *before the match starts*. The market prices ranking; it under-prices handedness matchup on specific pressure points.

### 3b. Head-to-head persistence beyond ranking
- Some players *own* others irrespective of ranking — the canonical example is Nadal's persistent edge over Federer (a lefty-heavy-topspin-to-one-handed-backhand stylistic kryptonite), H2H diverging from their overall records.
- **Modeling caution:** H2H is small-N and easy to overfit (2 matches ≠ a matchup law). Use it as a **shrunk Bayesian adjustment** toward a *stylistic* explanation (why does A beat B?), not a raw H2H count. The signal is the *style interaction*, not the history.

### 3c. Stylistic rock-paper-scissors
- **Big server vs. elite returner:** whoever's specialty dominates the surface wins. On grass the server's first-strike game is decisive (first 4 shots decide 67% of points on grass vs 48% on clay); on clay the returner drags them into rallies.
- **Flat hitter vs. heavy topspin:** high topspin to a one-handed backhand (Nadal-Federer) is a known kryptonite; low slice to a topspin grinder can be too.
- **Grinder vs. grinder:** high variance, long matches, fatigue-signal-rich (good for our fatigue bench).

### 3d. Surface as a matchup modifier (huge) **[PRIOR] [FILTER]**
Surface doesn't just change p/q levels — it changes *variance*, which is central to our fade thesis:
- **Clay: ~15% MORE upsets than grass.** Long rallies + physical demands give underdogs more paths to drag favorites into trouble. Serve is a weaker weapon (aces 41% less frequent than grass). → On clay, a break "means more" (harder to get, harder to break back) → **the overreaction may be LESS wrong** → fade more cautiously.
- **Grass: fewest upsets, serve-dominated, first 4 shots decide 67% of points.** Breaks are rarer and more decisive, but a single break of a big server is often quickly answered → **classic fade territory when a favorite big-server drops one break.**
- **Hard: in between.**
- **Surface specialists:** clay-raised players win ~68% on clay vs non-specialists; grass specialists (big serve, compact swings, net play) over-perform on fast courts. Ranking alone hides this → prior should be **surface-conditional**, per the Sackmann 50/50 surface-blend already noted in the spec.

**The key strategic translation:** *the correct fade aggressiveness is surface-dependent.* The same "one break" event is a stronger fade on grass (breaks get answered) and a weaker fade on clay (breaks are earned and stick). This should become a **surface coefficient on the fade threshold** in the strategy.

---

## 4. Variance vs. Fatigue — the two player fingerprints (the heart of the fade)

**This is the core of the whole strategy, so it gets its own section.** The fade decision — "is this break a blip that reverts, or a real decline that continues?" — reduces to telling two things apart that look *identical on the scoreboard*: **variance** (noise around a stable true level, reverts) and **fatigue/decline** (a one-directional shift in the true level, does not revert). The market can't distinguish them. If we can, that IS the edge.

Crucially, each has a *player-trait* dimension (a stable fingerprint you know before the match) AND a *live* dimension (what's happening right now). Knowing a player's fingerprint tells you how to *interpret* the live signal.

> **Two complementary lenses — keep both, they are not the same idea:**
>
> **Lens A — Player-trait fingerprints (pre-match, stable).** Every player carries two independent traits: a **shot-placement variance** trait (boom-bust liner ↔ low-variance metronome, §4a) and a **stamina** trait (fast fader ↔ fitness monster, §4b). These are computed *before* the match and tell us how to *interpret* whatever we see. (This is the "players who vary in shot location a lot vs. players who tire fast" framing.)
>
> **Lens B — Live noise-vs-drift read (in-match, dynamic).** Independent of who the player is, on any given dip we ask: is this *variance* (random, mean-reverting → fade) or *fatigue/decline* (monotonic, one-directional → don't fade)? (§4c.) This is the live-signal question — "is the wobble we're watching noise or a real trend?"
>
> **They work together:** Lens A sets the prior expectation; Lens B reads the live evidence; the trade is the combination. A boom-bust player (Lens A: high variance) showing scattered directionless errors (Lens B: noise) = maximum-confidence fade. A metronome (Lens A: low variance) showing a monotonic serve-speed downtrend (Lens B: drift) = do not fade. Both lenses must stay in the spec — dropping either collapses the decision.

### 4a. Shot-placement variance as a player trait **[PRIOR][FILTER]**

Some players are inherently **high-variance ball-strikers** — they hit closer to the lines, take more risk, go for more, and so their error rate and their winner rate are *both* high (boom-or-bust). Others are **low-variance metronomes** — high margin over the net, safe targets, low unforced-error rate, grind. This is a stable, measurable style, not a mood.

- **How to measure it:** dispersion of shot landing location (Match Charting Project has shot direction/depth), unforced-error rate, winner:UE ratio *shape* (a high-variance player has fat tails — lots of winners AND lots of UEs; a low-variance player is tight around the middle). Also rally-length distribution: high-variance players end points early (their way or the error), grinders sit in long rallies.
- **Why it's decisive for the fade:** *a bad patch means completely different things for the two types.*
 - **High-variance player gets broken after spraying 3 errors** → that's *within his normal distribution*. It reverts. **FADE — this is exactly the overreaction.** The market saw "he's falling apart"; the truth is "that's just his variance, and it regresses."
 - **Low-variance metronome suddenly sprays 3 errors** → that's *far outside his normal distribution*. Something changed (fatigue, injury, tightness). **DON'T fade — the break may be real.** For a grinder, unusual errors are a genuine signal, not noise.
- **The elegant part:** the *same observation* (a break preceded by errors) flips from "fade hard" to "don't fade" depending purely on the player's variance fingerprint. This is a clean, pre-computable prior that directly gates the fade rule.

### 4b. Stamina / fatigue-resistance as a player trait **[PRIOR][FILTER]**

Separately, some players **tire fast** (their level drops in long matches / third sets / heat) and others are **physical monsters** who hold level deep into five-setters. This is also stable and measurable.

- **How to measure it:** historical performance split by set number and match duration — does the player's serve%/DR/hold% decline in set 3+ vs set 1? Performance in matches over 3 hours. Age and injury history feed it. Fitness reputation is a weak prior; the *data* split by set/duration is the real one.
- **Why it's decisive for the fade:** it tells you **which direction to expect the true level to drift** as the match goes long.
 - Fade-prone player gets broken late in a long match → if he's a **known fader**, the decline may be real → *don't fade, or fade small*. The overreaction might actually be *correct* this time.
 - Same break, but the guy is a **fitness monster** → the late-match break is more likely variance → *fade with confidence*.
- **Interaction with weather (see 4d):** heat *accelerates* the fatigue drift and *widens* the gap between faders and monsters. On a hot day, trust the fatigue read earlier.

### 4c. Live variance vs. live fatigue — the in-match discriminator **[SIGNAL]**

The player-trait priors (4a, 4b) set expectations; the **live signal bench decides which is actually happening right now.** The whole "creative signals" apparatus from `TENNIS_RESEARCH.md §5` exists to answer one question: *is the observed dip variance (reverts → fade) or fatigue (real → don't)?*

- **Points to variance (reverts → FADE):** errors are scattered/random, serve speed steady, movement/court-coverage intact, W:UE tails but mean unchanged, no time-between-point lengthening. → "He just had a loose game."
- **Points to fatigue/decline (real → DON'T FADE):** serve speed on a rolling *downtrend* vs match baseline, court-coverage *shrinking*, time-between-points *lengthening*, grunt-pitch *rising*, W:UE *mean* dropping (not just fat-tailing), second-serve% collapsing. → "He's actually breaking down." (These are one-directional; variance is not.)
- **The tell that separates them:** **variance is mean-reverting and directionless; fatigue is monotonic and one-directional.** A rolling-trend test (is the signal *drifting* or just *noisy*?) is the mathematical core. This is where a Bayesian filter earns its keep — it naturally separates a level-shift from noise around a level.

### 4d. Modifiers that scale the fatigue drift

- **Weather / heat / humidity / altitude [SIGNAL-modifier]:** heat and humidity accelerate physical decline → fatigue signals should fire earlier and the fade should back off sooner for a fading player. Altitude/thin dry air makes the ball fly → helps servers/aggressors, subtly favors the favorite (a p/q modifier, not a fatigue one). Fold weather into the fatigue model as a *rate multiplier*, not a standalone factor.
- **Best-of-5 / Grand Slam format [PRIOR]:** best-of-5 mathematically *widens the favorite's edge* (more sets wash out variance) AND makes an early break mean *even less* than in best-of-3 → **early-break overreactions are even more fadeable at Slams.** Also fatigue matters far more in best-of-5 (five-set decline is real), so the 4b stamina prior is *most* valuable at Slams. Bonus: Slams have the best liquidity — the market we actually need. This is a hard branch in the win-prob model, not a soft factor.

### 4e. Why this framing is powerful

Almost every "factor" you can name is really an input to **one of these two axes**: variance (does the dip revert?) or fatigue/decline (is the true level shifting?). Rage/tilt is a transient variance spike (reverts unless it triggers a real spiral). Injury is an extreme, non-reverting fatigue event (→ kill-switch, §6 triage). Surface changes how much a break reverts. Clutch tells you if a break was earned. Organizing the whole feature space around **variance vs. decline** keeps us from the "too many factors" trap: every candidate signal has to answer *which axis does this inform, and does it beat the base model at informing it?*

---

## 5. New modeling ideas this session surfaced (ranked by edge × feasibility)

1. **Clutch-adjusted break realness** **[SIGNAL][FILTER]** — Tag every break with (a) did it happen on enumerated pressure points, (b) breaker's shrunk clutch prior, (c) breakee's break-points-saved prior. A break that's "deserved" on these = don't fade / fade small; a variance break = fade hard. *Directly sharpens the core strategy.* Cheap, uses only score + pre-match priors.
2. **Surface-conditional fade coefficient** **[FILTER]** — Scale fade size by surface (grass > hard > clay) because breaks are answered at different rates and upset variance differs. Nearly free; big realism gain.
3. **Handedness × pressure-point prior** **[PRIOR]** — Lefty-serving-on-ad-court adjustment to p/q on break/pressure points. Always available, market underprices it.
4. **Dominance Ratio as live "true-leader" signal** **[SIGNAL]** — Track in-match DR as a scoreline-independent read on who's actually on top; divergence between DR and scoreline flags fadeable mispricings.
5. **W:UE / Serve+1 decline as leading fatigue** **[SIGNAL]** — Rolling in-match decline in winner:error ratio or Serve+1 putaway rate as an *early* fatigue read, ahead of raw serve% (complements the serve-speed/grunt/court-coverage bench already in the spec).
6. **Stylistic-matchup prior (shrunk)** **[PRIOR]** — Encode style tags (server/returner, flat/topspin, 1H/2H backhand) and learn interaction coefficients from Sackmann + Match Charting data, shrinking H2H toward style rather than raw history.
7. **Player variance fingerprint gates the fade** **[PRIOR][FILTER]** — Pre-compute each player's shot-placement variance (boom-bust vs metronome). A break-after-errors reverts for a high-variance player (fade) but signals real trouble for a metronome (don't fade). Same event, opposite action. *(§4a — top pick.)*
8. **Player stamina fingerprint sets drift direction** **[PRIOR][FILTER]** — Pre-compute per-player decline by set-number/duration. Late-match break by a known fader may be real (don't fade); by a fitness monster it's variance (fade). *(§4b — top pick.)*
9. **Variance-vs-fatigue live discriminator** **[SIGNAL]** — Rolling-trend test on the signal bench: directionless/noisy = variance = fade; monotonic drift = fatigue = don't. The mathematical core of the fade decision. *(§4c — top pick.)*
10. **Best-of-5 / Slam format branch** **[PRIOR]** — Widen favorite edge and *increase* fade aggressiveness on early breaks in best-of-5; weight the stamina prior more. Hard model branch, plus best liquidity. *(§4d — top pick.)*
11. **Injury / medical-timeout kill-switch** **[FILTER-risk]** — Visible injury or medical timeout = KILL the fade, don't size it (non-reverting tail risk). One documented exception: a timeout can *help* the timeout-taker win the next set, occasionally tradeable — but tail risk dominates. *(§7.)*

Each of these is testable with the same **encompassing-test / rank-IC / does-it-lead-the-break-overreaction** discipline the spec already mandates in §D.

---

## 6. Factor triage — model / risk / research (avoiding the "too many factors" trap)

**The meta-rule:** the base Markov model is ~90% of the value. Every extra factor is a chance to overfit noise that vanishes live. A factor only ships if it beats the base model out-of-sample (encompassing test + rolling rank-IC). Fewer validated signals > kitchen sink. With that discipline, here's where every factor discussed lands:

**MODEL these (they earn their slot):** surface coefficient (§3d); best-of-5/Slam format branch (§4d); player variance fingerprint (§4a); player stamina fingerprint (§4b); variance-vs-fatigue live discriminator (§4c); weather as a fatigue *rate multiplier*, not standalone (§4d); clutch-adjusted break realness (idea 1); handedness × pressure-point prior (idea 3); DR live true-leader signal (idea 4).

**HANDLE as risk, not alpha (kill-switches, not bet-sizers):** in-match injuries — kill the fade, retirement/gap tail dominates; pre-match injury news is a *separate track*, not intra-match alpha. Retirement tail — time-stop out before it, per spec.

**RESEARCH tier (real precedent, prove-before-trusting):** rage / tilt / on-court emotion — transient variance spike; published face-emotion precedent (Kovalchik-Reid) but the "emotion at game N → games N+1..N+3" leap is unvalidated (moonshot). Home advantage — real but small in tennis and mostly already priced; travel/scheduling fatigue is the more useful cousin, feeds §4b. Probably too small to move a threshold.

---

## 7. Open questions to chase next session
- Is the DR-vs-scoreline divergence actually predictive of reversion, or does it just restate the score? (backtest on Sackmann pointbypoint)
- Quantify the lefty pressure-point edge magnitude — is it big enough to move a fade threshold, or second-order?
- Get real numbers on break-back rates by surface (grass vs clay) — the fade coefficient needs empirical calibration, not just the qualitative "clay has 15% more upsets."
- Does clutch (pressure-point over-performance) actually persist match-to-match enough to be a usable prior, or is it mostly noise even at career scale? (this determines whether idea #1 is real)
- Can we actually separate a player's *variance* fingerprint from their *skill* in the data? (a boom-bust player and a declining player both show high UE — need shot-location dispersion, not just error counts, to tell style-variance from level-drop)
- Does the rolling-trend test (§4c) reliably distinguish monotonic fatigue-drift from noisy variance *in-match, in time to trade*, or does it only resolve after the reversion window has closed? (the whole live edge hinges on this being early enough)
- How much does the best-of-5 format actually increase early-break fadeability vs best-of-3? (quantify on Sackmann — is it a big coefficient or a rounding error?)

---

## Sources (this session)
- Dominance Ratio / predictive variables: [The Tennis Stats That Really Decide Matches (LSports)](https://www.lsports.eu/blog/the-tennis-stats-that-really-decide-matches/); [Top Predictive Variables in ATP Tennis Matches (mark911)](https://mark911.wordpress.com/2026/07/13/top-predictive-variables-in-atp-tennis-matches/); [Understanding Dominance Ratio (Scribd)](https://www.scribd.com/document/941847129/Understanding-Dominance-Ratio-in-Tennis)
- Predictability / points-vs-matches: [15 Data-Driven Facts About Professional Tennis (Medium)](https://medium.com/@josegustavolara/15-data-driven-facts-about-professional-tennis-5e3842d7a6a0)
- Return anticipation / visual search: [Skill Level in Tennis Serve Return & Visual Search (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8488081/); [Kinematics of the Return of Serve (Sport Journal)](https://thesportjournal.org/article/the-kinematics-of-the-return-of-serve-in-tennis-the-role-of-anticipatory-information/)
- Movement: [Movement Characteristics of Elite Tennis Players on Hard Courts (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3761832/)
- Pressure / clutch: [Pressure Points — the deeper dimension of tennis data analysis (TennisRatio)](https://www.tennisratio.com/articles/2025-02-2024-06-pressure-points-the-deeper-dimension-of-tennis-data-analysis/); [What Tennis Stats Reveal About Consistency, Performance & Pressure (Tenngrand)](https://tenngrand.com/what-tennis-stats-reveal-about-consistency-performance-and-pressure/)
- Lefty / matchup / H2H: [The Advantage of Lefties in One-On-One Sports (Fagan/Columbia)](http://www.columbia.edu/~mh2078/Lefties.pdf); [Profit from Being Left Handed in Tennis (Tennis Bros)](https://thetennisbros.com/tennis-tips/tactics/profit-from-being-left-handed-in-tennis/)
- Surface / upsets / specialists: [Surface, climate and tennis betting (Tennis Majors)](https://www.tennismajors.com/others-news/surface-climate-and-tennis-betting-why-conditions-move-the-odds-more-than-you-think-840272.html); [Decoding Surface Dominance (Bruin Sports Analytics)](https://www.bruinsportsanalytics.com/post/surface-dominance)
- Rally length / Serve+1 / winners-errors: [The Most Important Number in Tennis (Brain Game Tennis)](https://braingametennis.com/the-most-important-number-in-tennis/); [Match analysis and probability of winning a point in elite men's singles (PLOS One)](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0286076); [Unlock the Serve +1 Advantage (TargetBound)](https://targetboundsports.com/en/unlock-the-serve-1-advantage-research-insights)

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — Machine Learning]]
