from __future__ import annotations

import hashlib
import json
import math
from html import escape
from pathlib import Path

from PIL import Image

from ..benchmark import Refusal, identifier
from .contracts import FIELDS
from .evaluation import SPORTS_ROLES, _objects, confusion_report, merge_confusions
from .extract import ocr_regions


def operation_registry():
    return {
        "identify-ui": {"metric": "class-independent IoU confusion", "classes": list(SPORTS_ROLES),
                        "boundary": "pixel-only trained detector; OCR field boxes do not measure this operation"},
        "read-text": {"metric": "exact text, missing text, character edit distance by role",
                      "boundary": "evaluator text regions align full-page OCR; localization scored separately"},
        "associate-fields": {"metric": "class-independent IoU confusion",
                             "boundary": "OCR-only field association; participant header is one region"},
        "parse-quote": {"metric": "typed rows and explicit refusals"},
        "store-quote": {"metric": "atomic insert, update, replay and stale history"},
        "verify-database": {"metric": "exact persisted records / expected records; field errors and missing fields"},
    }


def _distance(a, b):
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (x != y)))
        previous = current
    return previous[-1]


def _normalize(value):
    return " ".join("—" if token in ("-", "—", "–", "−") else token.replace("−", "-") for token in value.split())


def score_ocr_fields(truth, recognized, *, minimum_confidence=0.9, coverage=0.25):
    """Evaluator-only alignment, supporting shared and fragmented OCR regions."""
    if not 0.5 <= minimum_confidence <= 1 or not 0 < coverage <= 1:
        raise Refusal("invalid OCR scoring threshold")
    boxes = _objects(truth, SPORTS_ROLES, "text")
    regions = ocr_regions(recognized)
    per_role = {role: {"support": 0, "correct": 0, "missing": 0, "wrong": 0,
                       "characters": 0, "character_errors": 0} for role in SPORTS_ROLES}
    failures = []
    for field, checked in zip(truth, boxes):
        value = field.get("text")
        if not isinstance(value, str) or not 1 <= len(value) <= 1000 or not value.isprintable():
            raise Refusal("bounded expected visible text required")
        expected = _normalize(value)
        box = checked["box"]
        candidates = []
        for region in regions:
            other = region["box"]
            width = max(0, min(box["x"] + box["width"], other["x"] + other["width"]) - max(box["x"], other["x"]))
            height = max(0, min(box["y"] + box["height"], other["y"] + other["height"]) - max(box["y"], other["y"]))
            if region["confidence"] >= minimum_confidence and width * height / (box["width"] * box["height"]) >= coverage:
                candidates.append(region)
        observed = _normalize(" ".join(region["text"] for region in candidates))
        words = observed.split()
        length = len(expected.split())
        windows = [" ".join(words[i:i + length]) for i in range(max(0, len(words) - length + 1))]
        nearest = min(windows, key=lambda text: (_distance(expected, text), text)) if windows else observed
        correct = expected in windows
        errors = 0 if correct else _distance(expected, nearest)
        kind = "correct" if correct else "wrong" if observed else "missing"
        stats = per_role[checked["role"]]
        stats["support"] += 1
        stats[kind] += 1
        stats["characters"] += len(expected)
        stats["character_errors"] += errors
        if not correct:
            failures.append({"kind": kind, "id": checked["id"], "role": checked["role"], "box": box,
                             "expected": expected, "observed": observed, "compared": nearest,
                             "character_errors": errors, "ocr_ids": [r["id"] for r in candidates]})
    for stats in per_role.values():
        stats["accuracy"] = stats["correct"] / stats["support"] if stats["support"] else None
    totals = {key: sum(stats[key] for stats in per_role.values())
              for key in ("support", "correct", "missing", "wrong", "characters", "character_errors")}
    return {"schema": "sportsbook-ocr-score/1", **totals, "per_role": per_role, "failures": failures,
            "minimum_confidence": minimum_confidence, "overlap_coverage": coverage,
            "normalization": "whitespace and typographic minus/dash only; case and digits remain exact",
            "matching": "evaluator text-box overlap; contiguous token window; shared regions allowed"}


def _heatmap(report):
    classes, matrix = report["classes"], report["matrix"]
    size, margin = 36, 120
    width = margin + size * len(classes) + 20
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{width}" role="img" aria-label="Expected rows and predicted columns">',
                '<rect width="100%" height="100%" fill="white"/>']
    maximum = max(1, *(value for row in matrix for value in row if value is not None))
    for i, name in enumerate(classes):
        elements.append(f'<text x="{margin - 8}" y="{margin + i * size + 22}" text-anchor="end" font-size="10">{escape(name)}</text>')
        elements.append(f'<text transform="translate({margin + i * size + 22},112) rotate(-55)" font-size="10">{escape(name)}</text>')
        for j, value in enumerate(matrix[i]):
            shade = 245 if value is None else round(245 - 160 * value / maximum)
            x, y = margin + j * size, margin + i * size
            elements.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="rgb({shade},{shade},255)" stroke="white"/>')
            elements.append(f'<text x="{x + 18}" y="{y + 23}" text-anchor="middle" font-size="12">{value if value is not None else "—"}</text>')
    return "".join(elements) + "</svg>"


def _database_score(report):
    if not isinstance(report, dict):
        raise Refusal("persisted database score required")
    counts = ("expected_records", "stored_records", "correct_records", "wrong_records", "missing_records", "unexpected_records")
    if any(type(report.get(key)) is not int or not 0 <= report[key] <= 1000000 for key in counts):
        raise Refusal("invalid database score counts")
    expected, stored, correct = (report[key] for key in counts[:3])
    if (not expected or correct > min(expected, stored) or correct + report["wrong_records"] != stored
            or stored - report["unexpected_records"] != expected - report["missing_records"]
            or report.get("score") != correct / expected):
        raise Refusal("inconsistent database score")
    for metric in ("field_support", "field_errors", "field_missing"):
        fields = report.get(metric)
        if not isinstance(fields, dict) or not set(fields) <= FIELDS or any(type(value) is not int or not 0 <= value <= expected for value in fields.values()):
            raise Refusal("invalid database field score")
    if not set(report["field_errors"]) == set(report["field_missing"]) == set(report["field_support"]):
        raise Refusal("database field score taxonomy mismatch")
    for field, support in report["field_support"].items():
        if support != expected or report["field_errors"][field] + report["field_missing"][field] > support:
            raise Refusal("inconsistent database field support")


def write_evaluation(output, frames, *, provenance, detector_reports=None, final_database=None):
    """Persist immutable evidence, keeping every evaluated frame in the totals."""
    if not isinstance(frames, list) or not 1 <= len(frames) <= 1000:
        raise Refusal("bounded evaluation frames required")
    if not isinstance(provenance, dict):
        raise Refusal("evaluation provenance required")
    identities = [identifier(frame["sample_id"]) for frame in frames]
    if len(set(identities)) != len(identities):
        raise Refusal("duplicate evaluation frame")
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise Refusal("evaluation output already exists; preserve earlier evidence")
    evaluated = []
    associations = []
    if final_database is not None:
        _database_score(final_database)
    for frame in frames:
        _database_score(frame["database_score"])
        truth = frame["truth_fields"]
        association = confusion_report(frame.get("association_truth", truth), frame["predictions"],
                                       threshold=0.25, operation="associate-fields")
        associations.append(association)
        evaluated.append({"sample_id": frame["sample_id"],
                          "image_sha256": hashlib.sha256(Path(frame["image_path"]).read_bytes()).hexdigest(),
                          "ocr": score_ocr_fields(truth, frame["ocr"]), "association": association,
                          "database": frame["database_score"], "refusals": frame["refusals"], "ingest": frame["ingest"]})
    association = merge_confusions(associations)
    ocr = {role: {key: sum(row["ocr"]["per_role"][role][key] for row in evaluated)
                  for key in ("support", "correct", "missing", "wrong", "characters", "character_errors")}
           for role in SPORTS_ROLES}
    for stats in ocr.values():
        stats["accuracy"] = stats["correct"] / stats["support"] if stats["support"] else None
    database = {key: sum(row["database"][key] for row in evaluated)
                for key in ("expected_records", "stored_records", "correct_records", "wrong_records", "missing_records", "unexpected_records")}
    for metric in ("field_errors", "field_missing", "field_support"):
        keys = set().union(*(row["database"][metric] for row in evaluated))
        database[metric] = {key: sum(row["database"][metric].get(key, 0) for row in evaluated) for key in sorted(keys)}
    database["score"] = database["correct_records"] / database["expected_records"] if database["expected_records"] else None
    operations = {key: value | {"status": "measured"} for key, value in operation_registry().items()}
    operations["identify-ui"]["status"] = "measured" if detector_reports else "unmeasured"
    operations["store-quote"]["status"] = "measured" if any(row["ingest"] is not None for row in evaluated) else "unmeasured"
    report = {"schema": "sportsbook-evaluation/1", "frames": evaluated, "provenance": provenance,
              "operations": operations, "ocr_by_role": ocr, "association": association, "database": database,
              "detector": merge_confusions(detector_reports) if detector_reports else None,
              "final_database": final_database,
              "most_missed_ocr": sorted((dict(role=role, **stats) for role, stats in ocr.items() if stats["wrong"] + stats["missing"]),
                                        key=lambda row: (-row["wrong"] - row["missing"], row["role"]))}
    output.mkdir(parents=True, mode=0o700)
    (output / "error-crops").mkdir(mode=0o700)
    for frame, row in zip(frames, evaluated):
        with Image.open(frame["image_path"]) as image:
            if image.format != "PNG" or image.width > 4096 or image.height > 4096:
                raise Refusal("bounded PNG error evidence required")
            for index, failure in enumerate(row["ocr"]["failures"]):
                b = failure["box"]
                bounds = (max(0, math.floor(b["x"] - 8)), max(0, math.floor(b["y"] - 8)),
                          min(image.width, math.ceil(b["x"] + b["width"] + 8)), min(image.height, math.ceil(b["y"] + b["height"] + 8)))
                if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
                    raise Refusal("error crop outside capture")
                filename = f'{frame["sample_id"]}-{index}.png'
                image.crop(bounds).save(output / "error-crops" / filename)
                failure["crop"] = "error-crops/" + filename
    (output / "association-heatmap.svg").write_text(_heatmap(association), encoding="utf-8")
    if report["detector"]:
        (output / "identification-heatmap.svg").write_text(_heatmap(report["detector"]), encoding="utf-8")
    (output / "report.json").write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    rows = "".join(f'<tr><td>{escape(role)}</td><td>{stats["support"]}</td><td>{stats["correct"]}</td><td>{stats["missing"]}</td><td>{stats["wrong"]}</td></tr>' for role, stats in ocr.items())
    final = final_database or database
    errors = "".join(f'<tr><td>{escape(row["sample_id"])}</td><td>{escape(failure["role"])}</td><td>{escape(failure["expected"])}</td><td>{escape(failure["observed"]) or "Missing"}</td><td><a href="{failure["crop"]}"><img width="140" src="{failure["crop"]}" alt="Missing or wrong field crop"></a></td></tr>' for row in evaluated for failure in row["ocr"]["failures"])
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sportsbook training errors</title><style>body{{font:16px system-ui;max-width:1000px;margin:30px auto;padding:16px}}td,th{{padding:8px;border-bottom:1px solid #ccc;text-align:left}}img{{max-width:100%}}</style>
<h1>Sportsbook training errors</h1><p>Final database: {final["correct_records"]} / {final["expected_records"]} expected records stored exactly after {len(frames)} captures.</p>
<p>Across cumulative database snapshots: {database["correct_records"]} / {database["expected_records"]}. Earlier records contribute again when later captures are scored.</p>
<p>UI identification: {operations["identify-ui"]["status"]}. OCR reading and field association have separate scores.</p>
<h2>OCR by role</h2><table><thead><tr><th>Role</th><th>Support</th><th>Correct</th><th>Missing</th><th>Wrong</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Field association</h2><p>Rows: expected. Columns: predicted. Background true negatives are unmeasured.</p><img src="association-heatmap.svg" alt="Field association confusion matrix">
<h2>OCR error evidence</h2><table><thead><tr><th>Capture</th><th>Role</th><th>Expected</th><th>Observed</th><th>Crop</th></tr></thead><tbody>{errors}</tbody></table>
<p><a href="report.json">Complete report and error evidence</a></p></html>'''
    (output / "index.html").write_text(page, encoding="utf-8")
    return report
