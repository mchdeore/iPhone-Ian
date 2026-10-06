---
tags: [YOLO, optimization, inference, deployment, ML, computer-vision]
status: answered
date: 2026-10-05
related:
  - "[[YOLO — Efficient Dataset Recipe]]"
  - "[[YOLO — Efficient Dataset Recipe]]"
  - "[[YOLO — Synthetic Data and Flash Training App]]"
  - "[[YOLO — Training Hardware and Capture Rig]]"
---

# 08 — Other ways to optimize YOLO (variant, runtime, pipeline)

## Question

Besides quantization/pruning/distillation, how do we make the detector fast and
cheap for a **closed-loop tapper watching a mostly-static phone screen**, on
low-VRAM/CPU hardware, with minimal effort? Ranked by impact ÷ effort.

**Scope / no-duplication.** Crop-to-screen, `imgsz`, SAHI, model size (nano),
augments and pretrained/`freeze` already live in [[YOLO — Efficient Dataset Recipe]]; VRAM,
`cache='ram'`, workers in [[YOLO — Training Hardware and Capture Rig]]; the perception loop in
`specs/02-firmware-and-software.md` §7. This note adds **variant choice, export
runtimes, and the inference/camera pipeline**, and re-ranks the overlaps for the
*deployment* loop (notes 01/03 were about *training*).

Tags: `[Documented]` official docs/paper · `[Benchmark]` measured · `[Community]` forum/anecdote.

## Ranked: inference / deployment optimizations

**1. Don't infer every frame — event-driven + change detection. (impact HIGH, effort LOW)**
A phone UI is static between taps, so detecting every camera frame is almost pure
waste. Run YOLO only (a) when the agent needs to perceive before/after an action,
and (b) when the warped screen ROI actually changed — `cv2.absdiff` on the
homography-rectified screen crop, threshold the changed-pixel count. This can cut
inference calls **10–100×** for free. For a plain video source Ultralytics exposes
`vid_stride=N` (infer every Nth frame) and `stream=True` (lazy, memory-efficient
generator) as the lightweight version of the same idea. `[Documented]/[Community]`
This is the top lever for *this* use case and beats per-frame tracking (ByteTrack),
which only helps when objects move — ours don't.

**2. Crop to the screen ROI via the homography we already have. (impact HIGH, effort LOW)**
The flash-app/calibration already gives `H` (CSS→camera, [[YOLO — Synthetic Data and Flash Training App]]).
Warp + crop to just the phone rectangle before inference: fewer input pixels → faster,
*and* icons get bigger → better accuracy (the small-object win already argued in
[[YOLO — Efficient Dataset Recipe]]). Double duty, near-zero effort because `H` exists. Do this
at train **and** infer time so the distributions match.

**3. Export to the host's native runtime. (impact HIGH on CPU, effort LOW)**
One `model.export()` call, large payoff — especially since training/deploy may be
**CPU-only** (user constraint):
- **OpenVINO** on Intel CPU: **up to 3× speedup** vs PyTorch (AVX-512/AMX kernels). `[Documented]`
- **NCNN**: best on **ARM** (Pi/phone-class SoCs). `[Documented]`
- **ONNX Runtime**: solid, portable baseline, faster than raw PyTorch on CPU. `[Documented]`
- **TensorRT**: fastest on **NVIDIA** (FP16/INT8); **CoreML** for Apple Silicon/ANE.
Pick by the box you actually deploy on; on a Windows/Intel mini-PC that's OpenVINO.

**4. Model variant: prefer YOLO26n (NMS-free, DFL-free, STAL). (impact MED-HIGH, effort LOW)**
YOLO26 (Ultralytics, Jan 2026) is the edge-first successor to the YOLO11n baseline
in [[YOLO — Efficient Dataset Recipe]]. For us it hits three constraints at once: **up to 43%
faster CPU ONNX inference than YOLO11n** (Intel Xeon), **native end-to-end NMS-free**
inference (`nms=False` → one box per object, no NMS conf/iou tuning, lower and more
*predictable* latency, simpler ONNX/TensorRT export), DFL removed (lighter head), and
**STAL** (Small-Target-Aware Label Assignment) which directly targets the tiny-UI-icon
problem flagged in note 01. `[Documented]` Swap `yolo11n.pt`→`yolo26n.pt`. Keep
YOLO11n as the mature fallback if a YOLO26 export path misbehaves.

**5. Rectangular `imgsz` matched to the crop. (impact MED, effort LOW)**
A portrait phone crop square-padded into 640² wastes ~40–60% of pixels on gray bars.
Pass a rectangular size (e.g. `imgsz=[640,384]`) / `rect=True`, which pads only to the
short-side 32-multiple → less compute per frame. `[Documented]/[Community]` Train and
infer at the **same** rectangular size.

**6. Camera-pipeline latency, not just model latency. (impact MED-HIGH, effort MED)**
Closed-loop lag is often a **stale capture buffer**, not inference. Fixes:
- `cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)` — but it's **backend-specific and often
  ignored** (V4L support only since 2018; may return `False`). `[Community]`
- Robust fix: a **grabber thread** that keeps only the newest frame and drops the rest,
  so the loop always reads "now." `[Community]`
- Force **MJPG** FOURCC (`CAP_PROP_FOURCC`) so a USB2 webcam delivers compressed 1080p30
  instead of starving on raw YUY2 (~5 fps). `[Community]`
- Lock focus/exposure (already in [[YOLO — Training Hardware and Capture Rig]]) — AF/AE hunting adds latency too.

**7. Lower `imgsz` after cropping. (impact MED, effort LOW)**
Because the crop (#2) already enlarges icons, you can often drop `imgsz` 640→512/416
with little accuracy loss and ~1.5–2× speed. Cost scales ~`imgsz²` (note 03). Tune
against real iOS validation captures.

**8. Layer fusion. (impact LOW but FREE, effort ZERO)**
Ultralytics fuses Conv+BatchNorm at inference automatically (`model.fuse()`, logs
"Fusing layers…"). Already on; just don't disable it. `[Documented]`

**9. Threaded / async loop. (impact MED, effort MED)**
Decouple capture → inference → GRBL motion onto separate threads so camera I/O and
serial waits overlap compute. Helps loop latency more than raw throughput.

**10. Batching & FP16 — mostly N/A here. (impact LOW, effort LOW)**
A single live camera is `batch=1`, so **batching gives nothing** for the live loop
(only useful for offline eval/relabel passes). `half=True` (FP16) helps on GPU/TensorRT,
not CPU. Listed to say: skip them for the realtime path.

## Variant comparison (why not RT-DETR)

| Model | NMS-free | CPU/low-VRAM fit | Notes |
|---|---|---|---|
| **YOLO26n** ⭐ | **Native** (`nms=False`) | **Best** | DFL-free, STAL for small icons, ~43% faster CPU ONNX vs 11n `[Documented]` |
| YOLO11n | No (NMS) | Good | Mature fallback; current recipe in note 01 |
| YOLOv10n | Yes (dual-assign, 2024) | Good | Superseded by YOLO26's native end-to-end for Ultralytics users `[Documented]` |
| RT-DETR | Yes (by design) | **Poor** | Transformer, heavier + data-hungry, GPU-oriented — wrong tool for CPU/minimal-effort `[Documented]` |

## Training-side speedups (CPU-only, ≤16 GB RAM)

Builds on [[YOLO — Efficient Dataset Recipe]] / [[YOLO — Training Hardware and Capture Rig]]; prioritized for a weak box:
- **`cache='ram'`** (note 03) — biggest dataloader win; if RAM is tight at 16 GB use
  `cache='disk'`. `[Documented]`
- **`rect=True`** training — fewer padded pixels per batch → faster epochs on portrait
  crops (slight accuracy caveat historically, fine for fixed-aspect data). `[Community]`
- **`freeze=10`** (freeze backbone) — fewer grads → faster epochs and less overfit on a
  small synthetic set (note 01 raised freeze as optional; on a CPU it's worth it). `[Documented]`
- **Smaller `imgsz` first, then fine-tune** at target size — cheap early epochs, polish late.
- **`patience=20–50`** early-stop (note 01) + `epochs` capped — stop paying for flat epochs.
- **AMP** is CUDA-only; on CPU it does nothing — don't expect it to help the ≤16 GB box.
- Reality check (note 03): CPU training is **~10–40 min/epoch**. For iteration, offload
  to **free Colab T4** and keep the CPU box for the capture/agent loop.

## Impact ÷ effort summary (do these first)

| Rank | Optimization | Impact | Effort |
|---|---|---|---|
| 1 | Event-driven + change-detect inference | HIGH | LOW |
| 2 | Crop to screen ROI (reuse homography) | HIGH | LOW |
| 3 | Export to native runtime (OpenVINO/NCNN/TRT) | HIGH* | LOW |
| 4 | YOLO26n variant (NMS-free, STAL) | MED-HIGH | LOW |
| 5 | Rectangular `imgsz` | MED | LOW |
| 6 | Camera buffer/thread/MJPG | MED-HIGH | MED |
| 7 | Lower `imgsz` post-crop | MED | LOW |
| 8 | Layer fusion (already on) | LOW | ZERO |
| 9 | Threaded loop | MED | MED |
| 10 | Batching/FP16 (realtime) | LOW | — |

\*HIGH specifically on CPU/ARM; marginal if you already run TensorRT on a GPU.

## Sources

- https://docs.ultralytics.com/models/yolo26 — YOLO26: NMS-free, DFL-free, STAL, +43% CPU ONNX vs 11n `[Documented]`
- https://www.ultralytics.com/blog/ultralytics-yolo26-the-new-standard-for-edge-first-vision-ai — edge-first launch overview
- https://docs.ultralytics.com/guides/end2end-detection/ — end-to-end NMS removal rationale
- https://learnopencv.com/yolo26-nms-free-inference/ — native NMS-free explainer `[Community]`
- https://docs.ultralytics.com/integrations/openvino/ — OpenVINO up to 3× CPU speedup `[Documented]`
- https://docs.ultralytics.com/guides/raspberry-pi — NCNN best on ARM; 8-format benchmark `[Benchmark]`
- https://docs.ultralytics.com/modes/benchmark — "Export to ONNX or OpenVINO for up to 3x CPU speedup"
- https://docs.ultralytics.com/guides/model-deployment-options — 20+ runtime targets compared
- https://docs.ultralytics.com/modes/predict/ — `stream=True`, `vid_stride` `[Documented]`
- https://community.ultralytics.com/t/overcoming-time-skip-issues-in-m3u8-stream-processing-with-yolo11-and-opencv/1164/5 — `vid_stride=3` skips frames `[Community]`
- https://stackoverflow.com/questions/54460797/how-to-disable-buffer-in-opencv-camera — `CAP_PROP_BUFFERSIZE=1`, backend-flaky, thread workaround `[Community]`
- https://stackoverflow.com/questions/58293187 — drop stale frames / sync realtime capture `[Community]`
- https://docs.ultralytics.com/models/rtdetr — RT-DETR (transformer, GPU-oriented) `[Documented]`
- https://docs.ultralytics.com/models/yolov10 — YOLOv10 NMS-free dual assignments `[Documented]`
- https://docs.ultralytics.com/usage/cfg/ — `rect`, `imgsz`, `freeze`, `cache`, `half`, `batch` args `[Documented]`

## Open questions / follow-ups

- Does YOLO26n's **NMS-free** path export cleanly to OpenVINO/NCNN here, and how much CPU latency does it save vs YOLO11n at our rectangular crop size? (Benchmark on real hardware → `questions.md`.)
- Change-detection threshold: what `absdiff` pixel-delta separates a real UI change from camera noise/glare without missing subtle changes (e.g. a toggle)?
- Can we skip inference for actions whose result the **agent already predicts**, re-perceiving only on mismatch? (ties to the verify step in spec §7)
- Is `CAP_PROP_BUFFERSIZE=1` honored by our webcam+OS backend, or must we rely on the grabber-thread workaround? (hardware-specific test)
- Where does the deploy host land — Intel (OpenVINO) vs Apple (CoreML) vs ARM (NCNN)? Pick decides #3.
