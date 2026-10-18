# Primary training benchmark: iPhone sportsbook pages → verified database

Blue creates fictional sportsbook pages and their changes. Red identifies UI,
reads visible data and writes typed observations to a local database. An
independent evaluator measures what was missed, misread, assigned to the wrong
field or stored incorrectly. All fixtures and providers are synthetic.

This becomes the main training target. The existing generic tap/drag/entry
tasks remain navigation and controller tests. Existing OCR and trained detector
tools are starting points; sportsbook extraction and database ingestion are
new work, not accepted capabilities yet.

## Roles and data separation

Blue's page generator owns the seeded layout, fictional provider records,
rendered field borders and expected database state. Its provider truth is
available to training and evaluation, not to red at inference. Blue can create
held-out layouts, occlusions, menus, scroll states and quote updates.

Red receives screenshots, permitted visible identity and the task. Its path is
UI detection → OCR crops → field/row association → typed records → database
transaction. Every candidate record links to screenshot/crop evidence. A
separate evaluator compares the persisted database with expected state after
each frame/update. Blue's contact-pattern observer remains an optional,
provider-only diagnostic; it does not consume generator truth or robot labels.

## 1. Generate realistic iPhone pages deterministically

Start with portrait 390 × 844 CSS pixels, configurable for the actual phone.
Use a status bar, safe areas, fixed navigation, mobile typography, event cards,
market rows, selection buttons, sheets and scroll regions. Measure actual
rendered borders; do not infer ground truth from a screenshot detector.

Use three fictional provider themes. Generate events, participants, start
times, market/period, selection, signed line, odds format/value, quote timestamp
and open/suspended status. Begin with decimal odds, then add American odds as
a separately scored format. Include values that expose decimal/sign mistakes,
truncated names, similar rows, dark/light themes and asynchronous updates.
Generate old/new frames for known quote changes and status transitions.

Version the generator, schemas, fonts, renderer/runtime and seed recipe. Record
the actual browser version with every acquisition. Seeds alone do not guarantee
pixel equivalence after a renderer change. Split whole layout families, event
sessions and update sequences; group devices/fonts/providers deliberately.
Retain unseen provider/layout/device combinations as the final holdout.

```text
.local/sportsbook-data/<dataset-id>/
  spec.json                    generator + renderer + seed + schema versions
  images/{train,val,test}/     iPhone page states and update sequences
  annotations/                field roles, text, row relations, pixel borders
  labels/                     detector labels
  provider-truth/              expected snapshots; evaluator/training only
  manifests/                  IDs, hashes, provenance, grouping and tags
```

## 2. Record confusion and misses for every identification operation

Define a versioned operation registry instead of one aggregate accuracy:
identify provider/event/market/selection; locate odds/line/time/status fields;
read each field; associate fields with rows; navigate/scroll; create/update
records; reject incomplete/ambiguous observations. Every registered operation
has counts for correct, missed, wrong, ambiguous, refused and not applicable.

For detection and categorical identification, save machine-readable confusion
matrices with expected class on rows and predicted class on columns. Match
boxes one to one using a fixed overlap rule independently of predicted class.
A missed object maps to background; an unmatched prediction maps from
background. Wrong-class matches remain confusions. Background/background is
not a measured true-negative count, and should not inflate accuracy.

For each role/operation, save precision, recall, support and failure rate.
Rank failures by count, rate and downstream harm; show both numerator and
denominator so a rare class is not hidden by common buttons. Numeric odds and
lines also need exact value/error metrics; an arbitrary-value confusion matrix
cannot describe decimal/sign correctness adequately.

```text
.local/training/<run-id>/evaluations/<checkpoint>/
  operation_registry.json
  confusion/<operation>.json   counts and class ordering
  confusion/<operation>.png    readable heatmaps
  per_operation.csv           support, precision/recall, misses/refusals
  failures.jsonl              expected/predicted, stage, IDs and evidence
  examples/                   missed crops and border overlays
  summary.json                largest losses, coverage, downstream impact
```

Each failure references dataset/split, provider/layout/session/frame, model and
OCR/parser versions, expected/predicted roles and values, coordinates, overlap,
confidence and resulting database error. Save reports during validation and at
every candidate checkpoint. Keep training losses and evaluation results
separate. Preserve negative runs and rejected records.

## 3. Score OCR and structured extraction separately

Keep the existing owned OCR implementation as the first baseline. Score
character/word errors and exact fields by type: names, odds, signed lines,
timestamps and status. Report raw recognition and declared normalization
separately. A tiny overall character error can still corrupt a price.

Detect structural regions, OCR their crops, then associate text and values with
the correct event/market/selection. Save the association errors separately from
OCR errors. The first parser uses explicit schemas and documented rules, with
rejection for missing, conflicting or low-confidence evidence.

Store decimal prices and signed lines as exact decimal strings or scaled
integers, never binary floating-point approximations. Preserve the original
odds format and OCR text. Parse displayed timezone/time explicitly; ambiguous
time is a refusal. Suspended rows and unchanged quotes are real states, not
missing data or defaults.

## 4. Measure actual database updates

Use SQLite initially. Keep providers, events, markets and selections separate
from append-only quote observations and the latest accepted state. A candidate
observation includes provider/event/market/selection identity, period, signed
line, odds format/value, status, provider time, capture time, screenshot hash,
field evidence and model/parser versions. Expected provider records remain in
a separate evaluator store.

Read the database after each ingestion transaction. Measure:

- Row precision/recall and exact complete-record accuracy.
- Exact odds, signed line, status and timestamp accuracy by field.
- Wrong event/market/selection associations and unsupported writes.
- Duplicate records, idempotency on replay, stale updates overwriting newer
  quotes, partial transactions and incorrect suspension/absence handling.
- Complete update-sequence accuracy, rejection coverage and time to accepted
  fresh state.

A correct in-memory JSON object is not a passed database update. A rejected
record is retained and scored as reduced coverage; it does not count as a
correct stored row. Missing or occluded rows must not silently delete prior
state. Replaying the same accepted capture should leave the database unchanged.

Primary scoreboard: **correct records stored / expected records**, alongside
wrong writes, missing records and stale/duplicate violations. The stage reports
attribute each loss to detection, OCR, association, validation or persistence.
Acceptance must include hand-checked cases, ambiguous rows, price changes,
suspensions, out-of-order frames, duplicate replay and transaction failures.

## 5. Train the part that evidence shows is weak

Train detection/localization and OCR recognition as separate components when
needed. Field association may use a small text/layout model. First collect
paired OCR/layout → expected typed records and benchmark the rule parser.

A lightweight LLM is a later candidate for association/structured extraction if
OCR is already accurate and relationship mistakes dominate. Require schema
validation and evidence for every numeric field. It must be able to abstain;
it cannot repair odds by guessing. Compare it against the rule parser on the
same frozen inputs, database tests, latency and memory. Verify model access,
license and hardware before training or fine-tuning. No size/performance claim
is accepted without a measured run.

Mine difficult examples from the training/development partition and generate
new seeded cases there. Retain every dataset/model/report version. Do not turn
an inspected final holdout into training data while still calling it unseen.
If it is used for improvement, retire it and create a new untouched holdout.

## Ordered implementation and acceptance

1. Freeze provider/annotation/record schemas, operation registry and the iPhone
   page recipe; create hand-checked golden fixtures and update sequences.
2. Extend the deterministic curator with sportsbook pages, renderer provenance,
   tags/borders and leakage-checked splits. Verify repeated export bytes.
3. Implement per-operation confusion/miss reports and evidence crops; verify
   hand-calculated wrong-class, missed, duplicate and unmatched cases.
4. Run detector + OCR + typed parser into SQLite. Test persisted records,
   decimal/sign errors, entity joins, replay, stale updates and atomicity.
5. Train a bounded baseline and save checkpoint reports. Rank losses; improve
   detection, OCR or association according to evidence. Evaluate a small LLM
   only against the existing baseline and explicit record contract.
6. Add navigation and gantry interaction after static page ingestion works.
   Keep existing calibration/freshness/stop fences; physical commissioning and
   consented human/accessibility controls remain separate pending gates.

This is the implementation plan for the active goal. Phone lab 0.5 implements
fictional iPhone provider pages, actual-renderer dataset export, typed SQLite
ingestion, OCR-only association, persisted scores, error crops and association
confusion matrices. The initial 21-page development run stored 12 of 28 final
records exactly; failed updates and missing records remain in the evidence.
The first scorer incorrectly counted equivalent dash glyphs as OCR errors;
that version is retained and the corrected scorer has a regression test.

Expanded-role detector training and its pixel-only identification matrix are
still pending. OCR field association does not measure detector accuracy.
Next, train the detector baseline and isolate OCR recognition errors in event
IDs, headings and numeric fields. Fine-tuning a small LLM is conditional on
accurately recognized text still producing association errors. Keep static
database ingestion ahead of navigation and physical gantry commissioning.
