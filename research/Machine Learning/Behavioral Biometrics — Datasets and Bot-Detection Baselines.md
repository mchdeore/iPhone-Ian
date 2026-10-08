---
type: research
status: in-progress
author: marc
date: 2026-10-07
tags: [machine-learning, cybersecurity, robotics, behavioral-biometrics, bot-detection, touch-dynamics, imu, datasets, benchmark]
---

# Behavioral Biometrics — Datasets and Bot-Detection Baselines

**TL;DR**
- There are public touch and motion datasets (Touchalytics, BioIdent, HMOG, HuMIdb) and two published human-vs-bot detectors built on them (BeCAPTCHA-Mobile, zkSENSE).
- zkSENSE explicitly tested a **resting/docked phone** scenario. That's the closest published proxy for our clamped-phone "CoreMotion flatline" question.
- Proposal: rebuild a baseline detector and score our own rig's telemetry against it, to get a **number** for detectability instead of a guess.

**Useful for:** Cybersecurity (quantifies the threat model in [[Betting Apps — Behavioral and Automation Detection]]), Robotics (consumes data from [[Touch Telemetry — Measuring What the Rig Emits]]).

## Datasets

| Dataset | What's in it | Notes |
|---|---|---|
| **Touchalytics** (Frank et al., IEEE TIFS 2013) | Strokes: location, timestamp, pressure, finger area. 30 features per stroke | Median EER 0% intra-session, 2–3% inter-session, <4% after one week. The canonical feature set. `[Benchmark]` |
| **BioIdent** (Antal et al.) | Touch dynamics, ~100 users, multiple sessions | Often fused with HMOG for motion features. `[Benchmark]` |
| **HMOG** (Yang, Sitova, Gasti et al., SenSys 2014) | Touch + accelerometer/gyro + orientation, 120 users, sitting and walking, reading/typing/map tasks | Mostly taps and keystrokes; few swipes. `[Benchmark]` |
| **HuMIdb** (BiDA Lab) | 600 users, 14 mobile sensors | Used for BeCAPTCHA-Mobile; download location not confirmed yet. `[Benchmark]` |
| **TouchDB** (BiDA Lab) | Swipe benchmark | [listing](https://bidalab.eps.uam.es/listdatabases?id=TouchDB) |

A 2022 HMOG+BioIdent fusion (51 users, one session) reported up to ~82% accuracy with RF, SVM and KNN. That's a realistic "simple baseline" number. `[Benchmark]`

## Published human-vs-bot detectors

- **BeCAPTCHA-Mobile** (Acien et al., *Eng. Appl. of AI* 98:104058, 2021). Classifies one drag-and-drop gesture plus accelerometer as human or bot. Bots were synthesized with **GANs and handcrafted methods**, so it's a mimicry-aware threat model. `[Benchmark]`
- **zkSENSE** (PoPETs 2021, Brave Research). A real touch makes a tiny IMU response; software-injected touches don't. Reported ~92% accuracy across attack scenarios including **device resting, artificial vibration, and docked on a swinging cradle**. Sensor evidence is proven with zero-knowledge proofs, and attestation takes ~3 s. `[Benchmark]`
  - **Relevance to us:** a gantry tap on a clamped phone *is* a physical touch. Whether its IMU response looks like a hand-held tap or like a dock is exactly what our measurements can answer.

## Proposed work: detectability benchmark

1. **Baseline.** Train a human-vs-synthetic classifier on Touchalytics-style stroke features plus IMU-window features (RF/GBM first, then a small 1D-CNN). Generate synthetic negatives the way BeCAPTCHA does.
2. **Evaluate on our rig.** Feed in recordings from [[Touch Telemetry — Measuring What the Rig Emits]] for each condition (human hand-held, human on table, gantry, HID pointer) and report AUROC and per-feature importance.
3. **Report back, don't tune.** Publish the scores to Cybersecurity and Robotics as a threat-model input. This is measurement, not an evasion loop. It also gives numbers for the ADA/accessibility question in the parent note: how close a seated human on a table gets to the "robot" score.
4. **Evaluation hygiene:** separate users between train and test, and report variance across sessions. Touch-auth papers often leak users between splits (see FETA below).

## Pitch in (ML people)

- [ ] Find working download links for HMOG, BioIdent and HuMIdb, and note the licences here.
- [ ] Reproduce the Touchalytics 30-feature extractor. The code goes in the repo, not the vault.
- [ ] Build the baseline classifier and post its AUROC here.

## Sources

- [Touchalytics (arXiv 1207.6231)](https://arxiv.org/pdf/1207.6231) · [BioIdent](https://www.ms.sapientia.ro/~manyi/bioident.html) · [HMOG (arXiv 1501.01199)](https://arxiv.org/pdf/1501.01199) · [Hold On and Swipe — HMOG+BioIdent fusion (arXiv 2201.08564)](https://arxiv.org/pdf/2201.08564) · [FETA: Fair Evaluation of Touch-based Authentication (arXiv 2201.10606)](https://arxiv.org/pdf/2201.10606) `[Benchmark]`
- [BeCAPTCHA on HuMIdb (arXiv 2005.13655)](https://arxiv.org/pdf/2005.13655) · [BeCAPTCHA workshop paper (arXiv 2002.00918)](https://arxiv.org/pdf/2002.00918) `[Benchmark]`
- [zkSENSE (PoPETs 2021)](https://www.petsymposium.org/popets/2021/popets-2021-0058.php) · [Brave Research summary](https://brave.com/research/zksense-a-friction-less-privacy-preserving-human-attestation-mechanism-for-mobile-devices/) · [zkSVM code](https://github.com/iquerejeta/zkSVM) `[Benchmark]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — Cybersecurity]] · [[State of — Robotics]]
