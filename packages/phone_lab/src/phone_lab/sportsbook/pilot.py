from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ..benchmark import Refusal
from .contracts import quote_key
from .dataset import _inside, audit_dataset
from .extract import parse_page
from .reports import write_evaluation
from .storage import QuoteStore, score_database


def native_recognizer(executable, expected_sha256):
    executable = Path(executable)
    if not executable.is_absolute() or not executable.is_file() or hashlib.sha256(executable.read_bytes()).hexdigest() != expected_sha256:
        raise Refusal("reviewed OCR executable digest mismatch or unavailable")

    def recognize(image):
        result = subprocess.run([str(executable), str(image)], check=True, capture_output=True, timeout=30)
        if len(result.stdout) > 4 * 1024 * 1024:
            raise Refusal("OCR output budget exceeded")
        return json.loads(result.stdout)

    return recognize


def _association_truth(fields):
    result = [dict(field, box=field["text_box"]) for field in fields if field["role"] != "participant"]
    participants = [field for field in fields if field["role"] == "participant"]
    x = min(field["text_box"]["x"] for field in participants)
    y = min(field["text_box"]["y"] for field in participants)
    result.append({"id": "event-participants", "role": "participant", "box": {
        "x": x, "y": y,
        "width": max(field["text_box"]["x"] + field["text_box"]["width"] for field in participants) - x,
        "height": max(field["text_box"]["y"] + field["text_box"]["height"] for field in participants) - y}})
    return result


def evaluate_dataset(root, output, *, recognize, provenance):
    """The recognizer receives only PNG paths; gold is read after actor persistence."""
    root, output = Path(root), Path(output)
    if output.exists() or output.is_symlink():
        raise Refusal("evaluation output exists; preserve earlier evidence")
    audit = audit_dataset(root)
    manifest = json.loads((root / "dataset.json").read_text())
    output.mkdir(parents=True, mode=0o700)
    (output / "red-observations").mkdir(mode=0o700)
    store = QuoteStore(output / "observations.sqlite")
    frames, expected = [], {}
    start = datetime.now(ZoneInfo("America/Toronto")).isoformat()
    try:
        for sample in manifest["samples"]:
            image = _inside(root, sample["image"])
            refusals, ingest, recognized = [], None, []
            parsed = {"quotes": [], "fields": []}
            try:
                recognized = recognize(image)
                parsed = parse_page(recognized)
                refusals.extend(parsed["refusals"])
                if parsed["quotes"]:
                    ingest = store.ingest(sample["sha256"]["image"], parsed["quotes"], parser_version=parsed["parser_version"])
            except (Refusal, subprocess.SubprocessError, OSError, ValueError) as error:
                refusals.append({"operation": "read-extract-store", "type": type(error).__name__, "reason": str(error)})
            actor = {"ocr": recognized, "parsed": parsed, "refusals": refusals, "ingest": ingest,
                     "inputs": "PNG only for OCR; OCR text/confidence/boxes only for parsing"}
            (output / "red-observations" / (sample["sample_id"] + ".json")).write_text(json.dumps(actor, sort_keys=True, allow_nan=False) + "\n")
            truth = json.loads(_inside(root, sample["provider_truth"]).read_text())
            for quote in truth["quotes"]:
                expected[quote_key(quote)] = quote
            annotation = json.loads(_inside(root, sample["annotation"]).read_text())
            fields = annotation["fields"]
            frames.append({"sample_id": sample["sample_id"], "image_path": str(image), "ocr": recognized,
                           "truth_fields": [dict(field, box=field["text_box"]) for field in fields],
                           "association_truth": _association_truth(fields), "predictions": parsed["fields"],
                           "database_score": score_database(store, list(expected.values())), "refusals": refusals, "ingest": ingest})
        store.close()
        reopened = QuoteStore(output / "observations.sqlite")
        try:
            final = score_database(reopened, list(expected.values()))
            counts = reopened.counts()
        finally:
            reopened.close()
        return write_evaluation(output / "reports", frames, final_database=final, provenance={
            **provenance, "dataset_id": manifest["dataset_id"], "dataset_audit": audit,
            "started_at_toronto": start, "completed_at_toronto": datetime.now(ZoneInfo("America/Toronto")).isoformat(),
            "database_counts": counts, "score_scope": "each capture scores the cumulative expected database; final score independently reopens SQLite",
            "purpose": "synthetic development evaluation; no physical gantry or untouched human/phone holdout"})
    except Exception as error:
        (output / "failure.json").write_text(json.dumps({"accepted": False, "type": type(error).__name__, "reason": str(error)}) + "\n")
        raise
    finally:
        store.close()
