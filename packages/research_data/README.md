# Research data

Independent immutable snapshot catalog, chronological tennis baselines and exact payoff calculations for the phone research project. Raw/derived data stays in a separately configured ignored research store, with source, permission/license, hash and time metadata. This package contains code and generated tests only.

From this directory run `uv sync --locked --group dev`, `uv run pytest`, Ruff and Pyright. Generated paper cases do not establish live execution or profitability.

For an already acquired tennis CSV, run the outcome baseline with its reviewed hash:

```sh
uv run python -m research_data.paper /path/to/snapshot.csv \
  --source /path/to/source.json --sha256 VERIFIED_SHA256 \
  --holdout-start 20241001 --availability-days 21 \
  --output /path/to/new-private-report.json
```

The source JSON must contain exactly `dataset_id`, `source_url`, `provenance`,
`license_status`, `fetched`, `published` and `observed`. Use a credential-free HTTPS
URL, retain the actual license-review status, and give offset ISO timestamps or
explicit `unknown` values. Acquisition time and unknown publication time remain
separate from the evaluator's conservative tournament-start availability assumption.

Input bytes must match the reviewed SHA256 and pass bounded, strict UTF-8 CSV parsing.
The report uses only player identity and eligible prior outcomes; extra statistics and
unvalidated odds columns do not enter the model. Ratings stay frozen during the holdout.
Reports are deterministic, created with private permissions, and never overwritten.
Record actual execution times separately. Empty training/holdout splits refuse a report.
Keep source snapshots, license receipts and reports in the private research store;
`.local/` is ignored for experiments inside this package. Price/execution validation,
distribution approval and trading-return claims remain outside this outcome diagnostic.
