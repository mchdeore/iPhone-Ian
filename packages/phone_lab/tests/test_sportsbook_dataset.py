import json
from pathlib import Path

import pytest

from phone_lab.benchmark import Refusal
from phone_lab.sportsbook.dataset import audit_dataset, build_dataset
from phone_lab.sportsbook.evaluation import SPORTS_ROLES

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


@pytest.mark.skipif(not CHROME.is_file(), reason="owned Chrome unavailable")
def test_real_renderer_dataset_is_repeatable_bounded_and_group_disjoint(tmp_path):
    seeds = {"train": [17], "validation": [117], "test": [217]}
    first = build_dataset(tmp_path / "first", CHROME, seeds=seeds)
    second = build_dataset(tmp_path / "second", CHROME, seeds=seeds)
    assert first["dataset_id"] == second["dataset_id"]
    assert [r["sample_id"] for r in first["samples"]] == [r["sample_id"] for r in second["samples"]]
    assert len(first["samples"]) == 9
    assert first["renderer"]["browser_version"]
    assert len(first["renderer"]["executable_sha256"]) == 64
    groups = {}
    for row in first["samples"]:
        groups.setdefault(row["split"], set()).add(row["sequence_group"])
        annotation = json.loads((tmp_path / "first" / row["annotation"]).read_text())
        assert len(annotation["fields"]) == 30
        for field in annotation["fields"]:
            assert field["role"] in SPORTS_ROLES
            b = field["box"]
            assert 0 <= b["x"] < b["x"] + b["width"] <= 390
            assert 0 <= b["y"] < b["y"] + b["height"] <= 844
        assert len((tmp_path / "first" / row["labels"]).read_text().splitlines()) == 30
        assert row["tags"]["provider"] == {"train": "provider-a", "validation": "provider-b", "test": "provider-c"}[row["split"]]
    assert not groups["train"] & groups["validation"]
    assert not groups["train"] & groups["test"]
    assert audit_dataset(tmp_path / "first")["accepted"] is True
    with pytest.raises(Refusal):
        build_dataset(tmp_path / "first", CHROME, seeds=seeds)
    row = first["samples"][0]
    path = tmp_path / "first" / row["provider_truth"]
    path.write_text("{}")
    with pytest.raises(Refusal):
        audit_dataset(tmp_path / "first")


def test_invalid_split_seeds_are_rejected_before_creating_output(tmp_path):
    output = tmp_path / "invalid"
    with pytest.raises(Refusal):
        build_dataset(output, CHROME, seeds={"train": [17], "validation": [17], "test": [217]})
    assert not output.exists()
