"""Finite local dataset/OCR execution. Invoked only by the owned job supervisor."""

from __future__ import annotations

import signal
import sys

from ..benchmark import Refusal
from .dataset import build_dataset
from .jobs import JobStopped, JobStore
from .pilot import evaluate_dataset, native_recognizer


def run(root, jid, lease):
    store = JobStore(root)

    def stopped(signum, frame):
        raise JobStopped("job stop requested")

    signal.signal(signal.SIGTERM, stopped)
    try:
        frozen = store.execution(jid)
        request, executor = frozen["request"], frozen["executor"]
        output = store.root / "runs" / jid

        def progress(completed, total):
            store.check_budget(jid)
            store.progress(jid, lease, completed, total)

        if request["kind"] == "dataset":
            manifest = build_dataset(output / "dataset", executor["chrome"]["path"], seeds=request["seeds"], progress=progress)
            result = {"dataset_id": manifest["dataset_id"], "samples": len(manifest["samples"]), "artifact": "dataset/dataset.json"}
        else:
            dataset = store.dataset_path(request["dataset_id"])
            ocr = executor["ocr"]
            evaluation = evaluate_dataset(dataset, output / "evaluation", recognize=native_recognizer(ocr["path"], ocr["sha256"]),
                                          provenance={"ocr_binary_sha256": ocr["sha256"], "job_source": frozen["policy"], "training": "held"}, progress=progress)
            result = {"dataset_id": request["dataset_id"], "artifact": "evaluation/reports/index.html", "final_database": evaluation["final_database"]}
        store.terminal(jid, lease, "succeeded", result=result)
    except JobStopped:
        store.terminal(jid, lease, "interrupted", error="job interrupted")
    except Exception as error:
        store.terminal(jid, lease, "failed", error=str(error) if isinstance(error, Refusal) else type(error).__name__)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("owned supervisor arguments required")
    run(*sys.argv[1:])
