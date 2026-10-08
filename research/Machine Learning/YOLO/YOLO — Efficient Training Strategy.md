---
type: research
status: answered
author: marc
date: 2026-10-05
tags: [machine-learning, yolo, training, strategy, computer-vision]
---

# 12 — Quickest-to-train, minimal-overhead training strategy

Scope: the **end-to-end workflow** from flash-app captures to a usable `best.pt` with
the least effort and compute. Builds on `01` (dataset size, augs, epochs), `02`
(synthetic/flash app, synth:real ratio), `03`/`04` (hardware). Does **not** re-derive
those knobs — focuses on *strategy, model choice, re-training, and wall-clock*.

Tags: `[Documented]` docs/papers · `[Benchmark]` measured · `[Community]` forum/anecdote.

## Question

What is the fastest, lowest-overhead way to train (and re-train) the detector given a
CPU-only 16 GB box and/or free cloud GPUs?

## Bottom line (the lazy path)

1. Start from COCO **`yolo11n.pt`** — not a UI-pretrained model (reasons below).
2. **Crop to screen, `imgsz=640`, `cache=ram`, `batch=-1`, `patience≈20`.**
3. Try freezing the backbone (**`freeze=11`** on YOLO11) first; unfreeze if real-val mAP lags.
4. **One pooled run** (mostly synthetic + 5–20 % real) — *not* a two-stage curriculum.
5. **Train on free Colab/Kaggle T4** (~1 h); keep the 16 GB CPU box as an overnight fallback.
6. As data grows, **retrain from `yolo11n.pt` on the whole pool** — never fine-tune on only-new frames.

## Transfer learning — COCO nano vs a UI-pretrained model

Open UI-element YOLO weights **do exist** and most load straight into Ultralytics:

| Model | Base / size | License | Classes | Note |
|---|---|---|---|---|
| COCO **`yolo11n.pt`** | YOLO11-**n** | AGPL-3.0 | 80 generic | Ultralytics default `[Documented]` |
| OmniParser **`icon_detect`** | YOLOv8, **~6 MB (nano/small)** | AGPL-3.0 | 1 (interactable region) | Ultralytics-loadable `[Documented]`/`[Community]` |
| OmniParser **`icon_detect_v3`** | YOLOv9-**E** (large) | **MIT** | 1 (interactable) | TorchScript, torch-only, *not* Ultralytics `[Documented]` |
| **ScreenParser** (IBM/ETH) | YOLO11-**L**, 1280px | **Apache-2.0** | 55 web-UI | web-trained → **warns of mobile/native drift** `[Documented]` |
| Salesforce **GPA-GUI-Detector** | YOLO (OmniParser lineage) | check repo | icons/buttons | fine-tuned from OmniParser `[Community]` |

Why **COCO nano is the minimal-effort default**:
- Zero sourcing/conversion overhead; smallest to train; the whole pipeline assumes it.
- The *big* UI models (ScreenParser YOLO11-L, `icon_detect_v3` YOLOv9-E) are **too heavy to fine-tune** on a 16 GB CPU / low-VRAM box, and ScreenParser explicitly drifts on mobile/native, so you'd retrain the head anyway — the "head start" mostly evaporates.
- License is a non-issue for us: `icon_detect` is AGPL-3.0, but **so is the Ultralytics stack we already run** `yolo11n.pt` on, so AGPL adds no new obligation for private, non-distributed research (not legal advice).

The two moves that *are* worth it:
- **One cheap A/B for Phase 0:** OmniParser **`icon_detect`** is small *and* its single "interactable region" class ≈ our `tap_target`. Fine-tune it alongside `yolo11n.pt` and keep whichever wins on real-iOS val — low effort, Ultralytics-loadable. `[Community]`
- **Use the big UI models as zero-shot pre-labelers**, never as training weights: run ScreenParser / `icon_detect` over the small real-iOS set that the flash app can't auto-label (`02`'s 5–20 % real), then *review* its boxes instead of drawing from scratch. It never touches the training graph, so size/license don't matter. `ponytail:` borrow its predictions, not its weights.

## The knobs that actually move wall-clock

- **Freeze the backbone.** `freeze=10` is the YOLOv5/v8 convention (SPPF = layer #9). **YOLO11 adds a C2PSA block, so its backbone ends at index 10 → use `freeze=11` to freeze the whole backbone** (`freeze=10` leaves C2PSA trainable); verify by printing `model.model`. `[Documented]` A 2025 study (Mathematics 13(15):2539 / arXiv 2509.05490) across YOLOv8/v10: freezing cuts **GPU memory up to 28 %** and *sometimes beats* full fine-tuning mAP@50 — "no universal optimum; it depends on the data." `[Benchmark]` Good default on a small box; if real-val mAP lags, unfreeze (flat UI is off-domain for COCO textures, so the backbone may need to adapt).
- **`imgsz` — resolves the `README` tension** (01 wanted 960–1280, 03 timed 640): compute scales ≈ `imgsz²`, so **1280 ≈ 4× slower than 640**. **Stay at 640 + crop-to-screen**; raise `imgsz` only for genuinely tiny icons *and* only on GPU. `[Documented]`
- **Schedule / early stop** — see `01` (100–300 epochs, `patience` 20–50). The lever: **let early stopping decide** — set `epochs=150 patience=20` and walk away.
- **`cache=ram`** — biggest CPU win (kills repeat JPEG decode, the usual CPU bottleneck, `03`). **16 GB caveat:** cached uint8 @640 ≈ ~1.2 MB/img → ~4–5k images fit; `imgsz=1280` (~5 MB/img) or larger sets OOM → use `cache=disk`. `[Community]`

## Curriculum and re-training

- **Synthetic→real curriculum?** `02` already shows synthetic + 5–20 % real is the sweet spot and ≥1:1 synth:real *hurts*. For minimal overhead do a **single pooled run** at that ratio, not an explicit two-stage warm-up/fine-tune. `ponytail:` skip the two-stage machinery (ceiling: a model that overfits synthetic style) until a pooled model demonstrably underperforms on real-iOS val — only then warm up on synthetic and fine-tune on real at low `lr0`.
- **Incremental vs from-scratch.** Naïve "fine-tune on only the new frames" causes **catastrophic forgetting** of earlier conditions. `[Documented]` Retraining on the **accumulated** pool avoids it, and fine-tuning from pretrained converges in **<10 % of from-scratch time**. `[Documented]`/`[Benchmark]` So each cycle: add new hard frames → **retrain `yolo11n.pt` on the full pool** (cheap — minutes on T4). Don't build an online-learning pipeline. `resume=True` is for crash-recovery of the *same* run, never for adding data.

## How many images for "usable" (~10 UI classes)

"Usable" ≈ mAP50 ~0.7–0.8 on **real-iOS** val. `01`'s targets (≥1,500 img/class, ≥10k
instances/class; a few hundred instances/class to start) hold; the flash app's **3–8
targets/frame** reaches instance counts fast:

| Stage | Auto-labeled frames | + real-iOS | Instances | Expect |
|---|---|---|---|---|
| Phase 0 (1 class) | 300–800 | 50–100 | 2–6k | prove the loop |
| Phase 1 (~10 classes) | 3–5k | 300–500 | 15–40k | usable mAP |
| Diminishing returns | ~15k (1.5k/class) | ~1–2k | ~100k+ | only new *conditions* help (`01`) |

## Wall-clock — 16 GB CPU box vs free Colab T4

YOLO11n, ~3k images @640, `cache=ram`, `patience=20` (estimates; swing 2–3× with cores/loader):

| | per epoch | full run (~50–100 eff. epochs) | iterate? |
|---|---|---|---|
| **16 GB CPU (8-core)** | ~15–30 min `[Community]` | **~10–20 h (overnight)** | painful |
| **Free Colab T4 16 GB** | ~30–60 s `[Documented]` | **~0.5–1.5 h** | easy, many/day |

Headline: **the T4 is ~10–20× faster** — treat the CPU box as "kick it off before bed,"
not the iteration loop. Free limits (2026): **Colab T4 ~15–30 GPU-h/wk, 12 h session,
~90 min idle disconnect**; **Kaggle 30 h/wk, P100 or 2×T4 (32 GB)**, better for
unattended jobs. `[Community]` A ~1 h nano run fits trivially in either.

**Data movement (no public port needed).** Training is decoupled from capture: the
dataset is a **portable zip artifact**. Capture + auto-label on the Mac/rig → zip →
upload to Colab/Kaggle (or `scp` to the GPU box) → download `best.pt`. The Windows
"public port" question is only about *hosting the flash app*, never training — and if
you must expose it, use a tunnel (Cloudflare Tunnel / ngrok), not a raw router port.

## Step-by-step plan (commands + est. hours)

Assumes `01`/`02` dataset conventions (crop-to-screen, split-by-session, `flash.yaml`).

1. **Env** (Colab/Kaggle or local): `pip install ultralytics` — **0.1 h**.
2. **Phase 0 smoke test** (1 class, ~500 frames) — **0.5 h prep + ~0.5–1 h train on T4**:
  ```bash
  yolo detect train model=yolo11n.pt data=flash.yaml imgsz=640 epochs=100 \
   patience=20 batch=-1 cache=ram freeze=11 \
   fliplr=0 flipud=0 degrees=0 mosaic=0.3 close_mosaic=10 \
   perspective=0.0005 translate=0.1 scale=0.3
  ```
  Gate: on **real-iOS** val, `mAP50 > 0` and boxes land on targets. (Watch the MPS zero-mAP bug, `03`.)
3. **If backbone-frozen mAP lags**, re-run without `freeze` (full fine-tune) — **~1 h**. Optional A/B: same command with `model=icon_detect/model.pt`.
4. **Phase 1** (~10 classes, pooled synthetic + 5–20 % real), same command + new `data=` — **~1 h train**. Keep `fliplr=0` permanently (`01`).
5. **Validate + mine hard frames**: `yolo val model=runs/detect/train/weights/best.pt data=flash.yaml`; keep frames with low conf / failed taps (the tap score, `01`) and add to the pool.
6. **Retrain from `yolo11n.pt` on the grown pool** (not incrementally). Repeat 4–6 as data arrives — **~1 h/cycle on T4**.
7. **Export** for the agent host: `yolo export model=best.pt format=onnx` (CPU inference) — **0.2 h**.

First usable ~10-class model end-to-end: **~1 day wall-clock, <~4 h hands-on** — most of it capture, not compute.

## What NOT to do

- Don't **train from scratch** (`model=yolo11n.yaml`) — pretrained converges ~10× faster. `[Documented]`
- Don't **fine-tune incrementally on only-new frames** — catastrophic forgetting; retrain on the pool. `[Documented]`
- Don't **adopt ScreenParser / `icon_detect_v3` as the training base** — Large/Extended and off-domain for iOS; use them only as zero-shot pre-labelers.
- Don't **jump to `yolo11s/m/l` or `imgsz=1280`** before nano@640 is proven — 4×+ slower on CPU for usually-marginal gain (`01`,`03`).
- Don't **`cache=ram` a 1280px or >5k-image set on the 16 GB box** — it OOMs; use `cache=disk`.
- Don't **leave `fliplr=0.5`** (default) — it mirrors chevrons/text ("‹ Back" → "Back ›"), `01`.
- Don't **iterate on CPU** — kick off overnight runs there, iterate on the free T4.
- Don't **expose a raw public port from Windows for training** — training needs no inbound service; move a zip. Tunnel the flash app if anything.
- Don't **`resume=True` to add data** — that's crash-recovery of the same run, not new data.
- Don't **chase mAP past the real-val plateau** — more frames help only when they add new lighting / angle / glare (`01`).

## Sources

- https://huggingface.co/microsoft/OmniParser-v2.0 — `icon_detect` = YOLOv8/AGPL-3.0; new `icon_detect_v3` = YOLOv9-E/MIT (TorchScript) `[Documented]`
- https://github.com/b4rtaz/html2llm — OmniParser icon detection ≈ 6.1 MB weights (nano/small scale) `[Community]`
- https://huggingface.co/docling-project/ScreenParser — YOLO11-L, Apache-2.0, 55 web-UI classes @1280, mobile-drift caveat `[Documented]`
- https://huggingface.co/Salesforce/GPA-GUI-Detector — YOLO UI detector from the OmniParser lineage `[Community]`
- https://arxiv.org/abs/2509.05490 (Mathematics 2025, 13(15):2539) — layer-freezing: −28 % memory, sometimes > full-FT mAP `[Benchmark]`
- https://docs.ultralytics.com/yolov5/tutorials/transfer_learning_with_frozen_layers/ — freezing = less compute/time, slight accuracy trade `[Documented]`
- https://community.ultralytics.com/t/guidance-on-freezing-layers-for-yolov8x-seg-transfer-learning/189 — SPPF is #9 → `freeze=10` freezes the YOLOv8 backbone `[Documented]`
- https://arxiv.org/html/2410.17725 — YOLO11 adds C2PSA after SPPF (backbone boundary shifts by one) `[Documented]`
- https://docs.ultralytics.com/guides/finetuning-guide/ — fine-tune converges in a fraction of from-scratch time `[Documented]`
- https://arxiv.org/html/2503.04688v1 — catastrophic forgetting in incremental object detection `[Documented]`
- https://research.aimultiple.com/gpu-cluster · https://www.spheron.network/blog/google-colab-alternatives-8-gpu-clouds-compared-2026/ — 2026 free-tier T4 / Kaggle limits `[Community]`

## Open questions / follow-ups

- Does freezing the backbone actually help on *flat UI* (COCO textures are off-domain), or is full fine-tune always better here? Measure on real-iOS val. → `questions.md`
- Real CPU epoch time on the specific 16 GB box @640 with `cache=ram` — benchmark once (~15–30 min/epoch is an estimate).
- Is ScreenParser / `icon_detect` good enough as a **zero-shot pre-labeler on iOS** to reduce real-set labeling to a review step? Quick spike.
- Minimum real-iOS frames for mAP50 ≥ 0.8 at ~10 classes — the table is an estimate; pin empirically.
