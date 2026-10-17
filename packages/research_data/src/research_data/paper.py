"""Deterministic, outcome-only reports from caller-acquired tennis CSV snapshots."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from research_data.catalog import MAX_BYTES, _canonical_source_url, _shape, _time, _token
from research_data.tennis import evaluate

SOURCE_FIELDS = frozenset(
    {"dataset_id", "source_url", "provenance", "license_status", "fetched", "published", "observed"}
)
OUTCOME_FIELDS = frozenset(
    {"tourney_id", "tourney_date", "match_num", "winner_id", "loser_id", "score"}
)


def tennis_report(
    data: bytes,
    *,
    expected_sha256: str,
    source: Mapping[str, Any],
    holdout_start: str,
    availability_days: int = 21,
) -> dict[str, Any]:
    """Verify source bytes, preserve provenance, and reuse the frozen Elo evaluator.

    Acquisition/publication metadata is separate from tournament start dates.
    License metadata never grants distribution or execution rights. Timestamps
    of this program's execution belong in the caller's journal, not stable bytes.
    """
    if not isinstance(data, bytes) or not data or len(data) > MAX_BYTES:
        raise ValueError("nonempty bounded CSV bytes required")
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("reviewed lowercase SHA256 required")
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise ValueError("snapshot digest mismatch")
    if not isinstance(source, Mapping) or set(source) != SOURCE_FIELDS:
        raise ValueError("exact source provenance fields required")
    for name, limit in (
        ("source_url", 2048), ("fetched", 128), ("published", 128), ("observed", 128)
    ):
        if not isinstance(source[name], str) or len(source[name]) > limit:
            raise ValueError(f"bounded {name} required")
    metadata = {
        "dataset_id": _token(source["dataset_id"], "dataset_id"),
        "source_url": _canonical_source_url(source["source_url"]),
        "fetched": _time(source["fetched"]),
        "published": _time(source["published"]),
        "observed": _time(source["observed"]),
    }
    for name, limit in (("provenance", 2048), ("license_status", 128)):
        value = source[name]
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ValueError(f"bounded nonblank {name} required")
        metadata[name] = value
    if type(availability_days) is not int or not 0 <= availability_days <= 3650:
        raise ValueError("availability_days must be within zero and 3650")
    shape, row_count = _shape(data, "csv")
    if not OUTCOME_FIELDS <= set(shape["fields"]):
        raise ValueError("required tennis outcome columns missing")
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True))
    baseline = evaluate(rows, holdout_start, availability_days)
    if not baseline["counts"]["train"] or not baseline["counts"]["test"]:
        raise ValueError("baseline requires training and heldout outcomes")
    return {
        "schema": "tennis-paper-report/1",
        "source": metadata | {"sha256": digest, "bytes": len(data), "rows": row_count},
        "recipe": {
            "parser": "strict-utf8-csv/1",
            "model": "frozen-training-Elo/1",
            "k": 20,
            "features": "provider player identity and prior eligible outcomes only",
        },
        "baseline": baseline,
        "scope": "retrospective outcome diagnostic; source publication timing may be unknown",
        "market_prices_used": False,
        "price_and_execution_validation": "not performed",
        "live_execution": False,
        "distribution_rights_approved": False,
    }


def _read_regular(path: Path, limit: int) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError("bounded regular input file required")
        data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError("input size limit exceeded")
        return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--holdout-start", required=True)
    parser.add_argument("--availability-days", type=int, default=21)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError("new immutable report output required")
        source = json.loads(_read_regular(args.source, 64 * 1024))
        report = tennis_report(
            _read_regular(args.input, MAX_BYTES),
            expected_sha256=args.sha256,
            source=source,
            holdout_start=args.holdout_start,
            availability_days=args.availability_days,
        )
        payload = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except (ValueError, OSError) as exc:
        parser.exit(2, f"paper baseline refused: {exc}\n")
    print(json.dumps({"output": str(args.output), "counts": report["baseline"]["counts"]}))


if __name__ == "__main__":
    main()
