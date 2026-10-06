---
tags: [YOLO, index, ML, computer-vision]
status: answered
date: 2026-10-04
related:
  - "[[agent-ml/02-vlm-gui-agent-survey]]"
---

# YOLO training setup — research index

Research session 2026-10-04. Question: what makes an efficient "reinforcement"
YOLO training setup for iPhone-Ian (dataset, synthetic flash app, hardware)?
Gathered by three parallel research agents; sources listed in each note were found
by those agents and not individually re-verified.

| File | Covers |
|---|---|
| [`01-efficient-dataset.md`](01-efficient-dataset.md) | Dataset size, label quality, diversity, splits, `imgsz`, augmentations, model size, "is reinforcement YOLO a thing?", minimal recipe |
| [`02-synthetic-data-and-flash-app.md`](02-synthetic-data-and-flash-app.md) | Domain randomization, synthetic:real ratios, flash-app architecture, CSS px/DPR, Safari viewport, sync, glare/moiré, pitfalls |
| [`03-hardware.md`](03-hardware.md) | Bare-minimum hardware, most vs least limiting components (ranked), cost tiers, capture rig |

### Session 2 (2026-10-05): 12 parallel research agents

Sources were found by the agents and not individually re-verified.

| File | Covers |
|---|---|
| [[04-training-on-hardware]] | Ultralytics args per device (CPU 16 GB, MPS, low-VRAM NVIDIA, Colab/Kaggle, Pi); CPU-server verdict |
| [[05-quantization]] | PTQ vs QAT, FP16/INT8, calibration on flash captures, sensitive layers, export commands |
| [[06-flask-trainer-app]] | Closed-loop Flask trainer: SSE flash+act commands, Safari pointer capture, JSONL episodes, skeleton |
| [[07-pruning]] | Structured vs unstructured, Torch-Pruning/NNCF, measured results, verdict: skip for now |
| [[08-other-optimizations]] | Change-detection inference, screen-ROI crop, native runtimes, YOLO26n, camera latency, ranked |
| [[09-grouping-methods]] | Class taxonomy (v1 class list), grouping detections into rows/lists, dedupe + group-aware splits |
| [[10-knowledge-distillation]] | KD on low-VRAM/CPU, native `distill_model=`, offline pseudo-labeling as the cheap alternative |
| [[11-quantization-by-hardware]] | Hardware × precision matrix (x86, Apple, NVIDIA, Jetson, Pi, Hailo, Coral) + per-task picks |
| [[12-efficient-training-strategy]] | Quickest minimal-effort plan with commands + hour estimates; what NOT to do |
| [[13-exposing-device-controls]] | Action API, screen→gantry→GRBL mapping, MCP tool exposure, safety, AssistiveTouch alternative |
| [[14-windows-public-port-and-streaming]] | Tailscale vs Cloudflare Tunnel vs port-forward; WebRTC/WS/ZMQ streaming; Windows 24/7 hardening |
| [[15-raspberry-pi-input-converter]] | Pi serial bridge, Pi/ESP32 USB/BLE HID into iPhone, relative-pointer limits, BOM |

## Questions answered (short form)

**Is "reinforcement YOLO" a thing?** No. YOLO is supervised detection. The tap
score is best used as a calibration metric and hard-example signal; RL is optional
and only on top, for sequential navigation. → `01`

**What makes an efficient training set?** Pretrained nano model; a few hundred
instances/class to start (Ultralytics target ≥1,500 images / ≥10k instances per
class); diversity of conditions over raw count; 0–10% negatives; split by session,
not frame; crop to screen; `fliplr=0`. → `01`

**How do we make synthetic data?** The flash app: Flask page in Safari shows
randomized targets + 4 fiducials in CSS px; flash → hold → capture; per-frame
homography maps boxes to camera pixels → YOLO labels for free. Add ~5–20% real iOS
captures for fine-tune/validation. → `02`

**Bare minimum hardware?** $0: the current Mac as rig host + free Colab T4 for
training. Cheapest local GPU worth buying: used RTX 3060 12 GB (~$300). Camera:
1080p UVC webcam with locked focus/exposure. → `03`

**What matters most?** GPU VRAM → Tensor Cores/memory bandwidth → CUDA (vs MPS/CPU)
→ dataloader throughput. → `03`

**What matters least?** PCIe gen/lanes, CPU beyond 6–8 cores, RAM beyond 2× dataset,
NVMe vs SATA, storage size, PSU/motherboard/network. → `03`

**Can a 16 GB CPU-only box be the training server?** Yes, but only for overnight
runs: about 10–20 h for a full nano run, compared with about 0.5–1.5 h on a free Colab T4. Iterate on
Colab. Move the dataset as a zip, so no public port is needed. → `04`, `12`

**Quickest training recipe?** Fine-tune COCO `yolo11n.pt` (or `yolo26n.pt`), crop to the
screen, 640, `cache=ram`, `freeze=11`, `patience≈20`. Use one pooled synthetic + 5–20% real run.
Always retrain from pretrained on the full pool and never fine-tune on only the new frames. → `12`

**Quantize / prune / distill?** FP16 export by default. Use INT8 PTQ (calibrated on
flash captures) only if CPU-bound. Skip pruning. Skip feature KD on CPU, and pseudo-label real
captures offline with a big model instead. The gantry costs seconds per tap, while the nano forward pass
takes milliseconds, so compression is not the bottleneck. → `05`, `07`, `10`, `11`

**Biggest runtime win?** Only run inference when the screen changes, and crop to the
screen ROI with the existing homography. → `08`

**Classes?** Phase 0 uses one class, `tap_target`. Phase 1 uses `text_button, icon_button,
text_field, toggle_switch, keyboard_key, cell_row`. Fine identity comes from OCR or a second stage. → `09`

**Controls and networking?** Use a backend-agnostic screen-coordinate action API exposed as
MCP tools. Use Tailscale between machines, not a public port. Never expose GRBL serial or the
Flask dev server. → `13`, `14`

## Cross-note tension to resolve

`13`/`15` propose AssistiveTouch + HID mouse/keyboard as a gantry-free control path.
This contradicts `07-ios-control-constraints` ("don't rely on accessibility
features") and the charter's "phone is untouched" premise, because it needs a one-time Settings
toggle. HID pointers on iOS are relative-only. Possible compromise: keep the gantry for taps and add
an ESP32 BLE/USB HID keyboard for `type`. This needs a decision in `specs/`.


`01` suggests `imgsz` 960–1280 for small icons; `03`'s timings assume 640, and 1280
costs ~4× memory/time. Plan: **crop to screen and start at 640**; raise `imgsz`
only if small targets are missed.

## Suggested next steps

1. Build the flash page (Flask, 4 ArUco fiducials, randomized targets, frame-ID patch).
2. Capture Phase 0 (~500 frames, single class) with locked camera settings.
3. Train `yolo11n` on Colab T4; validate on real, hand-checked iOS captures.
