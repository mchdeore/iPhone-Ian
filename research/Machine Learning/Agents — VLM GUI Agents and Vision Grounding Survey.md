---
type: research
status: answered
author: marc
date: 2026-10-05
tags: [machine-learning, vlm, gui-agent, vision-grounding, mobile-agent, fine-tuning, prompting]
---

# VLM GUI agents & vision grounding — literature survey

## Question

What's the state of the art in vision-language model GUI agents? How do they ground natural language to screen coordinates? What approach works for a camera photo of a phone screen (not a screenshot)? Do we need fine-tuning or off-the-shelf prompting?

## Key findings

### Mobile GUI agents — major projects

- **Mobile-Agent family (Alibaba)** — most mature line. v1→v2→v3→v3.5 with GUI-Owl-1.5 (Feb 2026) hitting 56.5 OSWorld, 71.6 AndroidWorld, 80.3 ScreenSpotPro. Multi-agent architecture (planning/decision/reflection) gives 30%+ over single-agent. 9.3k stars. `[Documented]` https://github.com/X-PLUG/MobileAgent · https://arxiv.org/abs/2602.16855
- **CogAgent (Tsinghua)** — 18B VLM, dual-resolution, screenshot-only beats HTML-based methods. `[Documented]` https://arxiv.org/abs/2312.08914
- **SeeClick** — pure visual agent, created ScreenSpot benchmark. `[Documented]` https://arxiv.org/abs/2401.10935
- **OS-Atlas** — open-source foundation model for GUI grounding, 13M-element corpus. `[Documented]` https://arxiv.org/abs/2410.23218
- **UI-TARS (ByteDance)** — desktop agent product, not an academic paper. `[Community]` https://github.com/bytedance/UI-TARS-desktop
- **Architecture consensus:** Vision-only works (CogAgent, SeeClick, OS-Atlas all screenshot-only). Vision+accessibility-tree works better but needs platform access — dead end for black-box iPhone. Our path is vision-only by necessity, which the literature validates.

### Vision grounding — how agents locate what to tap

- **UGround** — strongest open-source pure-vision grounder, 10M elements, +20% over prior SOTA. `[Benchmark]` https://arxiv.org/abs/2410.05243
- **OmniParser (Microsoft)** — detection+caption pipeline that boosts GPT-4V. Detects UI elements, captions them, feeds to VLM. `[Documented]` https://arxiv.org/abs/2408.00203
- **ZonUI-3B** — **our ideal training target.** 3B params, trainable on single RTX 4090 with 24K samples. 84.9% ScreenSpot, 86.4% ScreenSpot-v2. `[Benchmark]` https://arxiv.org/abs/2506.23491
- **Accuracy ceiling:** ScreenSpot-Pro (professional high-res) best standalone model = 18.9%. With multi-view ensemble: 74.0%. **Camera photos will be strictly harder than screenshots — no published work on this gap.** This is a genuine research contribution opportunity. `[Benchmark]`
- **GUI-Primitives (2026):** 19 VLMs tested. 60–92% of predictions fall outside both candidate regions. VLMs understand instructions but can't locate precisely. `[Benchmark]` https://arxiv.org/abs/2608.21832

### Physical robot phone agents — almost no prior work

- **BrainyBot** — CV robot taps phone to play games. Closest analog. `[Academic]` https://github.com/DeMaCS-UNICAL/TappingBot
- **Tappy** — $80 DIY delta, no AI agent. `[Community]`
- **Robo-Harness K1 (2026)** — VLM→robot via perception-as-tools, not phone-specific but architecture maps well. `[Academic]` https://arxiv.org/abs/2609.29389
- **This intersection (physical robot + VLM GUI agent) is genuinely novel.** Feature, not bug.

### Prompting vs fine-tuning

- **Zero-shot works for prototyping, not for reliability.** GPT-4V + OmniParser boosts accuracy but still far below fine-tuned models.
- **ZonUI-3B proof:** small fine-tuned model (3B) beats large prompted models. Fine-tuning is the path to reliability.
- **Our path:** Phase 2 = UGround/OmniParser zero-shot → collect data → Phase 3 = fine-tune ZonUI-3B on our own iPhone camera captures.

### Architecture design for our agent

```
Camera photo of iPhone screen
    │
    ▼
 [Perception] — UGround / OmniParser zero-shot (Phase 2)
    │     → ZonUI-3B fine-tuned on our captures (Phase 3)
    │ bounding boxes + element descriptions
    ▼
 [Planning] — VLM (GPT-4V / Claude / Gemini) reasons over UI state
    │ "Tap the login button" → action: tap(x=342, y=518)
    ▼
 [Action] — screen coordinate → gantry coordinate → G-code → tap
    │
    ▼
 [Verification] — next camera frame → did it work? → retry or continue
```

Key insight: perception (what's on screen, where) and planning (what to do) are separate. Perception benefits from fine-tuning on our domain (iPhone camera photos). Planning works fine with off-the-shelf VLMs.

## Sources

- https://arxiv.org/abs/2602.16855 — GUI-Owl-1.5 / Mobile-Agent v3.5
- https://arxiv.org/abs/2312.08914 — CogAgent
- https://arxiv.org/abs/2401.10935 — SeeClick / ScreenSpot
- https://arxiv.org/abs/2410.23218 — OS-Atlas
- https://arxiv.org/abs/2410.05243 — UGround
- https://arxiv.org/abs/2408.00203 — OmniParser
- https://arxiv.org/abs/2506.23491 — ZonUI-3B
- https://arxiv.org/abs/2608.21832 — GUI-Primitives benchmark
- https://arxiv.org/abs/2609.29389 — Robo-Harness K1
- https://github.com/X-PLUG/MobileAgent
- https://github.com/bytedance/UI-TARS-desktop
- https://github.com/DeMaCS-UNICAL/TappingBot

## Related

- **Summary:** [[State of — Machine Learning]]
