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

The render harness alone receives labels and DOM measurements. A future vision policy receives
pixels and visible frame identity. The generated dataset is not a real-phone holdout. Real capture,
calibration, human/accessibility consent and hardware acceptance are separate gates.

Session capabilities are stored separately in a restricted credential directory and
excluded from evaluator/run evidence. Schema-1 experimental logs remain historical
copies; start a new schema-2 runtime rather than overwriting or silently migrating them.

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
