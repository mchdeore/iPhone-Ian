---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, ml-and-sports-markets, math, game-theory, tennis, soccer, minimax, mixed-strategies]
---

# Game Theory — Mixed Strategies in Sports (Serves and Penalties)

**TL;DR**
- Pros come **surprisingly close to equilibrium**: win rates are equal across serve directions (Wimbledon) and kick directions (penalties).
- But tennis servers **switch direction too often**. The serial-independence test fails in large samples, and women's play fits equilibrium less closely than men's.
- That predictability is a model feature: a server's *next* serve direction is partly forecastable, and serve direction feeds point-win probability.

**Builds on:** [[Game Theory — Foundations for Sports, Poker and Markets]]; feeds [[Tennis — Player and Matchup Modeling]] and [[Markets — Point Importance and Leverage in Tennis]].

## Two testable predictions of minimax

1. **Equal payoffs:** the win rate from each action used should be equal (the indifference principle).
2. **Serial independence:** choices shouldn't be predictable from past choices.

## Tennis serves

| Study | Data | Equal payoffs | Serial independence |
|---|---|---|---|
| **Walker & Wooders (AER 2001)** | Wimbledon finals | ✅ Consistent with minimax [1] | ❌ Players switch too often [1][2] |
| **Hsu, Huang & Tang (comment)** | Broader men's, women's, juniors | ✅ Passes all W&W tests [2] | ✅ |
| **Gauriot, Page & Wooders** ("Nash at Wimbledon") | ~half a million points / ~300k serves | Men ✅; women less close [3][4] | ❌ Switch too often [3] |
| **Dynamic thesis (2025, Wimbledon 2022)** | Point-level win probabilities | Static test on first serves in rejects; **dynamic** win probabilities ≈ equal [5] | — |

## Soccer penalties

- **Palacios-Huerta (Review of Economic Studies 2003), "Professionals Play Minimax":** scoring rates of 81.1% (weak side) vs 82.7% (strong side) are statistically equal, and choices are serially independent. Remarkably consistent with equilibrium [6][7].
- **Pushback:** with more than two actions (left/centre/right), equal win rates **no longer hold**; serial independence still does [8].

## How we use this

- **Serve-direction model:** P(next serve wide | last two serves, score, importance) from Match Charting Project shot-by-shot data. Too-frequent switching means the returner (and a model) can lean. That's a small edge in p for the Markov chain.
- **Pressure points:** test whether equilibrium play *breaks down* on high-importance points. Klaassen–Magnus found serving gets harder there ([[Markets — Point Importance and Leverage in Tennis]]). Do players also become more predictable?
- **Market angle:** if a player's patterns become predictable late in matches (fatigue), the market won't price it, so it's a candidate signal for the fade.

## Pitch in

- [ ] Sports: replicate the Walker–Wooders test on Match Charting data for 20 top players; add a "predictability under pressure" column.

## Sources

1. [Walker & Wooders — Minimax Play at Wimbledon (AER 91(5), 2001)](https://www.math.stonybrook.edu/~gaston/print/Old/WimbledonAER.pdf) `[Benchmark]`
2. [Hsu, Huang & Tang — comment (AER)](https://ah.lib.nccu.edu.tw/bitstream/140.119/68756/1/4408.pdf) `[Benchmark]`
3. [Gauriot, Page & Wooders — Nash at Wimbledon](https://opus.lib.uts.edu.au/bitstream/10453/116715/1/SSRN-id2850919.pdf) `[Benchmark]`
4. [Wooders — Spring 2018 slides](https://www.smeal.psu.edu/lema/documents/wooders-spring-2018-pdf.pdf) `[Benchmark]`
5. [Dynamic minimax behaviour in pro tennis serves (Emory thesis)](https://etd.library.emory.edu/concern/etds/pn89d8101) `[Benchmark]`
6. [Palacios-Huerta — Professionals Play Minimax (LSE eprint)](https://eprints.lse.ac.uk/26561/) `[Benchmark]`
7. [LSE impact case — Palacios-Huerta](https://lse.ac.uk/Research/Assets/impact-pdf/Palacios-Huerta.PDF) `[Documented]`
8. [Sentana Lledó — penalty kicks with more actions (Essex)](https://www1.essex.ac.uk/economics/documents/eesj/lledo.pdf) `[Benchmark]`

## Related

- **Summary:** [[State of — Sports Analytics]] · [[State of — ML and Sports Markets]] · [[State of — Math]]
