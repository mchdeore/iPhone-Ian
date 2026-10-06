---
tags: [YOLO, taxonomy, grouping, dataset, ML, computer-vision]
status: answered
date: 2026-10-05
related:
  - "[[YOLO — Efficient Dataset Recipe]]"
  - "[[YOLO — Synthetic Data and Flash Training App]]"
  - "[[YOLO — Training Hardware and Capture Rig]]"
  - "[[VLM GUI Agents and Vision Grounding Survey]]"
---

# 09 — Grouping methods (taxonomy, structure, data splits, compression)

Scope: four senses of "grouping" for the iPhone-Ian detector — (1) how many
**classes** to detect, (2) grouping **detections** into rows/lists/keyboard,
(3) grouping **training data** to split/dedupe without leakage, (4) group-wise
**compression**. Builds on `01` (Phase-1 vocab, session splits, burst dedup) and
`02` (the flash app only auto-labels what it *draws*; Text vs Icon/Widget).

Tags: `[Documented]` docs/papers · `[Benchmark]` measured · `[Community]` forum.

## Q1: How many classes — few coarse vs many fine?

Prior-art taxonomies span two orders of magnitude:

| Dataset / system | Classes | Note |
|---|---|---|
| Springer YOLO-UI study (2025/26) | **3** | Standardized everything to **Text / Button / Icon** `[Benchmark]` |
| ScreenSpot (SeeClick) | **2** | Text vs Icon/Widget (see `02`) `[Documented]` |
| Apple Screen Recognition (CHI'21) | **13** | element types; Text + Icon dominate counts `[Documented]` |
| VINS (CHI'21) | **21** | mAP 76.39%; text/images/icons/switches/checked-views/page-indicators… `[Benchmark]` |
| Rico "Learning Design Semantics" | **25** | + 197 text-button concepts + 135 icon classes (hierarchical) `[Documented]` |
| ScreenParser | **55** | (cited in `01`) `[Documented]` |

Apple's 13 types include Text, Icon, Button, Tab Button, Segmented Control, Toggle,
Checkbox, Slider, Text Field, Picture, Page Control, Dialog, Container `[Documented]`.
The lesson across all of them: **detection stays coarse; fine identity is a separate
layer.** Rico is explicitly hierarchical — a small set of *detected* component types,
then 135 icon classes and 197 button concepts resolved *after* localization. More
classes = more instances needed per class (`01`: ≥1.5k img / 10k inst **per class**),
a worse long tail, and a bigger model — all bad on CPU/≤16 GB (`03`).

**Rule for us: keep the detector's class count small; merge rare classes; push
fine identity to OCR / a second stage.** `[Documented]`

## Q2: YOLO + a second stage for fine identity

MUI elements carry OCR text that detectors routinely ignore, which is exactly the
information that disambiguates them (arXiv:2305.09699) `[Documented]`. For us this is
free: the flash app already knows each target's label string (`02`), so an OCR second
stage is trained/validated at no labeling cost.

- **Text identity** (which button, which field label) → OCR the detected box (Apple
  SR does this in §5.2 "Recognizing UI Content") `[Documented]`. Vision OCR / Tesseract
  / EasyOCR on the crop — cheap on CPU.
- **Icon identity** (135 Rico icon classes) → a small classifier or template/embedding
  match on the icon crop, **not** 135 YOLO classes `[Documented]`.
- **Keyboard keys** → one `keyboard_key` class; read the letter by OCR **or** by grid
  position (Q4), never 26–40 per-letter classes.

This keeps the detector at ~1–7 classes while still answering "tap the *Submit*
button" — the agent's real need (`specs/02 §6–8`).

## Q3: Recommended class list for iPhone-Ian v1

**Phase 0 (ship first):** a single class `tap_target` — matches `01`'s minimal recipe;
proves the whole flash→detect→tap→score loop before taxonomy debates.

**Phase 1 v1 detector — 6 coarse classes:**

| Class | Why it earns a slot | Fine identity via |
|---|---|---|
| `text_button` | Primary tap target (Continue/OK/links) | OCR |
| `icon_button` | Back chevron, share, settings gears, tab-bar icons | icon classifier |
| `text_field` | `login` flow needs focus-then-type (`specs/02 §8`) | OCR (label/placeholder) |
| `toggle_switch` | Distinct affordance + state (on/off) matters | state model |
| `keyboard_key` | Per-key tapping for `type`; dense, high-value | OCR / grid position |
| `cell_row` | List/table rows = large tap zones + structure anchor (Q4) | OCR |

Rationale, tied to constraints: 6 classes keep per-class instance counts reachable
with flash + a small real set; each maps to a **distinct tap affordance**, not a
visual synonym (so merging `text_button`+`link`+`segmented_control` avoids a long
tail); all 6 are renderable in the flash app for auto-labeling (`02`); fewer classes
→ nano stays accurate on low-VRAM/CPU and quantizes cleanly (Q6). **Not** classes:
individual icons, individual keys, "label text" (OCR), Container/Dialog (grouping,
Q4). Add `segmented_control`/`checkbox`/`slider`/`page_control` only when the real
tail justifies it. Keep `fliplr=0` permanently (`01`) — mirroring breaks chevrons/text.

## Q4: Grouping detections into higher-level UI structure

Apple SR solves this post-detection with **heuristics**, not a bigger model:
§5.5 "Grouping Elements for Efficient Navigation" clusters elements into navigable
groups; §5.6 "Inferring Navigation Order" sorts them for VoiceOver `[Documented]`.
Screen Parsing (Wu, UIST'21) instead *predicts* the group tree from the screenshot
`[Documented]` — more machinery than we need.

Lazy, dependency-free recipe (runs host-side in NumPy / `sklearn.cluster.DBSCAN` —
zero training, zero added VRAM):

- **Rows / columns** — 1-D cluster box centers with `DBSCAN` (or sort+gap) on
  **y-centers** → rows, **x-centers** → columns. A known layout trick (Agombar et al.
  2020; EasyOCR issue #121) `[Documented]/[Community]`.
- **Reading order** — classic **XY-cut** (recursive projection cuts) gives
  top-left→bottom-right order cheaply `[Documented]`.
- **Keyboard** — a **fixed grid** in a known region: don't cluster, fit the keyboard
  rectangle once (homography exists, `02`) and index keys by row/col. `ponytail:`
  template beats clustering; add DBSCAN only if layouts vary (emoji/numeric/languages).
- **Forms / lists** — proximity + alignment of `text_field`/`cell_row`/`text_button`; a
  label is the nearest `text` left/above a field.

## Q5: Grouping training data — splits, sampling, dedup

`01` already says "split by session, not frame" and "de-duplicate bursts". Concretely:

- **Group-aware split** so near-identical frames can't straddle train/val (the classic
  mAP-inflation trap): `GroupShuffleSplit` for one split, `GroupKFold` /
  **`StratifiedGroupKFold`** for CV, with **group key = session / app / screen-id**.
  StratifiedGroupKFold keeps class balance *and* non-overlapping groups `[Documented]`.
- **Dedupe before splitting.** Perceptual hash (`imagededup`/`imgdupes`) is cheap but
  weak on near-dups and geometric shifts; CNN-embedding dedup is robust but costlier
  (MDPI 2026) `[Benchmark]`. Run **pHash first** (static camera → near-dups are
  near-identical); fall back to embeddings only for subtle cases.
- **Stratified sampling** when oversampling rare classes / hard examples (tap-score miss
  set, `01`) — keep per-class proportions matched across splits.
- Order matters: **dedupe → assign groups → stratified-group split**; a random split
  after dedupe re-introduces leakage.

## Q6: Group-wise compression (brief)

Relevant because training/inference may be CPU-only ≤16 GB (`03`):

- **Grouped / depthwise-separable convs** cut FLOPs/params and are already in YOLO
  backbones — nothing to add, just prefer the light `n` model `[Documented]`.
- **Group / per-channel quantization** gives each channel group its own scale and keeps
  far more accuracy than per-tensor at INT8 (Quantizing-YOLOv7 granularity study; GroupQ
  clusters kernels into bit-precision groups) `[Benchmark]/[Documented]`. Matters when
  exporting to **ONNX/NCNN/OpenVINO** for CPU inference on the rig host; Ultralytics
  `export(..., int8=True)` applies per-channel quant for free. `ponytail:` use the
  exporter, don't hand-roll it.

## Key takeaways

- Detector = **few coarse classes** (start 1, then ~6); fine identity = **OCR + a small icon classifier** (Rico's hierarchy; flash app's free labels).
- Recommended v1: `text_button, icon_button, text_field, toggle_switch, keyboard_key, cell_row`. Merge the rare tail; expand only when real captures demand it.
- Group **detections** with cheap host-side heuristics (DBSCAN on centers, XY-cut order); treat the **keyboard as a fixed grid**, not a clustering problem.
- Group **data** by session/app and dedupe (pHash) **before** a StratifiedGroupKFold split — the biggest guard against inflated mAP.
- Compression: prefer nano + exporter per-channel INT8; grouped convs are already there.

## Sources

- https://arxiv.org/abs/2101.04893 — Apple Screen Recognition, CHI'21: 13 element types; §5.5 grouping, §5.6 nav order `[Documented]`
- https://machinelearning.apple.com/research/screen-parsing — Screen Parsing (Wu, UIST'21): predicts UI group tree `[Documented]`
- https://experts.illinois.edu/en/publications/learning-design-semantics-for-mobile-apps — Rico semantics: 25 types + 197 button concepts + 135 icon classes `[Documented]`
- https://arxiv.org/abs/2102.05216 — VINS: 21 UI classes, detection mAP 76.39% `[Benchmark]`
- https://arxiv.org/abs/2305.09699 — MUI element detection needs the OCR text detectors ignore `[Documented]`
- https://link.springer.com/10.1007/978-3-032-12478-4_9 — YOLO UI study standardized to 3 classes (Text/Button/Icon) `[Benchmark]`
- https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html — group-aware, stratified splits `[Documented]`
- https://github.com/idealo/imagededup — pHash + CNN near-dup dedup (`imgdupes` is a pHash-only CLI alt) `[Documented]`
- https://www.mdpi.com/2079-9292/15/7/1493 — hashing (cheap, weak on near-dups) vs deep embeddings (robust, costly) `[Benchmark]`
- https://link.springer.com/chapter/10.1007/978-3-030-57321-8_23 — DBSCAN-backed document layout grouping `[Benchmark]`
- https://www.researchgate.net/publication/4214809_Optimized_XY-cut_for_determining_a_page_reading_order — XY-cut reading order `[Documented]`
- https://arxiv.org/abs/2407.04943 — Quantizing YOLOv7: quantization granularities `[Benchmark]`
- https://dl.acm.org/doi/10.1109/TCAD.2024.3363073 — GroupQ: group-wise CNN quantization `[Documented]`

## Open questions / follow-ups

- `keyboard_key`-as-one-class + OCR vs per-key classes for `type` reliability? Measure on real keyboards (flag in `questions.md`).
- Minimum real-capture count before adding `segmented_control`/`checkbox`/`slider` without starving the tail?
- Is pHash enough with a locked camera, or do True Tone / glare swings (`02`) need embedding-based dedup?
- Feed group structure (rows/forms) to the agent as context, or only use it to pick a tap point? (ties to `specs/02 §7`.)
