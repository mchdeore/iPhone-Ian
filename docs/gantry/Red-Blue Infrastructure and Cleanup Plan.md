# Red/blue infrastructure, optimization and cleanup

Further training is held at the user's request. Continue infrastructure,
verification and design work. Do not start a training job, fine-tune a model,
download a candidate model or schedule training while this hold is active.
The completed development baseline and its checkpoints remain preserved.
Existing-model inference and deterministic fixture verification are separate
operations; they must never silently trigger training.

## Keep the shared workspace intact

Protect `Gantry Vision Roadmap.canvas`, every other `.canvas`, `.obsidian/`,
the red/blue board and all linked notes/images/attachments. The shared local
canvas and published canvas are different valid versions: preserve both and
their history. Do not rebuild, rename, overwrite or automatically reconcile
them during infrastructure or cleanup work.

Protect `research/`, including
`research/Projects/Program Plan — Gantry Vision and Red-Blue Research.md`,
the existing red/blue build plans, diagram originals, proposals, source data,
checkpoints, error evidence and restore receipts. Keep the existing local
red/blue dashboard and its matched-round artifacts. These are retained project
work, even where an item was generated. Keep CRAFT outside this work.

## Team workflow and boundaries

The shared Obsidian canvas/board remains the planning surface. The local web
apps provide execution views and refer to the same stage names:

1. **Blue prepares a challenge.** Choose a fictional provider, seeded event
   sequence and layout recipe. Export immutable screenshots, component/text
   borders, tags, golden records and update history. Preview and review them
   in the curator. Freeze a challenge version before a round starts.
2. **Red receives pixels.** Supply an opaque capture ID and PNG. Red must not
   receive DOM labels, provider truth, fixture seeds, split labels or hidden
   database contents. Existing OCR/model adapters may produce observations
   or action intentions; no training starts from this view.
3. **The coordinator records attempts.** Capture, actor/parser/model versions,
   confidence, latency, accepted/rejected rows and refusal codes belong in an
   append-only run ledger. An empty/refused extraction still counts as an
   attempted capture. Retries receive explicit attempt identities.
4. **The evaluator scores persisted state.** Reopen SQLite and compare its
   expected latest state. Keep wrong, missing, unexpected and stale records
   separate. Explain cumulative scores separately from final-state accuracy.
   Join expected truth only after actor observations are saved.
5. **Blue scores provider-visible behavior.** Freeze its detector/rule version
   before a match. Feed only permitted app-input/provider telemetry. Exclude
   evaluator labels, model output, camera/motor state and hidden ground truth.
   Retain fixed/varied-contact matched rounds and failed/refused rounds.
6. **Both teams inspect the round.** Show data quality, task completion,
   database accuracy, provider flags and failures separately. A flag is an
   experimental signal; consented human controls are still required before
   claiming reliable bot detection. Physical gantry gates remain separate.

Use separate Blue and Red HTTP surfaces locally. The Red image service has
no annotation, source-page or truth routes. This separation constrains the
actor interface; production access control still needs authenticated,
per-round capabilities and isolated artifact mounts. Do not present a local
interface split as production security.

## Infrastructure implementation order

The 0.6 foundation enforces the training hold, supplies separate Blue and Red
local services, and records a frozen round with opaque captures and atomic
attempt/quote writes. It retains empty/refused attempts, explicit retries,
conflicting submissions and stale history. Blue evaluates committed SQLite
state afterward and preserves the score's attempt snapshot. These round
scores aggregate saved quotes; candidate comparisons need separate round
databases until per-actor scoring is implemented. Manual coordination tests
are not model accuracy or physical gantry validation.

The 0.7 foundation adds Blue provider pointer-contact sessions, frozen scorer
source fingerprints, immutable contact/score history and explicit links to
saved attempts on the same capture. Supported earlier rounds migrate
transactionally; their old attempts have no retroactive behavior score.
The collector exports only pointer timing and geometry. Browser-trusted events
do not establish a human, and the rules apply no sanctions.

The following list remains the full infrastructure checklist. Isolated Red
browser action execution, broader input/navigation workflows, job control,
per-actor comparisons and authenticated deployment remain pending. The Obsidian
planning surfaces stay unchanged.

- Enforce the training hold before dataset access, output creation or model
  loading. Show its status in the execution views; provide no automatic or
  in-page training bypass.
- Preserve the current typed provider/SQLite contracts and deterministic
  artifact export. Add a Red pixel-input service beside the Blue curator.
- Add explicit run/capture/attempt contracts and a transactional coordinator
  ledger. Record empty/refused attempts, replay, conflicting submissions and
  stale updates. Avoid partial quote/attempt commits.
- Connect provider-visible action logging and the frozen Blue scorer to that
  ledger. Keep scene truth and behavior scoring on separate paths.
- Make the execution board readable: Blue preparation, Red attempt, scoring,
  and review; compact status cards, per-round history and drill-down crops.
  Keep detailed model/debug data behind the review view.
- The Blue queue controls dataset capture and native OCR evaluation with one
  active leased child, durable progress, cancellation and new-run restart.
  Frozen source/executable/dataset identities and hashed artifacts remain
  recorded; interrupted and failed outputs are preserved. The child retains
  its lease after supervisor death. Execution success is separate from OCR
  and database accuracy. Training jobs remain disabled.
- Connect typed Red action intentions to an isolated software browser executor
  on the Blue page. Return fresh pixels to Red without DOM/fixture access;
  record actual provider input separately from requested action intentions.
  Link those windows explicitly to navigation/extraction attempts. Preserve
  failures and refusal outcomes before reading evaluator truth. Extend the
  pages' keyboard/scroll/navigation behavior before claiming broader workflows.
  The local coordinate console now provides the first executor milestone:
  real Chrome navigation/price refresh, committed PNGs, stale/refused actions,
  replay and retained trusted contacts. Persistent supervised sessions, actor
  database submissions and web-surface integration remain open. Local console
  isolation does not establish an OS sandbox or authenticated team deployment.
- Verify end-to-end local rounds with scripted/manual observations and
  existing inference. Label stand-ins explicitly. Do not imply a newly trained
  model, connected gantry or human-validated detector.

## Optimization design before training resumes

Measure one stage at a time: rendering/capture, UI localization, OCR reading,
field association, parsing, database commit and final verification. Keep the
six-operation registry and extend OCR coverage to format/column headings,
which can reject entire pages even when record-field text is readable.

Save confusion matrices, class support, missed/duplicate/wrong detections,
OCR character/field errors, refusal codes and persisted record errors. Count
unmeasured operations explicitly. Retain original screenshots, pixel/model
hashes and failure crops. Rank class-balanced misses so frequent odds fields
cannot hide missing event IDs, timestamps or navigation.

Before later model selection, define the objective at the intended confidence
gate: class-balanced recall, false identification/association rates and exact
persisted records. Keep default trainer mAP as a diagnostic. A high precision
on one detected box is not coverage of an entire page.

Plan improvements around observed failures: more varied seeded records and
provider layouts; small-region localization/letterboxing; OCR language and
candidate evidence; crop/scale preprocessing; and deterministic association
from observed headings. Compare preprocessing to the existing baseline on
development data and retain negative results. Never repair ambiguous prices,
signs, event IDs or timestamps by guessing.

Consider a small extraction LLM only when OCR text is accurate and association
still fails. Keep typed validation and independent database scoring around it.
Model/access/license/hardware review and explicit permission to resume
training precede any fine-tuning. Retire inspected holdouts and freeze new
provider/layout/event groups before any final evaluation.

For responsiveness, bound CPU work and queues, reuse reviewed inference
processes, avoid duplicate capture/encoding, cache only by complete artifact
identity, stream compact progress, and set frame/latency budgets. Every cache
or speed change must preserve borders, confidence and stale-frame gates.

## Cleanup pass: plan only

No deletion, repository archival or worktree removal is authorized by this
planning request. Use the existing consolidation plan for the broader repo
inventory, preservation, dependency and privacy requirements.

1. Inventory source, local worktrees, generated artifacts, environments,
   exports and Obsidian links. Mark every item keep, investigate or candidate.
   Active/dirty/shared checkouts and unknown ownership default to keep.
2. Build a protected-file register with hashes and consumers. Include both
   canvas versions, `.obsidian/`, the red/blue board/notes, linked assets,
   diagram originals, databases, model/dataset versions and needed history.
   Follow links before considering their targets for cleanup.
3. Identify genuine clutter: duplicate verified restore clones, superseded
   build products, orphan temporary renders, caches and unused environments.
   A filename or old timestamp is insufficient evidence of disposability.
4. Preserve and independently restore every candidate's needed source,
   valid refs, dirty files and selected ignored artifacts. Keep sensitive
   history/originals local; upload only reviewed sanitized source when allowed.
5. Prepare an exact move manifest for eligible inactive owned duplicates into
   dated subfolders of `/Users/cheddar/Developer/delete`. Include original
   path, consumer changes, bytes/hashes, reason and exact restoration command.
   Perform no moves during this planning pass and no permanent deletion.
6. Before a later cleanup execution, verify the protected register, Obsidian
   canvas/board opening and links, app startup, dataset/database reads and
   project tests. Preserve old paths until their consumers are safely updated.
7. After any separately authorized cleanup, repeat those checks and verify a
   fresh restore from quarantine. Report retained exceptions and missing
   access; never infer that a missing or uninspected item can be removed.

Acceptance requires byte preservation of the shared canvas and board, working
links/assets, recoverable history, working local execution views and no
stranded source or data. Cleanup success is reduced verified duplication,
not a target amount of disk space deleted.

## Standalone delivery and rendering checks

Keep all app, dataset, SQLite, evaluation and OCR source in iPhone-Ian's
`packages/phone_lab`. Its pinned Python dependencies, operator-supplied Chrome
and Apple Vision/Swift are the only required software surfaces for local
browser/OCR checks. Do not introduce cross-repository paths, services,
credentials or symlinks. Test a fresh source copy and an independently
installed wheel; compile OCR from the included Swift source. Generated data
and compiled binaries stay local and ignored. Training remains held.

Capture the actual actor PNG and retain renderer/version/platform context.
Verify repeated captures, field text crops and border geometry separately
from whole-image pixel equality. Decorative antialiasing differences remain
recorded evidence even when all field crops and borders agree. A successful
single-page OCR/database check is infrastructure evidence; broader provider
coverage, navigation, actor comparisons and physical operation remain gates.
