import json

import pytest
from PIL import Image

from phone_lab.benchmark import Refusal
from phone_lab.sportsbook.reports import operation_registry, score_ocr_fields, write_evaluation


def field(identity, role, value, x):
    return {"id": identity, "role": role, "text": value,
            "box": {"x": x, "y": 10, "width": 40, "height": 16}}


def observed(value, x, width=40, confidence=1):
    return {"text": value, "confidence": confidence,
            "box": {"x": x, "y": 10, "width": width, "height": 16}}


def test_ocr_score_distinguishes_missing_wrong_and_fragmented_shared_text():
    truth = [field("odds-1", "odds", "1.89", 10), field("line-1", "line", "—", 60),
             field("status-1", "status", "Open", 110)]
    report = score_ocr_fields(truth, [observed("1.88", 10), observed("Open", 110)])
    assert report["per_role"]["odds"]["wrong"] == 1
    assert report["per_role"]["line"]["missing"] == 1
    assert report["per_role"]["status"]["correct"] == 1
    assert report["character_errors"] == 2
    assert report["characters"] == 9
    assert report["per_role"]["navigation"]["support"] == 0
    assert report["per_role"]["navigation"]["accuracy"] is None
    names = [field("away", "participant", "Lake Wolves", 10), field("home", "participant", "East Hawks", 80)]
    assert score_ocr_fields(names, [observed("Lake Wolves @ East Hawks", 10, 110)])["correct"] == 2
    assert score_ocr_fields([truth[0]], [observed("1.89", 10, confidence=0.2)])["missing"] == 1


def test_report_preserves_per_frame_misses_and_refuses_overwriting_prior_evidence(tmp_path):
    image = tmp_path / "capture.png"
    Image.new("RGB", (180, 80), "white").save(image)
    truth = [field("odds-1", "odds", "1.89", 10)]
    database = {"expected_records": 1, "stored_records": 0, "correct_records": 0,
                "wrong_records": 0, "missing_records": 1, "unexpected_records": 0,
                "field_errors": {"odds": 0}, "field_missing": {"odds": 1},
                "field_support": {"odds": 1}, "score": 0, "failures": []}
    frame = {"sample_id": "frame-1", "image_path": str(image), "truth_fields": truth,
             "ocr": [], "predictions": [], "database_score": database,
             "refusals": [{"operation": "extract-row", "reason": "missing odds"}], "ingest": None}
    output = tmp_path / "evaluation"
    report = write_evaluation(output, [frame], provenance={"purpose": "test fixture"})
    assert report["database"]["score"] == 0
    assert report["database"]["field_missing"]["odds"] == 1
    assert report["association"]["per_class"]["odds"]["false_negative"] == 1
    assert report["operations"]["identify-ui"]["status"] == "unmeasured"
    assert (output / "association-heatmap.svg").is_file()
    assert len(list((output / "error-crops").glob("*.png"))) >= 1
    persisted = json.loads((output / "report.json").read_text())
    assert persisted == report
    original = (output / "report.json").read_bytes()
    with pytest.raises(Refusal):
        write_evaluation(output, [frame], provenance={})
    assert (output / "report.json").read_bytes() == original
    assert set(operation_registry()) == {"identify-ui", "read-text", "associate-fields", "parse-quote", "store-quote", "verify-database"}


def test_dash_glyphs_normalize_but_missing_digits_and_decimal_points_do_not():
    expected = [field("line-1", "line", "—", 10), field("line-2", "line", "-2.5", 60)]
    assert score_ocr_fields(expected, [observed("-", 10), observed("−2.5", 60)])["correct"] == 2
    assert score_ocr_fields([field("odds-1", "odds", "1.89", 10)], [observed("189", 10)])["wrong"] == 1


def test_impossible_database_score_is_rejected_before_report_output_is_created(tmp_path):
    image = tmp_path / "capture.png"
    Image.new("RGB", (180, 80), "white").save(image)
    database = {"expected_records": 1, "stored_records": 1, "correct_records": 2,
                "wrong_records": -1, "missing_records": 0, "unexpected_records": 0,
                "field_errors": {"odds": 0}, "field_missing": {"odds": 0}, "field_support": {"odds": 1},
                "score": 2, "failures": []}
    frame = {"sample_id": "frame-1", "image_path": str(image), "truth_fields": [], "ocr": [],
             "predictions": [], "database_score": database, "refusals": [], "ingest": None}
    with pytest.raises(Refusal):
        write_evaluation(tmp_path / "evaluation", [frame], provenance={})
    assert not (tmp_path / "evaluation").exists()
