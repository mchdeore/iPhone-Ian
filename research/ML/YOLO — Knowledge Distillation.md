---
tags: [YOLO, distillation, knowledge-distillation, ML, computer-vision, CPU, edge]
status: answered
date: 2026-10-05
related:
  - "[[ML Central]]"
---

# 10 — Knowledge distillation on low-VRAM / CPU-only hardware

## Question

Should iPhone-Ian use knowledge distillation (KD) to get a better nano detector,
given training may run CPU-only on ≤16 GB RAM and minimal overhead is the priority?

Builds on `03-hardware.md` (CPU ≈ 10–40 min/epoch; free Colab T4 is the real path)
and the fact that the flash app (`02`) already produces perfect, abundant labels.
Tags: `[Documented]` docs/papers · `[Benchmark]` measured · `[Community]` forum/anecdotal.

## TL;DR decision

- **Classic feature/logit KD on the CPU box: skip it.** It co-resides teacher+student
 and adds a teacher forward *every batch* — pure cost on already-bottlenecked hardware,
 for ~0.5–1.0 mAP. `[Benchmark]`
- **The useful "distillation" here is offline pseudo-labeling**: a big model/VLM labels
 what the flash app can't (real iOS screens, named UI classes); train a nano student
 normally. Teacher runs **once, offline**, never co-resident → fits 16 GB CPU. Recommended.
- **Want true KD cheaply?** Ultralytics now does it in one arg (`distill_model=`) — but
 run it on the free Colab GPU, not the CPU box.

## Part 1 — Detection KD methods (what the literature offers)

Response/logit KD underperforms for detection *localization*; feature imitation and
localization-aware variants dominate. `[Documented]`

| Method | Idea | Note for us |
|---|---|---|
| **Logit / response KD** (Hinton) | Student mimics teacher's soft class probs (temperature) | Weak alone for boxes; but **precomputable offline** (see Part 3) |
| **Feature imitation / Mimic** (Li 2017; **FGFI** Wang CVPR'19) | Match teacher feature maps **near object regions**, not whole image | What Ultralytics' native KD is closest to |
| **LD — Localization Distillation** (Zheng CVPR'22) | Distill the box **distribution** (DFL), not just class | Less relevant to **YOLO26**, which *removes DFL* and is NMS-free `[Documented]` |
| **CWD — Channel-Wise** (Shu ICCV'21) | Softmax each channel → KL match per-channel activation maps | Strong, cheap, popular for dense prediction; many 2025–26 YOLO papers use it `[Benchmark]` |
| **FGD / MGD** (Yang CVPR/ECCV'22) | Focal+global / masked feature regeneration | Higher ceiling, more plumbing |

2025–26 YOLO-KD results are consistently **small single-digit mAP gains** (infrared
YOLOv8s→n **+1.18 mAP@50-95**, −7.9% params; a YOLO11n CWD variant **+2.92 mAP@50** on
tiny-object edge). `[Benchmark]` KD helps most for a *starved* student (few params, hard
small objects) — the small-icon regime (`01`) — but only once a good teacher exists.

## Part 2 — Tooling that actually works with Ultralytics YOLO in 2026

**Ultralytics now supports KD natively (new since ~mid-2026).** `[Documented]`

```python
from ultralytics import YOLO
YOLO("yolo26n.pt").train(data="flash.yaml", epochs=100, distill_model="yolo26s.pt")
```

- One arg (`distill_model`), plus `dis` (loss weight, default 6.0). Exported model is
 **student-only — zero inference overhead**. `[Documented]`
- **Method:** feature KD from the **three neck layers feeding the Detect head**; a
 projector (two 1×1 convs + ReLU) aligns student→teacher channels; **score-weighted
 L2**, weighted by the teacher's class confidence (i.e. FGFI-style, foreground-focused).
 Teacher is frozen/eval, forward-only; only student+projector backprop. `[Documented]`
- **Supported:** detect/segment/pose/obb (only **detect** verified). Teacher must be
 **same family** (YOLO11→YOLO11, YOLO26→YOLO26); **cross-family is blocked**. `[Documented]`
- **COCO gains (val mAP50-95):** n 40.9→**41.5**, s 48.6→**49.2**, m 53.1→**53.9**,
 l 55.0→**56.0**, x 57.5→**57.9**. Recommended pairs n←s, s←m, m←x, l←x. `[Benchmark]`

Other tooling:
- **Community forks** (manual pre-hook on `YOLO(...).model` + adapter) predate the native
 feature — now redundant. `[Community]`
- **Torch-Pruning** (VainF) — structural channel pruning for YOLOv8/11; **compression, not
 KD** (often paired with a KD fine-tune to recover mAP). `[Documented]`
- **NNCF / OpenVINO** — INT8 PTQ/QAT + filter pruning → fast **CPU** inference via
 Ultralytics' built-in OpenVINO export: the real CPU *deployment* win, orthogonal to KD.
 **mmrazor** has CWD/FGD but targets mmdetection, not Ultralytics — not worth porting. `[Documented]`

## Part 3 — Memory cost, and the offline trick

- **Co-resident cost:** KD needs **both** models in memory. The teacher is forward-only
 (no grads/optimizer) so it's cheaper than the student, but still adds a full forward
 per batch → **slower + more RAM**, scaling with the pair (n←s light, n←x not). For n/s
 @640 weights are tiny (<100 MB) and activations×batch dominate — fits 16 GB, but on CPU
 that extra forward is the cost, pushing `03`'s 10–40 min/epoch higher. `[Documented]`
- **Precompute teacher outputs offline → soft labels.** Works for **response/logit** KD:
 run the teacher once, cache per-image predictions, train with the teacher **absent from
 RAM**. Big saver. `[Community]`
- **Caveat:** *native feature* KD can't go offline — it matches dense neck features under
 **random per-epoch augmentation**, so caching = storing/re-augmenting full feature
 tensors per image → impractical. Offline = response/pseudo-label territory.
- **So the RAM-free "distillation" here = pseudo-labeling (Part 4):** teacher writes tiny
 `.txt` labels once; student trains as ordinary detection.

## Part 4 — The cheap alternative: pseudo-labeling (recommended)

A big model labels images once; a nano YOLO trains on those labels. Roboflow literally
brands this "YOLO distillation," via the open-source **autodistill** (base model →
target model; `autodistill-yolov11` plugin exists). `[Documented]`

Big labelers relevant to iPhone-Ian:
- **OmniParser v2** (Microsoft) — *is itself a YOLOv8* trained on UI screenshots; outputs
 bounding boxes for interactive elements (single "icon/clickable" class) + Florence-2
 captions. Runs fine on CPU for a one-time pass → ideal **class-agnostic "tappable
 region" labeler** for real iOS captures. `[Documented]`
- **Grounding DINO / OWLv2** — open-vocabulary, **text-prompted** detection → gives
 *named* boxes ("back button", "text field") for a real UI taxonomy the flash app can't
 synthesize cleanly. `[Documented]`
- **YOLO11x / YOLO26x** — only useful here if first trained on our own data (COCO classes
 don't include UI icons).
- **UGround** (`06`) outputs **points**, not boxes → weaker for box pseudo-labels; keep it
 for the agent's grounding, not for YOLO supervision.

Always **review/correct a sample** before training — VLMs miss, hallucinate, draw loose
boxes. `[Documented]` And per `specs/02…§9`: never run a labeler over frames with real secrets.

## Decision + minimum-overhead recipe (16 GB CPU-only box)

1. **Synthetic flash-target detector:** no KD. Train `yolo11n`/`yolo26n` normally on the
  flash-app labels (`01` recipe). The free, abundant, perfect labels already give what
  KD would approximate — distilling adds cost for ~0.5 mAP.
2. **Real iOS screens + UI vocabulary:** **pseudo-label offline**, not KD. Run OmniParser
  v2 (tappable regions) and/or Grounding DINO via `autodistill` (named classes) **once**
  — on Colab or an accepted slow CPU pass — write YOLO `.txt`, hand-check a sample, then
  train the nano student normally. Teacher never co-resident → fits 16 GB easily.
3. **Only if nano hits a real accuracy wall** (small icons still missed after `01`'s
  crop + higher `imgsz`): use Ultralytics' native `distill_model=` from a same-family
  `s`/`m` teacher — **but run it on the free Colab T4** (`03`), not the CPU box.
4. **CPU deployment speed** (perception on HomeLab): export **OpenVINO INT8** (NNCF);
  add Torch-Pruning only if latency still misses target. Separate from KD.

`ponytail:` the lazy win is pseudo-labels, not a teacher-in-RAM loop. Ceiling: a nano
can't beat its labeler on hard classes; upgrade path is the one-arg native KD on a GPU.

## Key takeaways

- YOLO-KD gains are small (≤~1–3 mAP) and need a pre-existing good teacher; Ultralytics'
 native `distill_model` is effortless but co-resident + teacher-forward/batch = wrong
 fit for a slow CPU box (run it on Colab).
- Feature KD can't be precomputed offline (augmentation); only response/pseudo-labels can.
- Pseudo-labeling (autodistill + OmniParser/Grounding DINO) is the RAM-free, minimal-
 overhead "distillation" that fits this project; use OpenVINO INT8 for CPU inference.

## Sources

- **Ultralytics native KD** — [guide](https://docs.ultralytics.com/guides/knowledge-distillation) (`distill_model`, method, COCO gains, same-family rule) `[Documented]/[Benchmark]`; [community pre-native thread](https://community.ultralytics.com/t/implementing-knowledge-distillation-with-yolo11n-student-and-yolo11m-teacher-in-ultralytics-trainer/1743/5) `[Community]`; [YOLO26 overview arXiv 2510.09653](https://arxiv.org/pdf/2510.09653v3) (DFL removed → LD less relevant) `[Documented]`
- **KD methods** — LD [2204.05957](https://arxiv.org/html/2204.05957v1)/[2102.12252](https://arxiv.org/html/2102.12252v4) · FGFI [1906.03609](https://arxiv.org/abs/1906.03609) · FGD [2111.11837](https://arxiv.org/html/2111.11837v2) · MGD/DMKD [2309.02719](https://arxiv.org/html/2309.02719v2) `[Documented]`
- **CWD / YOLO-KD benchmarks** — tiny-object YOLO11 [2609.30395](https://arxiv.org/html/2609.30395v1) · CWD+pruning YOLOv8 [2509.12918](https://www.arxiv.org/pdf/2509.12918) · infrared YOLOv8s→n +1.18 mAP [MDPI 25/13/4054](https://www.mdpi.com/1424-8220/25/13/4054) `[Benchmark]`
- **Pseudo-labeling** — [Roboflow YOLO Distillation](https://blog.roboflow.com/yolo-distillation/) · [autodistill-yolov11](https://github.com/autodistill/autodistill-yolov11) · [OmniParser v2 (YOLOv8 UI detector)](https://huggingface.co/microsoft/OmniParser-v2.0) · [Grounding DINO](https://github.com/idea-research/groundingdino) `[Documented]`
- **CPU compression** — [Torch-Pruning YOLOv8](https://github.com/VainF/Torch-Pruning/blob/master/examples/yolov8/readme.md) · [NNCF/OpenVINO filter pruning](https://docs.openvino.ai/2024/openvino-workflow/model-optimization-guide/compressing-models-during-training/filter-pruning.html) `[Documented]`

## Open questions / follow-ups

- Does OmniParser v2's "clickable" class transfer to **camera photos** of iOS, not clean screenshots? Likely a domain gap → may still need flash-app realism (`02`).
- Native KD on **CPU**: one-off bench the n←s @640 epoch-time multiplier vs plain to confirm "skip on CPU" → `questions.md` row.
- Is training a same-family teacher worth the GPU time when flash labels are free? Likely only for the hard-icon tail; revisit after Phase 1 mAP.
