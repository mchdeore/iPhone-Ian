import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from phone_lab.benchmark import Refusal
from phone_lab.sportsbook.app import create_app
from phone_lab.sportsbook.dataset import build_dataset
from phone_lab.sportsbook.pilot import evaluate_dataset

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


@pytest.mark.skipif(not CHROME.is_file(), reason="owned Chrome unavailable")
def test_actual_dataset_app_and_failed_ocr_keep_truth_separate_and_measure_every_capture(tmp_path):
    root = tmp_path / "dataset"
    manifest = build_dataset(root, CHROME, seeds={"train": [17], "validation": [117], "test": [217]})
    client = TestClient(create_app(root))
    assert client.get("/").status_code == 200
    row = manifest["samples"][0]
    assert client.get("/images/" + row["sample_id"]).headers["content-type"] == "image/png"
    assert client.get("/api/samples/" + row["sample_id"]).json()["tags"] == row["tags"]
    assert "Provider B" in client.get("/providers/provider-b?seed=117&phase=2").text
    assert client.get("/providers/provider-real").status_code == 404
    assert client.get("/providers/provider-a?phase=99").status_code == 422
    assert client.get("/images/unknown").status_code == 404
    calls = []

    def recognize(image):
        calls.append(image)
        assert image.suffix == ".png"
        return []

    output = tmp_path / "evaluation"
    report = evaluate_dataset(root, output, recognize=recognize, provenance={"recognizer": "deliberately empty test recognizer"})
    assert len(calls) == 9
    assert len(report["frames"]) == 9
    assert report["final_database"]["expected_records"] == 12
    assert report["final_database"]["missing_records"] == 12
    assert report["final_database"]["score"] == 0
    assert all(frame["refusals"] for frame in report["frames"])
    assert json.loads((output / "reports" / "report.json").read_text()) == report
    reviewed = TestClient(create_app(root, reports=output / "reports"))
    assert "Final database: 0 / 12" in reviewed.get("/evaluation/").text
    assert reviewed.get("/evaluation/report.json").json()["final_database"]["score"] == 0
    assert reviewed.get("/evaluation/observations.sqlite").status_code == 404
    with pytest.raises(Refusal):
        evaluate_dataset(root, output, recognize=recognize, provenance={})
    assert len(calls) == 9
