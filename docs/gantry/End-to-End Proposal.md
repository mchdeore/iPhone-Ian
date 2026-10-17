# Gantry: build, train and run red / blue trials

The first usable system is an owned mobile web app with repeatable layouts,
trained vision actions, a calibrated controller boundary and a live battle
scoreboard. Red completes tasks from screenshots. Blue observes the contacts
received by the website. A separate evaluator supplies task outcomes and label
truth after actions. The same contracts then carry across to the physical gantry.

Open [Gantry Vision Roadmap.canvas](../../Gantry%20Vision%20Roadmap.canvas) for
the stages, and [phone lab](../../packages/phone_lab/README.md) for commands.

## 1. Prepare the owned app and synthetic data

Run the curator app in `packages/phone_lab`:

```sh
uv sync --extra test
uv run python -m phone_lab data-web --store .local/synthetic-data \
  --browser-executable '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
```

Open `http://127.0.0.1:8766`. Enter seeds, viewport and tags, then generate a
dataset. Filter by task and split; toggle borders; download manifest, catalog
and annotation JSON. Tags are bounded lowercase words. Changing tags creates
another immutable dataset; it does not rewrite existing captures or labels.

Each seed produces tap, drag, entry, menu, overlay and scroll task states. A
layout seed stays in one split. Layout, session, device and font groups must
not cross train/validation/test boundaries. Current fonts are deliberately
segregated by split. Add more fonts and real devices as separately reviewed
generator versions, and retain an unseen real-phone holdout.

```text
.local/synthetic-data/<dataset-id>/
  catalog.json                 stable sample IDs, tags, borders and hashes
  catalog.sha256               catalog integrity receipt
  manifest.json                rendered layout and evaluator provenance
  images/{train,val,test}/     actual browser PNG captures
  labels/{train,val,test}/     normalized YOLO boxes
  annotations/{train,val,test}/
                              pixel borders and deterministic tags
  dataset.yaml                 local training configuration
  dataset-portable.yaml        configuration for use from dataset directory
```

IDs derive from generator source, recipe, sorted seeds/tags, viewport, task and
phase. Annotation borders come from the rendered component DOM and use CSS
pixels, origin at top left, at device scale 1. The image is captured after fonts
settle and two consecutive PNGs agree. Matching environments are required for
pixel reproducibility; renderer updates are a new acquisition, not assumed
equivalent data. Execution timestamps belong in run receipts, not sample IDs.

Keep curator/evaluator APIs separate from red's screenshots and blue's narrow
contact export. Ground-truth boxes are useful for training and scoring; they
are never a shortcut for selecting actions during a trial.

## 2. Train and evaluate vision

Start with the existing five detector roles: button, field, handle, destination
and list. OCR supplies visible text and numeric instructions. Store generator
recipe, source hashes, split audit, training seed, model hash and configuration
with every experiment. Existing tools are `tools/vision_pilot.py` and
`tools/owned_policy_smoke.py`; the vision dependencies have their own pinned
requirements because their NumPy version differs from the base app.

Audit hashes, border/YOLO alignment, group leakage and duplicate proxies before
training. Evaluate target precision/recall, safe interior-point hits, OCR error,
frame age, latency and complete task outcomes. Retain low-confidence and stale
frame refusals. Export comparisons use identical captures and preprocessing;
an export is accepted only after numerical and decision parity checks.

The current trained CPU pilot provides a local starting point. The GTX 1080
plan assumes its actual 8 GB only when attached and verified. Physical phone
accuracy, GPU performance and real-device holdout results remain unmeasured.
Do not tune on the reserved real holdout or calibrate precision on test data.

## 3. Let red and blue run matched trials

Red's loop is screenshot → detector/OCR → typed intent → calibrated bounds and
freshness checks → contact → new screenshot. Existing one-use arming, device
and frame identity, confidence, acknowledgement and stop checks remain active.
The local controller uses fake acknowledgements; browser entry and wheel events
are declared stand-ins until a physical implementation is commissioned.

Blue receives only session identity, viewport and observed contact/input/scroll
event kind, time, coordinates and pointer ID. It never receives entered text,
robot labels, camera frames, motor paths, hover, capability tokens or target
boxes. Frozen descriptive rules flag short dwell, repeated dwell or straight
contact paths. These are hypotheses, with no robot probability or sanctions.

With the reviewed trained checkpoint and the owned OCR binary available:

```sh
python tools/owned_battle.py .local/battles/round-set-001 \
  --detector .local/models/best.pt --detector-sha256 <reviewed-sha256> \
  --ocr .local/bin/owned-ocr \
  --chrome '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
  --rounds 2
python -m phone_lab battle-web --store .local/battles/round-set-001
```

Open `http://127.0.0.1:8767`. The scoreboard reads completed evidence and can
stay open while the worker runs in another terminal. It cannot dispatch actions.
Each pair has the same layout seeds, viewport and frozen detector. One round
uses fixed contacts and one uses declared varied browser dwell/drag settings.
The variation is an experimental input; it is not fitted to blue feedback.
OCR timing and other environmental variation must be reported as confounders.

```text
.local/battles/<round-set>/
  design.json                  frozen trial settings and source/model hashes
  rounds/01-fixed/              captures, policy actions, independent outcome
    blue_inputs.jsonl           provider-only packet, separate from labels
  rounds/02-varied/
  battle_runs.jsonl             blue scores joined with task outcomes
  dashboard.html               offline scoreboard
  completion.json              actual Toronto start/end receipt
```

Report red completions, wrong actions and refusals alongside blue's flagged
sessions and features. An incomplete task is not a blue victory. A session
without contacts is not evidence of a human or a robot. Frozen rules and model
hashes make future team changes comparable. Human/manual-stylus/accessibility
controls require consent, participant/device/session holdouts and false-positive
analysis before any classifier accuracy claim.

## 4. Commission the gantry and connect the phone

Inventory the actual CoreXY frame, motors/drivers, controller, power supply,
phone mounts, conductive stylus, Z/contact mechanism, camera and stop wiring.
Confirm the controller's identity and documented protocol before opening it.
The existence of a serial port alone does not establish a motion controller.

Verify the stop, endstops, homing directions and limits. Test unloaded motion
within the usable workspace, then the mounted stylus and owned phone under
supervision. Map image pixels through viewport/letterbox inversion and a fitted
device calibration. Validate independent holdout points and an interior safety
margin before contact. Each phone fixture and camera change has its own
calibration identity; stale frames and mismatched devices refuse motion.

Replace fake acknowledgements through the existing typed-intent boundary after
the physical acceptance gates pass. Do not let models issue raw firmware.
Measure actual touch registration, drag continuity, contact force/dwell if
instrumented, travel limits, camera frame age and stop latency. Keep motor and
camera evidence in a lab channel separate from website observations.

The current local app and tests run independently of these physical gates.
Controller identity, physical commissioning, phone capture/calibration and
consented controls remain pending. The old scenario game remains historical.
After the supervised rig passes, collect fresh permitted phone captures and
run matched physical trials. Policy learning can follow a reviewed reward and
replay protocol; the present task runner is a deterministic workflow, not an
accepted reinforcement-learning system.
