---
type: research
status: answered
author: marc
date: 2026-10-05
tags: [machine-learning, yolo, pruning, compression, edge, computer-vision]
---

# 07 — Pruning YOLO — does it beat just picking a smaller model?

## Question

For a single-phone UI detector whose forward pass runs on the HomeLab host (not a
microcontroller), is it worth pruning a YOLO model, and if so how — vs. simply
choosing nano and quantizing?

Tags: `[Documented]` official docs/papers · `[Benchmark]` measured · `[Community]` forum/anecdotal.

## Verdict (short)

**Not worth it for this project right now.** Our YOLO runs on the host and the
closed loop is dominated by camera capture + agent/grounding + gantry motion, not a
nano forward pass (`01`, `specs/02` §7). The cheap wins are already banked: **pick
`yolo11n`** (2.6M params / 6.5 GFLOPs — already ~25% leaner than `yolov8n`'s
3.2M / 8.7 GFLOPs for similar mAP `[Documented]`), **crop-to-screen @640** (`01`'s
biggest lever), and if CPU latency bites, **INT8 via OpenVINO** ([[YOLO — Quantization by Hardware]])
— a bigger, less fragile win than pruning. Keep **structured** pruning as a documented
*fallback* only if, after quantization, the forward pass is *measured* to be the
bottleneck or we must run on weaker hardware. **Never ship unstructured pruning on
CPU — it gives zero speedup.**

## Key findings

### Structured vs unstructured — only structured speeds up CPU/edge
- **Unstructured** (zero out individual weights) keeps every tensor the same shape;
 cuDNN/oneDNN still run a *dense* convolution over the zeros — "multiplying by zero
 at full price." Needs a sparse kernel + special hardware (Ampere 2:4) to cash in. `[Community]`
- **Structured** (remove whole filters/channels) physically shrinks tensors → FLOPs
 and memory traffic actually drop → real speedup on CPU/GPU/edge. `[Documented]`
- "Unstructured pruning … does not provide any benefits in model size. To obtain
 smaller and faster networks, structured pruning needs to be applied." `[Documented]` (arXiv 2405.03715)

### Measured results
| Case | Method | Params | FLOPs | mAP Δ | Latency | Tag |
|---|---|---|---|---|---|---|
| Jetson defect det. (baseline FP16) | — | — | 17.2 G | 0.910 | 31.0 ms | `[Community]` |
| same, **unstructured 60%** | magnitude | −60% | **17.2 G (unchanged)** | −0.005 | **30.8 ms (no gain)** | `[Community]` |
| same, **structured 45%** | DepGraph L2 | −41% | **9.4 G** | −0.006 | **11.4 ms** | `[Community]` |
| YOLOv8m edge | struct + channel-wise distill | 25.85M→6.85M | 49.6→13.3 G | AP50 −2.7% | — | `[Benchmark]` |
| YOLOv8n-ALM | layer-adaptive prune + retrain | **−65.3%** | −29.6% | **+2.2%** mAP50 | — | `[Benchmark]` |
| Torch-Pruning demo (yolov8x) | DepGraph | 68.2M→20.8M | 129→41.7 GMACs | (not reported) | — | `[Documented]` |

Takeaways: the gap between "params removed" and "FLOPs removed" is the whole lesson —
FLOPs only fall when **shapes** shrink. The YOLOv8n-ALM row shows a *nano* can be
pruned ~65% and even gain mAP — but that is an **architecture redesign + full
retrain**, not stock-nano "free" pruning; it costs exactly the training effort we are
trying to avoid.

### Criteria (how to pick what to cut)
- **L1-norm filter pruning** (Li et al. 2017): rank filters by Σ|w|, drop the smallest. Simplest. `[Documented]`
- **BN-scaling / Network Slimming** (Liu et al. 2017): L1-penalize BatchNorm γ during
 training, then prune channels with small γ. Natural for YOLO (every `Conv` has a BN);
 exactly what the YOLOv8m edge paper used. `[Documented]`/`[Benchmark]`
- **Group importance** (Torch-Pruning `GroupNormImportance(p=2)`), plus Taylor / LAMP.
 A YOLOv8 study found DepGraph compresses *intermediate* layers hard, LAMP prunes more
 uniformly but loses high-frequency texture. `[Benchmark]`

### prune → fine-tune cycle
Standard loop (and Ultralytics' own forum advice): **train baseline → prune a small %
→ fine-tune to recover → repeat to target → re-export (and re-quantize)**. `[Community]`
In the Jetson case, 3 fine-tune epochs recovered 0.86→0.904 mAP. **Cost for us:**
each round is a retrain, and our training box is **CPU-only ≤16 GB** (`03`:
~10–40 min/epoch on CPU) — so iterative prune→fine-tune is disproportionately
expensive here, which further argues against it.

### Tools (status 2026)
| Tool | Kind | 2026 status | Note |
|---|---|---|---|
| **Torch-Pruning (DepGraph)** | structured, physically removes | **Active** (v1.6.1, ~3.4k★) | Best option; official `examples/yolov8`, but README warns it "is crashed due to ultralytics upgrade" → pin a commit. `[Documented]` |
| **OpenVINO NNCF filter pruning** | structured, training-time | **Active** (2025 docs) | Integrates into PyTorch training; pairs with INT8; natural if deploying via OpenVINO on CPU. `[Documented]` |
| **Ultralytics native** | — | **No native support** | "It would work only if you export the pruned model manually to ONNX." Its only official tutorial is YOLOv5 *unstructured* sparsity (zeroing) → **no CPU speedup** = the trap. `[Documented]` |
| **NNI (Microsoft)** | structured + speedup module | **Stale** | Last meaningful release ~2023; "retiarii no longer maintained." Heavyweight AutoML — against "minimal effort." `[Community]` |
| **Neural Magic SparseML / DeepSparse** | unstructured + sparse CPU runtime | **DEAD** | Red Hat acq. Jan 2025; community versions deprecated **2 Jun 2025**, repos archived 3 Jun 2025. Was *the* way to cash unstructured sparsity on CPU; Ultralytics now redirects to OpenVINO/ONNX. `[Documented]` |

### Pitfalls specific to YOLO
- **Concat / C2f coupling:** removing one output channel forces removing the matching
 input channels across residual adds, `Concat`s and `C2f` splits. Do it by hand → shape
 hell. DepGraph auto-traces the group; arXiv 2405.03715 is purpose-built for
 concatenation architectures (2× conv speedup, code released). `[Documented]`
- **DFL / Detect head is sensitive:** pin it (`ignored_layers=[head...]`). Pruning the
 head tanked rare-class recall in the Jetson run. `[Community]`
- **Half-precision checkpoints:** Ultralytics saves FP16 + `strip_optimizer`, so a pruned
 model validates differently than it fine-tunes; the TP example monkey-patches
 `train` / `save_model` / `final_eval` to full precision. `[Documented]`
- **Re-export + re-quantize:** pruned (odd) channel counts must be re-exported to
 ONNX/OpenVINO, and the **INT8 calibration cache from the dense model is useless** —
 pruning fights quantization, budget re-calibration. `[Community]`
- **Pruning-ratio cliff:** sweep per model; past ~0.45–0.60 small classes collapse
 *irrecoverably*. No universal ratio. `[Community]`
- **Speedup is hardware-shaped:** FLOPs↓ only helps compute-bound layers; profile the
 real target first (the same 9.4 GFLOPs model was 11.4 ms on Orin Nano, 4 ms on a 4070). `[Community]`

### Why this project is the rare "pruning could help" case — but still shouldn't bother
A COCO nano carries capacity for 80 classes of natural images; our task is 1–8 flat UI
classes on **one** phone → lots of redundant filters, so pruning *would* find slack.
But that slack is cheaper to reclaim by **distillation into / training a smaller head**
([[YOLO — Knowledge Distillation]]), **quantization** ([[YOLO — Knowledge Distillation]]), and simply
**not over-sizing the model** in the first place. Pruning only earns its keep once those
are done and the forward pass is proven to be the clock.

## Sources

- [Torch-Pruning / DepGraph (CVPR'23)](https://github.com/VainF/Torch-Pruning) + [yolov8 example README](https://github.com/VainF/Torch-Pruning/blob/master/examples/yolov8/readme.md) — structured pruning w/ dependency graph; YOLO half-precision & upgrade-breakage pitfalls
- [DepGraph paper (arXiv 2301.12900)](https://arxiv.org/abs/2301.12900) — structural coupling, "any structural pruning"
- [Structured channel pruning on a Jetson (dev.to, 2026)](https://dev.to/marcorinaldi_ai/structured-channel-pruning-got-our-detector-under-12ms-on-a-jetson-3m3j) — `[Community]` structured vs unstructured latency table, ratio cliff, head pinning
- [Aerial YOLOv8 struct-prune + distill (arXiv 2509.12918)](https://arxiv.org/abs/2509.12918) — `[Benchmark]` BN-scaling criterion, 73.5% params, AP50 −2.7%
- [Iterative Filter Pruning for Concatenation CNNs (arXiv 2405.03715)](https://arxiv.org/html/2405.03715v1) — `[Documented]` Concat dependency handling, 2× conv speedup
- [YOLOv8-PSN: DepGraph vs LAMP vs Taylor (MDPI 16/15/3055)](https://www.mdpi.com/2075-5309/16/15/3055) — `[Benchmark]` criterion comparison
- [YOLOv8n-ALM layer-adaptive pruning (MDPI 14/21/4149)](https://www.mdpi.com/2079-9292/14/21/4149) — `[Benchmark]` nano pruned −65% params, +2.2% mAP (redesign+retrain)
- [OpenVINO NNCF Filter Pruning docs](https://docs.openvino.ai/2025/openvino-workflow/model-optimization-guide/compressing-models-during-training/filter-pruning.html) — maintained training-time structured pruning
- [Ultralytics: "Does Ultralytics support model Pruning?"](https://community.ultralytics.com/t/does-ultralytics-support-model-pruning/1680) · [YOLOv11n Pruning workflow](https://community.ultralytics.com/t/yolov11n-pruning/1816) — no native support; prune→fine-tune→re-export loop
- [Neural Magic deprecation notice (Ultralytics)](https://docs.ultralytics.com/integrations/neural-magic/) · [sparseml README](https://github.com/neuralmagic/sparseml) — SparseML/DeepSparse dead (Jun 2025)
- [microsoft/nni releases](https://github.com/microsoft/nni/releases) — stale maintenance
- Classic criteria: Li et al. 2017 *Pruning Filters for Efficient ConvNets* (L1) · Liu et al. 2017 *Network Slimming* (BN-γ) · Blalock et al. 2020 *What is the State of Neural Network Pruning?*

## Open questions / follow-ups

- Measure the actual nano forward-pass share of the closed-loop budget on the chosen
 host (Mac MPS / CPU / RTX 3060). If it's <10% of loop time, pruning is permanently off
 the table. → candidate row in `questions.md`.
- Does our deploy path go through **OpenVINO** on CPU? If yes, NNCF filter-pruning +
 INT8 in one pipeline may be lower-overhead than Torch-Pruning + separate quantization. → ties to [[YOLO — Quantization]].
- If model capacity ever becomes the issue, prefer **distillation** ([[YOLO — Knowledge Distillation]])
 over pruning for a fixed-architecture nano — compare both before committing.

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — YOLO]]
