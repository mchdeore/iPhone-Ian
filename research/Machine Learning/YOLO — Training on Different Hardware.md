---
domain: [ml]
type: research
status: answered
author: marc
date: 2026-10-05
tags: [yolo, training, cpu, mps, gpu, colab]
related:
  - "[[== MACHINE LEARNING ==]]"
---

# 04 — Training YOLO on different hardware

Companion to (which **ranks and prices** hardware). This note is the
operational **how**: exact Ultralytics args per device, RAM/VRAM budgets, measured
epoch times, and a verdict on the user's question — **is a CPU-only, ≤16 GB box a
viable training server?**

As of 2026-10, the current line is **YOLO26** (released Jan 2026: NMS-free head, DFL
removed, MuSGD optimizer; YOLO27 is waitlist-only). All training args below are
**identical across YOLOv8 / YOLO11 / YOLO26** — swap only the weight name
(`yolo26n.pt` ↔ `yolo11n.pt`). markaicode notes YOLO11 is still "officially
recommended for stable production." `[Documented]`

Tags: `[Documented]` official docs/`default.yaml` · `[Benchmark]` measured · `[Community]` forum/anecdotal.

## The args that actually move memory & speed

All defaults verified against `ultralytics/cfg/default.yaml` (main). `[Documented]`

| Arg | Default | What it does / when to change |
|---|---|---|
| `device` | auto | `0` CUDA · `[0,1]` multi-GPU · `-1`/`[-1,-1]` idle-GPU auto · `'cpu'` · `'mps'` · `'xpu:0'` Intel · `'npu:0'` Ascend. Auto = GPU0 if present else CPU |
| `batch` | `16` | int, **`-1`=AutoBatch (~60 % VRAM)**, or float `0.0–1.0` = VRAM fraction (`0.70`). AutoBatch is CUDA/NPU single-device only |
| `imgsz` | `640` | **Biggest memory/speed lever**: activation mem ∝ `imgsz²` (640→320 ≈ ¼ cost). Train+infer same size |
| `amp` | `True` | FP16 mixed precision; also `'bf16'`, `'fp32'`. Real speedup only on CUDA Tensor Cores; **no-op on CPU** |
| `cache` | `False` | `True`/`'ram'` or `'disk'` — caches decoded images to kill the dataloader bottleneck |
| `workers` | `8` | Dataloader procs (per-RANK in DDP). Fewer on low-RAM/CPU to avoid oversubscription |
| `nbs` | `64` | Nominal batch for **auto gradient accumulation** (`accumulate = nbs/batch`). No separate `accumulate` flag |
| `rect` | `False` | Rectangular batching — less letterbox padding ⇒ cheaper on a **tall phone-screen crop** |
| `multi_scale` | `0.0` | Random-scales imgsz each step; costs mem — leave off on tight hardware |
| `deterministic` | `True` | Reproducible but slower; **`False` speeds up** |
| `compile` | `False` | `torch.compile` (inductor); can speed CUDA/CPU after warm-up |
| `channels_last` | auto | Auto on non-Windows CUDA + x86; memory-format speedup |
| `time` | — | **Max training hours, overrides `epochs`** — cap a run to fit a Colab/overnight window |

**Batch modes & OOM safety net** `[Documented]`: fixed int · `-1` (60 % mem) ·
fraction (`0.70`). On a **first-epoch** CUDA OOM the trainer auto-halves batch and
retries ×3 (single-GPU only, **not DDP**). Validation runs at **2× train batch** — a
common late-stage OOM; drop `batch` or `val=False` for exploratory runs.

## Per-device playbook

Times are for **nano, ~1–5 k images @640** (our Phase 0 is smaller — see ); ranges swing 2–3× with dataset/`imgsz`/`workers`.

| Device | Launch args | Budget | Est. s–min/epoch | Verdict |
|---|---|---|---|---|
| **x86 CPU, 16 GB** | `device=cpu imgsz=640 batch=16 cache=disk workers=6 deterministic=False rect=True` | proc ~3–5 GB; `cache='ram'` adds ~1.2 MB/img (5 k≈6 GB → use `disk`) | **~2–7 min** (300–800 img); ~10–40 min (2–5 k). `imgsz=320` ≈ 4× faster `[Community]` | **Overnight-only.** Viable for Phase 0; too slow to iterate |
| **Apple Silicon MPS** | `device=mps batch=8–16 imgsz=640 cache=ram` | unified RAM shared CPU/GPU | ~2–15 min; measured **~1/6 of an NVIDIA GPU** (M4 vs RTX A2000) `[Community]` | Works but immature; **sometimes slower than CPU** at small batch; verify mAP≠0 after epoch 1 |
| **NVIDIA 4–8 GB** (2060/3050/3060) | `device=0 batch=-1 imgsz=640 amp=True` (OOM → `batch=4 imgsz=320`) | nano/small fit **4–6 GB @640** w/ AMP | ~15–45 s | **Best cheap path.** Needs Tensor Cores (RTX 20xx+) for AMP |
| **Colab free (T4 16 GB)** | `device=0 batch=-1 imgsz=640 cache=ram time=11` | 16 GB VRAM; ~12 h session, idle disconnects `[Community]` | ~20–90 s | **Recommended $0 path** |
| **Kaggle free (P100 / T4×2)** | `device=0` (or `[0,1]` T4×2 on Linux) `cache=ram` | **30 GPU-h/week**, ~9–12 h session `[Community]` | ~20–90 s | Equal to Colab; more weekly quota |
| **Raspberry Pi 4/5** | — | 4–16 GB LPDDR, no CUDA | — | **Inference only.** Ultralytics Pi guide is deploy/NCNN; training would run on CPU but is impractical `[Documented]` |

### CPU thread tuning `[Community]`
- PyTorch defaults to **all physical cores** for intra-op (OpenMP) math. Don't set
 `OMP_NUM_THREADS=1` (cripples it); leave unset or `= physical cores`.
- Beware **oversubscription**: `workers` (dataloader procs) × OpenMP threads can
 exceed cores and thrash. On an 8-core box, ~`workers=4–6` + default threads is a
 safe start; benchmark 1 epoch each way.
- `torch.set_num_threads(n)` / `set_num_interop_threads(n)` for fine control.
- CPU wins: `rect=True` (less padding), `deterministic=False`, `imgsz=320`,
 `cache='disk'` (RAM-safe), nano model, `amp` gives nothing (expect FP32; `'bf16'`
 autocast only helps on very recent AVX-512-BF16/AMX CPUs).

### NVIDIA low-VRAM extras `[Documented]`/`[Community]` (markaicode, Jun 2026)
- Order of levers: **`imgsz=320` first** (∝²), then `batch=-1`/`4`, keep `amp=True`.
- Long-run creeping OOM/fragmentation → `export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
- No user `accumulate` arg — tune via `batch`/`nbs`.

## Verdict — is a 16 GB CPU-only box a viable training server?

**Qualified yes, as an always-on fallback — not as the iteration machine.** `[Community]`/reasoning

- **Phase 0** (1 class, 300–800 auto-labeled frames, `yolo26n`, `imgsz=640`,
 `epochs=100 patience=20`): est. **~2–7 min/epoch ⇒ a few hours**, i.e. a clean
 overnight run. 16 GB is enough if you use **`cache='disk'`** (not `'ram'`) and
 modest `workers`; the process itself is only ~3–5 GB.
- **Where it breaks:** fast flash→train→evaluate iteration (minutes matter), and
 **Phase 1 scaling** toward Ultralytics' 1,500 img / 10 k inst per class across
 5–8 classes — that's many hours to days per CPU run.
- **Lazy call:** keep the CPU box as the always-available retrain/cron server, but
 push anything time-sensitive or multi-class to **free Colab/Kaggle T4** (≈10–40×
 faster), then a used **RTX 3060 12 GB** when HomeLab lands (per ).
 Use `time=<hours>` to fit CPU/Colab runs into a window. `ponytail:` the CPU box is
 the "it'll finish by morning" tier; the GPU is the "iterate" tier.

### Windows / remote-training note
If the CPU/Windows box is also the training host: **multi-GPU DDP is broken on
Windows** with official PyTorch wheels `torch≥2.4` (libuv `TCPStore`) — use a single
`device=0`, or **WSL2/Linux**, for >1 GPU. `[Documented]` For the "expose a public
port" plan, **do not expose the training/host process directly** — bind to
`127.0.0.1` and reach it over SSH/Tailscale/an authenticated reverse proxy;
a raw public port on a training/control box is an unauthenticated-RCE risk.

## Key takeaways
- `imgsz` (∝²) is the master memory/speed knob; `batch=-1` auto-sizes VRAM; OOM auto-retry only saves you once, in epoch 1, single-GPU.
- Low-VRAM NVIDIA (4–8 GB) trains nano/small fine @640 with AMP — the best cheap tier.
- MPS works but runs ~⅙ of NVIDIA, can trail CPU at small batch, and has a zero-mAP history → sanity-check epoch 1.
- Raspberry Pi is deploy-only; it will not meaningfully train.
- 16 GB CPU box = **overnight Phase-0 server**, not an iteration machine; `cache='disk'`, `workers=4–6`, `rect=True`, `deterministic=False`, cap with `time=`.
- Free Colab/Kaggle T4 remains the zero-cost fast path (watch session/quota limits).

## Sources
- https://docs.ultralytics.com/modes/train — device syntax, batch modes, MPS, Windows DDP `[Documented]`
- https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/default.yaml — arg defaults `[Documented]`
- https://docs.ultralytics.com/compare/yolo26-vs-yolo11 — YOLO26 current (Jan 2026) `[Documented]`
- https://docs.ultralytics.com/guides/yolo26-training-recipe — MuSGD, 640, batch 128 recipe `[Documented]`
- https://markaicode.com/errors/yolov11-common-errors-and-fixes/ — 8 GB fix: batch 4 / −1, imgsz 320, amp, nbs, expandable_segments `[Community]`
- https://docs.ultralytics.com/guides/raspberry-pi — Pi = inference/NCNN deploy, no training `[Documented]`
- https://github.com/ultralytics/ultralytics/issues/22778 — MPS ~1/6 of NVIDIA (M4 vs RTX A2000) `[Community]`
- https://github.com/ultralytics/yolov5/issues/11589 — MPS slower than CPU at small batch `[Community]`
- https://github.com/pytorch/pytorch/issues/109457 — MPS poor training results vs CPU/CUDA `[Community]`
- https://pytorch.org/tutorials/recipes/recipes/tuning_guide — DataLoader workers, OMP_NUM_THREADS `[Documented]`
- https://agneya.medium.com/how-to-train-a-custom-yolo-model-for-free-d189178f1c66 — Kaggle 30 GPU-h/week P100/T4 `[Community]`
- https://electronics.alibaba.com/question/free-gpu-access-in-2026-real-options-limits — Colab/Kaggle free-tier limits 2026 `[Community]`

## Open questions / follow-ups
- Actual CPU epoch time on the specific 16 GB target box? → benchmark 1 epoch of the real Phase-0 set at `imgsz` 320 vs 640 before committing to it as the server.
- Does `cache='ram'` + many `workers` still OOM/hang (hist. Ultralytics #1010)? Confirm on 16 GB; prefer `cache='disk'` until verified.
- Does `compile=True` net-help a CPU nano run after warm-up, or does compile overhead eat a short-run's budget?
- Cropping to screen (per ) shrinks images — re-estimate CPU time and whether `cache='ram'` then fits 16 GB.
