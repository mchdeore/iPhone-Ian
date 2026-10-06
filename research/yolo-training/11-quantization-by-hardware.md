---
tags: [YOLO, quantization, hardware, edge, inference, ML, computer-vision]
status: answered
date: 2026-10-05
related:
  - "[[05-quantization]]"
  - "[[03-hardware]]"
  - "[[01-efficient-dataset]]"
---

# 11 — Quantization formats by hardware and task

Scope: which export/quantization formats run on which hardware, and which precision to
use for each iPhone-Ian task. `03-hardware.md` covers **training** boxes (GPU VRAM,
Colab); this note covers **inference/deployment** precision. Quantization mechanics
(what PTQ/INT8/FP16 *are*) live in `05-quantization.md`; here it's applied to real
silicon. The phone being tapped is a black box — nothing of ours runs on it — so
"deployment target" means the **host that films the screen**, not the iPhone.

Tags: `[Documented]` docs · `[Benchmark]` measured · `[Community]` anecdotal.

## Q: What runs where? (the matrix)

YOLO11n ≈ YOLO26n in cost (same nano class); where only YOLO26n is published I label it.
All Ultralytics numbers are COCO @ `imgsz=640`, inference-only (no pre/post), nano model.

| Hardware | Best export format | FP32 / FP16 / INT8 | Expected nano FPS @640 | mAP loss vs FP32 |
|---|---|---|---|---|
| **x86 CPU** (Win/Linux; AVX2 / AVX-512 / VNNI / AMX) | OpenVINO (ONNX fallback) | ✅ / ✅ / ✅ (VNNI/AMX accel INT8) | real-time (tens of FPS); OpenVINO up to **3× PyTorch** CPU `[Documented]` | FP16 ≈0; INT8 ~1–3% |
| **Intel iGPU / NPU** | OpenVINO (`intel:gpu` / `intel:npu`) | ✅ / ✅ (iGPU) / ✅ (NPU is INT8-centric) | real-time, device-dependent `[Documented]` | FP16 ≈0; INT8 small |
| **Apple Silicon** (Mac host): CoreML→ANE, or MPS | CoreML `.mlpackage` (ANE); `.pt`+MPS | ✅ (CPU/GPU) / ✅ / ✅ (ANE weight-quant) | YOLO26n INT8 **3.2 ms CPU+ANE ≈ 310 FPS** burst / ~88 FPS camera (A19 Pro, 16-core ANE) `[Benchmark]` | INT8 weight-quant small |
| **NVIDIA consumer GPU** (RTX 20→40) | TensorRT (`.engine`) | ✅ / ✅ / ✅ | FP16 sub-2 ms → **100s of FPS** on RTX 30/40 `[Community]` | FP16 ≈0; INT8 1–6% |
| **Jetson Orin Nano Super** (8 GB) | TensorRT | ✅ / ✅ / ✅ | YOLO26n **FP32 133 / FP16 219 / INT8 263 FPS** (7.53 / 4.57 / 3.80 ms) `[Benchmark]` | FP16 ≈0; **INT8 −0.031 mAP (~6.5% rel)** `[Benchmark]` |
| **Raspberry Pi 4/5 CPU** | **NCNN** (ARM); else OpenVINO/MNN | ✅ / ✅ / ~ (ARM INT8 gain modest) | Pi 5 YOLO26n **NCNN 67 ms ≈ 15 FPS** vs ONNX ~8 FPS; YOLO11n ONNX 6.8 FPS `[Benchmark]` | NCNN ≈0 (runs FP32/FP16) |
| **Pi 5 + Hailo-8L** (AI Kit, 13 TOPS NPU) | Hailo HEF (`format=hailo`) | ❌ / ❌ / ✅ **INT8-only** | YOLOv8s @640 **~30 FPS**; nano higher; Hailo-8 (26 TOPS) ~2× `[Benchmark]/[Community]` | INT8 PTQ; needs **≥1,024 calib imgs** `[Documented]` |
| **Coral Edge TPU** (USB, 4 TOPS) | TFLite full-int8 `_edgetpu.tflite` | ❌ / ❌ / ✅ **INT8-only** | YOLO maps **poorly** — many ops fall back to CPU; built for SSD-MobileNet/EfficientDet `[Community]` | INT8 + op-fallback **reduces YOLO accuracy** `[Benchmark]` |
| **iPhone itself** (the tapped phone) | CoreML *if we owned it* — but we don't | — | **N/A — black box; our model never runs on it** | N/A |

## Q: What does each precision actually cost?

- **FP16**: ~2× speed / ½ memory vs FP32 on Tensor Cores / ANE / NPUs, with **effectively zero mAP loss** (Jetson 26n: FP32 0.477 → FP16 0.480). The safe default anywhere with FP16 hardware. `[Benchmark]`
- **INT8 (PTQ)**: another ~1.2–1.5× over FP16 and ¼ model size, but needs a **calibration set** and costs mAP — small on bigger models, **meaningful on nano** (Jetson 26n dropped 0.479→0.449). TensorRT engines are **device-specific**; calibrate on the target. `[Benchmark]/[Documented]`
- **QAT** (quantization-aware training): recovers most INT8 loss by simulating quant during training, but it's extra training machinery — **not used here** (see task c). `[Documented]`
- **ARM CPU (Pi)**: Ultralytics publishes Pi numbers at **FP32**; NCNN already wins on ARM via NEON/FP16 kernels, so INT8 buys little and isn't the default path. `[Benchmark]`
- Export-location gotchas: **Edge TPU, Hailo, and LiteRT compile only on x86_64 Linux** (Hailo/Coral also need it); CoreML compiles on macOS or x86 Linux. A Windows-only box can't produce these artifacts without WSL/Linux/Colab. `[Documented]`

## Q: Which setup for each iPhone-Ian task?

**The punchline first:** the gantry + stylus move in **seconds per tap**, and the flash
app's labels come from **homography, not a model**. So the detector's critical path needs
only a few FPS, and nothing in this project is quantization-bound. Reach for INT8/NPUs
only if you later want to free the host — and even then you probably won't need to.

**(a) Live inference for tapping** — latency target is loose (gantry is the bottleneck,
not YOLO). Run `yolo11n` **on the existing capture host**, no accelerator:
- Mac host → **CoreML (ANE)** or just `.pt` on **MPS**; FP16 is plenty, INT8 unnecessary.
- x86 host → **OpenVINO FP16** (ONNX if lazy). 
- If offloaded to a Pi 5 → **NCNN FP32 (~15 FPS)** already exceeds what one stylus needs.
→ **Recommendation: ONNX/CoreML FP16 on the host you already have. Skip quantization.**
`ponytail:` the mechanical loop caps throughput; buying a Hailo/Jetson for a one-stylus
rig is effort with no payoff. Upgrade path = add Hailo-8L only if you run many camera
streams later.

**(b) Auto-labeling synthetic flash data** — this is **geometry (fiducials → homography →
boxes), not inference** (`02-synthetic-data-and-flash-app.md`), so **no model, no
quantization** at all; OpenCV on CPU. *If* you later model-assist pre-labeling of **real**
captures, use **full precision (FP32/FP16)** — never INT8 — because label fidelity matters
more than speed, and it's an offline batch job where latency is irrelevant.

**(c) Training** — **quantization is not used for training.** Train in FP32 with AMP
(mixed FP16), exactly as `03-hardware.md` recommends (Colab T4 > the CPU-only 16 GB box,
which works but crawls). INT8/PTQ is a **post-training export** step. Only reach for **QAT**
if a chosen INT8 target later shows unacceptable nano mAP loss — unlikely to be worth it.

**(d) Serving the flash webapp alongside inference** — Flask is **near-zero load** and
co-hosts fine with the detector on one machine (`specs/02-firmware-and-software.md` §5.1).
CPU-only is fine. To expose the Windows box's port publicly, prefer a **tunnel
(cloudflared / ngrok / Tailscale)** over opening a firewall port — no public inbound, less
attack surface. **Note:** the flash page serves synthetic targets only; never run captures
over a public link while real screen content is visible (charter credential rules).

## Key takeaways

- **FP16 everywhere it exists** — free ~2× with ~0 mAP loss. Make it the default. `[Benchmark]`
- **INT8 hurts nano more than big models** (Jetson 26n −6.5% rel); use only when a device demands it, and calibrate on-device. `[Benchmark]`
- **Hailo-8L and Coral are INT8-only**; Coral additionally maps YOLO badly (op fallback) — Hailo ≫ Coral for YOLO. `[Community]`
- **Pi: use NCNN** (ARM-optimized, FP32/FP16); ~15 FPS nano is more than one stylus needs. `[Benchmark]`
- **For iPhone-Ian specifically: quantization is a non-issue** — the gantry is the bottleneck and labels are geometric. Run FP16 on the host; buy an NPU only for multi-stream futures.
- Edge TPU / Hailo / LiteRT artifacts **must be compiled on x86_64 Linux** — plan for Colab/WSL if the host is Windows-only. `[Documented]`

## Sources

- https://docs.ultralytics.com/guides/raspberry-pi — Pi 5 8-format table: NCNN 67.03 ms / mAP 0.4784, ONNX 125.99 ms (26n); YOLO11n ONNX 147.20 ms / 39.5 `[Benchmark]`
- https://docs.ultralytics.com/guides/nvidia-jetson — Orin Nano Super 26n: TensorRT FP32 7.53 / FP16 4.57 / INT8 3.80 ms, INT8 mAP 0.449 vs 0.477 `[Benchmark]`
- https://docs.ultralytics.com/integrations/openvino/ — `quantize=16/8/32`; up to 3× CPU speedup; `intel:cpu/gpu/npu` `[Documented]`
- https://docs.ultralytics.com/integrations/coreml/ — `quantize=8` INT8, `.mlpackage`/ANE; iPhone 17 Pro 26n INT8 3.2 ms CPU+ANE `[Benchmark]`
- https://docs.ultralytics.com/integrations/hailo/ — `format=hailo`, INT8-only HEF, ≥1,024 calib imgs, x86_64-Linux compile `[Documented]`
- https://docs.ultralytics.com/guides/coral-edge-tpu-on-raspberry-pi/ — full-int8 `_edgetpu.tflite`, x86_64-Linux compile `[Documented]`
- https://docs.ultralytics.com/integrations/ncnn/ · https://docs.ultralytics.com/modes/benchmark/ — NCNN best on ARM; ONNX/OpenVINO ~3× CPU `[Documented]`
- https://wiki.seeedstudio.com/benchmark_on_rpi5_and_cm4_running_yolov8s_with_rpi_ai_kit/ — Hailo-8L YOLOv8s int8 640 `[Benchmark]`
- https://community.hailo.ai/t/raspberry-pi-5-with-hailo-8l-benchmark/746 — Hailo-8L real-time nano/small `[Community]`
- https://arxiv.org/abs/2409.16808 — Edge TPU aids SSD/EfficientDet but reduces YOLOv8 accuracy `[Benchmark]`
- https://www.mdpi.com/2504-4990/8/7/204 — YOLOv8–v12 FPS/mAP across Pi 4/5, Jetson, LattePanda `[Benchmark]`

## Open questions / follow-ups

- Exact YOLO11n **NCNN** ms on Pi 5 (only ONNX 11n and NCNN 26n are published) — benchmark locally if a Pi becomes the host.
- Does the Mac host's **ANE via CoreML** beat plain **MPS** enough to bother, given the loose latency budget? Likely no — measure only if inference ever shares the host with heavy work.
- If multi-camera/multi-stylus is ever on the table, re-open the Hailo-8L vs Jetson Orin Nano choice (then INT8 and `[[05-quantization]]` calibration actually matter) → flag in `questions.md`.
