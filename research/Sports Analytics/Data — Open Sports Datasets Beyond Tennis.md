---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [sports-analytics, machine-learning, ml-and-sports-markets, datasets, statsbomb, nflverse, football-data]
---

# Data — Open Sports Datasets Beyond Tennis

**TL;DR**
- Tennis isn't the only sport the sports-analytics members care about. Free, high-quality data exists for **soccer (StatsBomb events, football-data.co.uk with closing odds)** and **NFL (nflverse play-by-play since 1999)**.
- **football-data.co.uk's closing odds** make it the easiest place to practise the whole ML-and-markets pipeline (calibration, Benter test, Kelly, backtest) before tennis in-play data is ready.
- Check licences: "free to download" isn't "free for commercial use".

**Builds on:** [[Tennis — In-Play Market Research]] §3 (Sackmann data) and [[Markets — Backtesting Without Fooling Yourself]].

## Sources by sport

| Sport | Dataset | What | Licence notes |
|---|---|---|---|
| Soccer | **StatsBomb open-data** (GitHub) | JSON events, lineups, matches, **360 freeze-frames** for selected matches; `statsbombpy` reads it without auth [1][2] | **Non-commercial**; credit StatsBomb when publishing [3] |
| Soccer | **football-data.co.uk** | Decades of European results as CSV **with closing odds from multiple bookmakers**; recommended for betting backtests [4] | Check terms |
| American football | **nflverse** | Play-by-play since 1999, rosters, schedules, EPA; R and Python packages [4] | Community-maintained |
| American football | **StatsBomb AMF open data** | CSV, Parquet, JSON [5] | Non-commercial |
| Tennis | Sackmann repos, Betfair BASIC | See the tennis note and the backtesting note | — |
| Basketball | `nba_api` | Not covered by our search; check the repo | — |

## A practice project for newcomers

**"Benter on the Premier League":** fit a simple Poisson/Elo model on football-data.co.uk history, run the **calibration-by-edge** analysis ([[Markets — Calibration Beats Accuracy for Betting Models]]), the **Benter test** against closing odds ([[Markets — Model plus Market - Blending and the Benter Test]]), and a **bootstrap-Kelly** bankroll simulation ([[Markets — Kelly Sizing Under Model Uncertainty]]). Every method transfers to tennis.

## CV crossover

StatsBomb 360 freeze-frames plus our YOLO experience give a computer-vision on-ramp for sports people. It's the soccer analogue of the TrackNet/court-homography work in the tennis note.

## Pitch in

- [ ] Sports: do the Premier League practice project; post calibration and Benter results.
- [ ] Anyone: add NBA/NHL sources with licences.

## Sources

1. [StatsBomb open data (Brown VR wiki)](https://www.vrwiki.cs.brown.edu/scientific-data/statsbomb-open-data) · [GitTrend — statsbomb/open-data](https://gittrend.io/repo/statsbomb/open-data) `[Documented]`
2. [statsbombpy](https://github.com/statsbomb/statsbombpy) `[Documented]`
3. [mplsoccer — StatsBomb module (licence note)](https://mplsoccer.readthedocs.io/en/latest/mplsoccer.soccer.statsbomb.html) `[Documented]`
4. [Free sports datasets for models and backtesting](https://sportsapis.dev/free-sports-datasets) `[Community]`
5. [StatsBomb AMF open data](https://github.com/statsbomb/amf-open-data) `[Documented]`
