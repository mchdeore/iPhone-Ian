---
tags: [YOLO, quantization, INT8, FP16, deployment, ML, computer-vision]
status: answered
date: 2026-10-05
related:
  - "[[ML Central]]"
---

# 05 — Quantizing YOLO weights for low-VRAM / CPU deployment

## Question

Whether and how to quantize the iPhone-Ian detector — FP16 vs INT8 vs INT4, PTQ vs
QAT, calibration, sensitive layers, measured accuracy drops, and exact export commands.

Orientation: inference runs on the **host filming the phone, not the stock iPhone**
(`03-hardware.md`) → quantize for the *host* runtime: OpenVINO on the ≤16 GB Intel CPU
box, TensorRT on the RTX 3060, or CoreML/MPS on the Mac. CoreML/TFLite/NCNN INT8 matter
only if detection moves to a true edge device. Tags: `[Documented]`·`[Benchmark]`·`[Community]`.

## FP16 vs INT8 vs INT4

- **FP16 (half)** — 16-bit float weights+activations. **~Lossless** (OpenVINO YOLO26:
 FP32≡FP16 mAP50-95 to 4 dp, n→x), **~2× smaller**, zero calibration, one flag. Needs
 Tensor Cores (GPU) or any FP16 runtime. **This is the default choice.** `[Benchmark]`
- **INT8** — 8-bit affine `val ≈ scale·(q − zero)`. **~3–4× smaller**, big CPU/edge
 speedup, **~1–3 mAP pts lost** (table). Needs a calibration pass. `[Documented]`
- **INT4 / sub-8-bit** — an LLM technique; for CNN detectors it needs QAT, loses real
 accuracy, thin runtime support → **skip**. The practical "mixed" lever is keeping
 sensitive layers in FP16 (Ultralytics `quantize="w8a16"` = INT8 weights/FP16 acts).
 Nano is already ~5 MB → quantize for **CPU latency**, not size. `[Documented]/[Community]`

## PTQ vs QAT

- **PTQ** — calibrate a trained model on a few hundred images, no retraining. Minutes;
 fits the minimal-effort charter. Fails only at aggressive bitwidths and hurts **small
 models more** (nano has little redundancy to absorb rounding). `[Documented]/[Community]`
- **QAT** — simulate rounding/clipping in training so weights adapt; recovers most PTQ
 loss (~2× speedup at near-FP accuracy reported on Jetson Orin Nano) but needs a
 training loop. `[Community]`
- **Plan**: PTQ by default; escalate to QAT only if PTQ (even w8a16) misses *and* FP16
 is too slow/big. Labels are free (flash app), so QAT is cheap to try if needed.

## Calibration — use flash-app captures

- **Representativeness beats size.** The set must match the deployed distribution; a
 camera-of-screen domain is nothing like COCO. **Reuse the flash-app val split**
 (`02`) — same glare/moiré/brightness. `[Documented]`
- **Size**: ~**100–500 images** is the standard sweet spot (NNCF/ONNX/TensorRT);
 Ultralytics `fraction` sets it (ratio or image count). `[Documented]`
- **Trap**: `quantize=8` with **no `data=` falls back to a default COCO calibration
 set** → wrong domain, silent loss. Always pass `data=flash.yaml`. `[Documented]`
- **Methods** (ONNX Runtime): `MinMax` (default), `Entropy` (KL), `Percentile`;
 Entropy/Percentile clip activation outliers → usually better for detectors. `[Documented]`

## Per-channel vs per-tensor, and sensitive layers

- **Weights per-channel** (one scale per output channel) = default, clearly more
 accurate for conv; **activations per-tensor**. Use `per_channel=True`. Symmetric
 weights / asymmetric activations is the common HW-friendly scheme. `[Documented]`
- **Sensitive parts of a YOLO graph** (quantize last / keep FP16):
 - **Detect head + DFL** — Distribution Focal Loss softmaxes bin logits, a wide
  outlier-prone range INT8 mangles. `[Community]`
 - **First conv (stem)** and **final output convs** — classic keep-higher layers. `[Community]`
 - **Concat / residual-add** need aligned input scales; mismatched ranges leak error. `[Documented]`
 - **Small objects degrade disproportionately** under INT8 (low-signal, high-variance
  shallow activations) — directly relevant to our small UI icons. `[Benchmark]`
- Mitigation ladder: per-channel + Entropy → exclude detect head/DFL
 (`nodes_to_exclude`/`w8a16`) → QAT. ONNX Runtime `qdq_loss_debug` auto-finds the
 worst tensors. `[Documented]`

## Measured accuracy drops (COCO mAP50-95)

OpenVINO PTQ, Ultralytics YOLO26 (same head family as YOLOv8/11; behavior transfers).
FP16 lossless; INT8 drop grows with model size. `[Benchmark]`

| Model | FP32 | FP16 | INT8 | Δ | Size FP32→INT8 |
|---|---|---|---|---|---|
| n | 0.4762 | 0.4762 | 0.4634 | −2.7% | 9.7→3.2 MB |
| s | 0.5616 | 0.5616 | 0.5462 | −2.7% | 36.7→10.0 MB |
| m | 0.6166 | 0.6166 | 0.6055 | −1.8% | 78.4→20.6 MB |
| l | 0.6205 | 0.6205 | 0.5938 | −4.3% | 95.3→25.2 MB |
| x | 0.6568 | 0.6568 | 0.6385 | −2.8% | 213→54.8 MB |

Speed (155H CPU, ms/im): n 9.1→5.8 (**1.6×**), m 34.5→15.5 (**2.2×**); on a fast iGPU
nano INT8 is *not* faster (overhead-bound). TensorRT static INT8 (YOLOv8/11): **1.5–3.3×
speedup, 3–7% mAP50-95 drop**. `[Benchmark]`

## Commands

```bash
# Ultralytics ≥ v8.4.80 unified `quantize` (replaces half=/int8=, still supported)
yolo export model=best.pt format=openvino quantize=16              # FP16, lossless
yolo export model=best.pt format=openvino quantize=8 data=flash.yaml fraction=300 # INT8 PTQ (NNCF)
yolo export model=best.pt format=engine  quantize=8 data=flash.yaml       # TensorRT INT8
yolo export model=best.pt format=coreml  quantize=8 data=flash.yaml       # Mac host
# onnx / tflite / ncnn also accept quantize=16|8 data=; mixed: quantize="w8a16"
yolo val model=best_openvino_model/ data=real_ios.yaml  # measure drop on REAL iOS, not flash
```

```python
# ONNX Runtime static PTQ (full control: per-channel, exclude head, calib method)
from onnxruntime.quantization import quantize_static, QuantType, QuantFormat, CalibrationMethod
from onnxruntime.quantization.shape_inference import quant_pre_process
quant_pre_process("yolo.onnx", "yolo.prep.onnx")       # optimize HERE, not in quant
quantize_static("yolo.prep.onnx", "yolo.int8.onnx",
  calibration_data_reader=FlashAppReader("calib/", n=300), # yields {input: NCHW float}
  quant_format=QuantFormat.QDQ, per_channel=True,      # QDQ portable; QOperator is alt
  weight_type=QuantType.QInt8, activation_type=QuantType.QUInt8,
  calibrate_method=CalibrationMethod.MinMax,        # Entropy/Percentile if drop high
  nodes_to_exclude=[...],                  # detect head / DFL if sensitive
  reduce_range=True)                    # only on pre-VNNI x86 CPUs
```
INT8 CPU speedup needs **VNNI (x86)** or dot-product (ARM) instructions, else it may
not beat FP32. OpenVINO INT8 = NNCF under the hood; TensorRT INT8 ≈ `trtexec --int8` + calib cache. `[Documented]`

## Minimal recipe

1. Train FP32 (`yolo11n`, per `01`).
2. **Export FP16** (`quantize=16`); `yolo val` on **real iOS captures** → expect ~0
  drop. Ship this unless CPU-bound. `[Benchmark]`
3. **Only if the ≤16 GB CPU box is the inference host**: INT8 PTQ, `data=flash.yaml
  fraction≈300` (reuse val split), per-channel, QDQ, OpenVINO.
4. `yolo val` INT8 on real captures **and** check the tap-score metric from `01`
  (closed-loop error matters, not just mAP). Too big a drop → `w8a16` / exclude detect
  head+DFL → QAT as last resort.
5. **Recalibrate when the rig changes** (lighting/camera/homography) — same discipline
  as the labels in `01`/`02`.

## Key takeaways

- FP16 is free accuracy-wise and halves size — the default; INT8 only to unlock CPU speed.
- Calibrate on **flash-app captures** (100–500 imgs); never let `data=` default to COCO.
- Per-channel weights + Entropy/Percentile; detect head, DFL, small objects are the risks.
- INT8 PTQ ≈ 1–3 mAP pts (nano/small), up to ~4% larger / with TensorRT; FP16 ≈ 0.
- PTQ first; QAT only if a FP16-mix still misses. Validate on **real iOS + tap score**.

## Sources

- https://docs.ultralytics.com/modes/export — export args, `quantize`/`data`/`fraction`
- https://community.ultralytics.com/t/new-release-ultralytics-v8-4-80/2085 — unified `quantize=8/16/32`, `w8a16`
- https://docs.ultralytics.com/integrations/openvino/ — NNCF INT8, FP16-lossless + INT8 benchmark table
- https://docs.ultralytics.com/integrations/tensorrt/ — INT8/FP16 calibration, engine caveats
- https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html — `quantize_static`, QDQ, MinMax/Entropy/Percentile, debug
- https://quark.docs.amd.com/latest/tutorials/onnx/ryzen_ai/yolov8/onnx_ryzen_ai_yolov8_tutorial.html — YOLOv8 ONNX PTQ, CLE/mixed precision
- https://arxiv.org/html/2508.19600 — TensorRT static INT8: 1.5–3.3× speedup, 3–7% mAP drop
- https://theses.liacs.nl/pdf/2025-2026-JohannsenL.pdf — INT8 disproportionately degrades small objects; QAT recovery
- https://medium.com/@smallerNdeeper/quantization-yolov8-qat-x2-speed-up-on-your-jetson-orin-nano-1-why-quantization-e052a72c506d — PTQ worse on small models; QAT 2× on Orin Nano

## Open questions / follow-ups

- Does INT8 move the **tap-accuracy / homography error**, or just mAP? Needs the
 closed-loop metric from `01`, not COCO mAP. → `questions.md`
- Is the inference host the ≤16 GB CPU box, the RTX 3060, or the Mac? Decides FP16-GPU
 vs INT8-CPU → belongs in ``.
- Does FP16-only on the DFL (`w8a16`/`nodes_to_exclude`) recover the small-icon loss at
 near-INT8 speed? One A/B export answers it. Prune-then-quantize ordering → ``.
