# Owned phone lab

A local mobile benchmark with tap, drag, numeric entry, menu, overlay and scroll tasks.
It uses generated inputs. Browser observations establish outcomes; a policy's success flag
is refused. No physical serial driver, external website automation or financial execution is enabled.

Install with Python 3.12 and `uv sync --extra test`. Start an owned generated task with
`uv run python -m phone_lab serve`. Operator/evaluator keys live only in the restricted
runtime directory. Use one server process. Raw events, captures and datasets belong in ignored storage.

Create actual browser screenshots with `uv run python -m phone_lab dataset .local/datasets/run-1
--browser-executable /path/to/chrome`. Seeds control layouts, fonts and themes. The manifest records
measured browser boxes, pixel hashes, generated device/session identity and disjoint font/layout/device
groups. `uv run python -m phone_lab audit .local/datasets/run-1` fails on group leakage, changed bytes
or the declared near-duplicate proxy. Inspect flagged examples before training.

The render harness alone receives labels and DOM measurements. The trained vision policy receives
pixels and visible frame identity. The generated dataset is not a real-phone holdout. Real capture,
calibration, human/accessibility consent and hardware acceptance are separate gates.

Session capabilities are stored separately in a restricted credential directory and
excluded from evaluator/run evidence. Schema-1 experimental logs remain historical
copies; start a new schema-2 runtime rather than overwriting or silently migrating them.

## Red / blue app and dataset workflow

Version 0.4 adds an immutable synthetic dataset curator and a read-only battle
scoreboard. The [end-to-end proposal](../../docs/gantry/End-to-End%20Proposal.md)
and [Obsidian canvas](../../Gantry%20Vision%20Roadmap.canvas) connect these to the
gantry build and model training stages.

```sh
uv run python -m phone_lab data-web --store .local/synthetic-data \
  --browser-executable '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
```

Open `http://127.0.0.1:8766`. Choose seeds, tags and viewport, then generate a
dataset. Inspect measured borders, filter task/split, and download annotations
and manifests. Sample IDs derive from generator source, sorted seeds/tags,
viewport, task and phase. Files live under `images/`, `labels/` and
`annotations/`, each split into train/val/test. The catalog verifies every
image, label and annotation hash on read. Matching browser/render environments
are necessary for identical pixels. New tags create a new dataset version.

Run a matched pair using the separate vision environment, reviewed checkpoint
and the compiled `tools/owned_ocr.swift` binary:

```sh
python tools/owned_battle.py .local/battles/pair-001 \
  --detector .local/models/best.pt --detector-sha256 <reviewed-sha256> \
  --ocr .local/bin/owned-ocr \
  --chrome '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
  --rounds 2
python -m phone_lab battle-web --store .local/battles/pair-001
```

The scoreboard is at `http://127.0.0.1:8767`, with an offline copy in the round
directory. Run the worker and scoreboard in separate terminals to see completed
rounds appear. Fixed and declared varied contacts share layouts and model
hashes. Blue scores narrow provider packets before independent outcomes are
joined. Its frozen dwell/path flags are descriptive hypotheses. Consented
human/control validation and physical gantry commissioning remain pending.

The worker preserves captures, refusals, source/model hashes and actual Toronto
timestamps. It requires a new output directory and bounds rounds/timeouts.
Generated keyboard/wheel/contact timings and fake motor acknowledgements do
not establish physical phone performance. Evaluator boxes, camera/motor traces,
entered text and capability tokens are excluded from blue packets.

Test with `uv run pytest -p no:cacheprovider`. The browser tests require an actual Chrome executable;
missing browser tests are skipped explicitly. All six tasks also have independent event-level tests.

Keyboard controls work on the owned benchmark: Tab moves focus; Enter activates a button.
For drag, press Enter on Grip, then Tab to Goal and press Enter. Numeric entry and PageDown
on the list use the same browser-observation evaluator. Zoom and visible focus remain available.
These generated checks are not a consented participant study.

`phone_lab.control` provides affine calibration with independent holdout checks, inverse
letterbox mapping, typed tap/drag intentions, frame/device/calibration fences, one-use arm
tokens, inset limits, stop, restart refusal and deterministic replay. It only accepts
`FakeSerial`; no physical serial driver exists. Coordinates and acknowledgement results are
generated evidence. Actual homing, force, pressure, controller and phone calibration remain untested.

`phone_lab.workflow` saves immutable hashed captures and append-only run evidence. Its CPU
border detector consumes pixels only and returns unclassified, non-actionable candidates.
Website observations summarize contact, timing and outcomes; motor/camera/hover fields
do not enter that summary. Consent references are required for real participant cohorts.

The initial generated detector fixture uses button, field, handle, destination and list
roles. Field corresponds to a text input; handle to a drag grip. Destination and list are
regions, not generic tap permissions. This subset does not cover the proposed checkbox,
radio, toggle, menu-item, dialog-close or actionable-icon taxonomy. OCR and disabled,
occluded or ambiguous states need separate acceptance before any vision-guided action.

Generated capture recipe 3 waits for fonts and paint, uses Chrome software compositing,
and requires two consecutive identical PNG captures. Older experimental recipes are
retained; the current audit requires a new recipe-3 dataset. Inspected generated splits
serve development only and do not replace an untouched real-phone test set.

The optional `requirements-vision.txt` environment runs a pinned CPU YOLO11n experiment.
`tools/vision_pilot.py` audits a frozen dataset, proves an isolated optimizer step, measures
the unchanged checkpoint, trains at most 50 epochs, evaluates and exports FP32 ONNX with
raw-output parity checks. It records actual environment, license and checkpoint hashes.
Ultralytics is AGPL-3.0; distribution/service obligations and weight terms remain a
separate gate. CUDA/GTX1080, MPS, quantization and real-phone results are not implied.

On macOS, compile `tools/owned_ocr.swift` with `swiftc` to use installed Vision OCR on
owned PNGs. `tools/owned_policy_smoke.py` uses pixels/OCR and visible frame identity on
the generated site, with fake motor intents and independent browser outcomes. Missing,
ambiguous or stale candidates stop. Its generated scroll wheel is a stand-in, and its
results do not certify physical gestures or an external website policy.

For a trained local detector, create a separate Python 3.12 environment with
`uv venv .local/vision-env --python 3.12` and install `requirements-vision.txt`
using `uv pip install --python .local/vision-env/bin/python -r requirements-vision.txt`.
This environment uses the pinned NumPy 1.26 research stack. From this package directory:

```sh
PYTHONPATH=src .local/vision-env/bin/python tools/owned_policy_smoke.py .local/workflows/run-1 \
  --ocr /path/to/compiled/owned-ocr --chrome /path/to/chrome \
  --detector /path/to/owned/best.pt --detector-sha256 VERIFIED_SHA256
```

Replace `VERIFIED_SHA256` with the reviewed training artifact's hash. The same flag
accepts its FP32 ONNX export. Each run requires a new directory and records detector,
OCR binary, environment, stable capture and timing evidence. Warm-up happens before
frame capture. Both engines receive explicit 640-square inputs; boxes return to screen
coordinates using the actual rounded padding. ONNX thread defaults are recorded separately.

Button selection combines detector class/confidence with OCR inside the box. Its score
is the minimum of detector confidence, OCR confidence and normalized label similarity;
small OCR errors reduce that score. Region selection requires a unique supported class.
Scores below 0.9, ambiguous candidates, malformed boxes and stale frames refuse actions.
These development scores need calibration on real devices. Independent site outcomes
and refusals remain visible in `result.json`; numeric insertion and scrolling use generated
browser stand-ins. Model files, workflow captures and private runtime data stay ignored.


## Fictional sportsbook lab (0.7)

**Training is held.** Prepare infrastructure and evaluate existing artifacts;
do not start training, fine-tuning or new model downloads. The training entry
point fails closed before model loading or output creation. Both team views
show the saved hold policy. Re-enabling training requires a later explicit
human instruction; there is no web toggle.

`phone_lab.sportsbook` generates three fictional providers in a 390×844 iPhone
viewport. It exports PNGs, component/text borders, YOLO labels, typed provider
truth, source pages and deterministic tags. Sample identities include actual
renderer/version/platform, generator hashes and every output digest. The audit
checks source bytes and keeps provider layouts and event sequences apart.
A test split is generated development data until an untouched evaluation is
explicitly frozen; seed values alone do not guarantee identical pixels.

From this package directory:

```sh
uv run tools/owned_sportsbook.py generate --output .local/sportsbook/dataset-1 \
  --chrome "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
swiftc tools/owned_ocr.swift -o .local/owned-ocr
shasum -a256 .local/owned-ocr
uv run tools/owned_sportsbook.py evaluate --dataset .local/sportsbook/dataset-1 \
  --output .local/sportsbook/evaluation-1 --ocr .local/owned-ocr \
  --ocr-sha256 SHA_FROM_REVIEWED_BINARY
uv run tools/owned_sportsbook.py serve --dataset .local/sportsbook/dataset-1 \
  --reports .local/sportsbook/evaluation-1/reports --port 8768
```

Open `http://127.0.0.1:8768` for page previews, tags, border overlays and saved
training errors. Existing dataset/evaluation directories are never overwritten.
The recognizer receives PNGs. The parser receives only OCR text/confidence/boxes;
evaluator truth is read after actor observations and database writes are saved.
Typed decimal/sign/UTC contracts reject ambiguity. SQLite preserves quote history,
refuses conflicting replay, ignores older updates for latest state, and commits
batches atomically. No sportsbook accounts, bets or physical controller are used.

The six-operation registry separates UI identification, OCR reading, field
association, quote parsing, storage and final verification. Reports keep
per-role OCR misses/edit counts, class-independent association confusion,
per-frame refusals, error crops and persisted record/field errors. Final accuracy
reopens SQLite and compares the full expected latest state. Cumulative capture
scores repeat earlier records and are displayed separately. Missing roles have
explicit support; background true negatives remain unmeasured. The expanded
pixel-only detector and any OCR/LLM fine-tuning remain pending; successful report
generation does not establish training accuracy.

Run separate local team surfaces with the same owned round database:

```sh
uv run tools/owned_sportsbook.py serve --dataset .local/sportsbook/dataset-1 \
  --surface blue --arena .local/sportsbook/round-1.sqlite --port 8768
uv run tools/owned_sportsbook.py serve --dataset .local/sportsbook/dataset-1 \
  --surface red --arena .local/sportsbook/round-1.sqlite --port 8769
```

Blue's curator retains provider previews, tags and border overlays. `/arena/`
shows saved attempts and evaluates the database separately. Red receives
opaque capture identities, image hashes and PNGs, with no annotation, provider
preview, report or evaluator routes. Its console can save a manually authored
observation or an empty/refused attempt. Manual entries verify coordination;
they do not demonstrate model accuracy. Red's API acknowledges saving only;
it never returns golden data or a database score.

Attempts preserve actor/parser/model identity, latency, pixel commitment,
refusals and retry references. Identical submissions replay without duplicating
history; conflicting replay fails. Another attempt by the same actor on the
same capture requires an explicit `retry_of`. A refused quote batch rolls back
all its quote writes while retaining the attempted payload and reason. Older
updates remain in observation history without replacing newer values. Empty
and refused attempts count toward expected database coverage. Scoring reopens
SQLite after submissions commit and stores its attempt snapshot. Current
scores aggregate the round's saved quotes; use separate round databases for
candidate comparisons rather than treating aggregate scores as actor scores.

These are separate local interfaces, not authenticated shared hosting.
Isolated actor comparisons and per-round deployment capabilities are the
next infrastructure steps in
`docs/gantry/Red-Blue Infrastructure and Cleanup Plan.md`. Protect the shared
Obsidian canvas, all `.canvas` files, `.obsidian/`, red/blue board, research notes
and linked assets. Cleanup is planned only; no moves or deletions run here.

Blue's round review now starts **provider contact sessions** on a frozen
fictional page. The phone frame observes trusted browser pointer events and
exports only kind, time, x/y and contact slot. It exports no entered text,
field labels, model predictions, camera or motor state. Browser trust here
describes the event source; it does not establish a human operator. Session
timestamps come from the browser's event clock, independently of the fake
provider's displayed quote times.

The round freezes the exact descriptive Blue scorer/protocol/helper source
hashes before new sessions. New scoring refuses source drift; saved scores
remain readable. Contact packets and scores are immutable, replay is explicit,
and cancelled/empty sessions remain visible. Link a closed session explicitly
to a saved attempt on the same capture. Database accuracy and behavior flags
remain separate outcomes. The rules describe short/regular dwell and straight
paths; robot probability is unmeasured, consented human/accessibility controls
are pending, and no sanctions apply.

Arena schema 2 transactionally adds provider session/link history to supported
schema-1 rounds. Existing quotes, attempts, challenge IDs and evaluations remain
intact; prior attempts do not receive retroactive behavior measurements. Back
up an owned live database before upgrading. Malformed or unsupported legacy
tables are refused unchanged. This collector currently measures pointer
contacts. Broader keyboard/scroll workflows, isolated Red browser action
execution and authenticated shared hosting still need infrastructure work.

Blue can enable **dataset and evaluation jobs** from this package directory:

```sh
uv run tools/owned_sportsbook.py serve --dataset .local/sportsbook/dataset-1 \
  --arena .local/sportsbook/round-infrastructure-1.sqlite --surface blue \
  --jobs .local/jobs/blue-1 \
  --chrome "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --ocr .local/owned-ocr --ocr-sha256 SHA_FROM_REVIEWED_BINARY --port 8768
```

Open `/jobs/` for seed controls, frozen dataset inspection, progress,
cancel/restart and OCR/database error reports. Red refuses these routes and
executor options. Native OCR is optional for capture jobs; evaluation requires
the reviewed executable and its exact digest. The local runner uses POSIX
file locks on macOS/Linux. It permits one active child and at most sixteen
pending/active jobs, eight seeds per split, a 120-second runtime deadline with
bounded shutdown, a 2 MiB worker log and a 64 MiB accepted-artifact budget.
These are capture/inference jobs; training and fine-tuning remain held.

Requests, source/executable fingerprints, progress and outcomes persist in
SQLite. Import copies only audited dataset files into owned storage. Evaluation
accepts catalog identities, never browser-supplied commands or paths. The child
retains its owner lock if the supervisor exits, preventing duplicate execution;
unfinished jobs become interrupted only after that lock can be reacquired.
Cancelled/failed/interrupted evidence remains in its original run directory.
Restart uses the same frozen request and a new run identity; source drift
refuses execution. Exact replay keys return the original job. Accepted artifacts
are hashed and checked before serving. Successful execution means a valid
export/report, not that the model stored every quote correctly.

The lab stands alone in iPhone-Ian. Install its pinned dependencies with
`uv sync --extra test`; source, generated fixtures, database code and native
OCR source all live in this package. macOS Vision OCR needs the installed
Apple Swift compiler; browser capture needs the Chrome executable passed by
the operator. Neither requires another repository, service or credentials.
Keep generated captures, databases and compiled tools under this package's
ignored `.local/` directory. The Python wheel includes runtime modules and
assets; compile the optional Swift tool from a source checkout.

Record the actual actor PNG and renderer context. Stable field borders and
text crops do not prove whole-image identity: embedded-page compositing can
change decorative antialiasing even when geometry agrees. Compare repeated
captures in the same context and retain full-image differences separately.
