import json
from dataclasses import replace

import pytest
from PIL import Image, ImageDraw

from phone_lab.benchmark import Benchmark, Refusal
from phone_lab.control import Frame
from phone_lab.workflow import (
    append_run,
    color_candidates,
    load_capture,
    read_runs,
    save_capture,
    website_observations,
)


def test_saved_pixel_capture_candidates_and_tamper(tmp_path):
    source = tmp_path / "source.png"
    im = Image.new("RGB", (400, 800), "white")
    ImageDraw.Draw(im).rounded_rectangle(
        (30, 140, 169, 187), radius=8, outline=(97, 147, 205), width=2
    )
    im.save(source)
    frame = Frame("one", "sid", "sid:1", 10, 400, 800)
    m = save_capture(tmp_path / "capture", source, frame, permission="generated-fixture")
    loaded, path = load_capture(tmp_path / "capture")
    assert loaded == frame
    assert not m["real_phone"]
    assert color_candidates(path) == [
        {
            "box": {"x": 30, "y": 140, "width": 140, "height": 48},
            "role": "unknown",
            "source": "pixel-border-baseline",
            "actionable": False,
        }
    ]
    with pytest.raises(Refusal):
        save_capture(tmp_path / "capture", source, frame, permission="generated-fixture")
    with pytest.raises(Refusal):
        save_capture(
            tmp_path / "bad", source, replace(frame, width=300), permission="generated-fixture"
        )
    path.chmod(0o600)
    path.write_bytes(b"changed")
    with pytest.raises(Refusal):
        load_capture(tmp_path / "capture")


def test_append_restart_and_retained_interrupted_tail(tmp_path):
    path = tmp_path / "runs.jsonl"
    append_run(path, {"simulated": True, "result": 1})
    append_run(path, {"simulated": True, "result": 2})
    assert [r["result"] for r in read_runs(path)] == [1, 2]
    with path.open("a") as f:
        f.write("{broken")
    before = path.read_bytes()
    with pytest.raises(Refusal):
        read_runs(path)
    assert path.read_bytes() == before


def test_blue_summary_uses_only_contact_evidence_and_consent(tmp_path):
    bench = Benchmark(tmp_path / "lab")
    s = bench.create("generated", 17, 400, 800, "tap")
    s.complete = True
    s.wrong_actions = 1
    s.events = [
        {"time_ms": 20, "motor_hover_mm": 999},
        {"time_ms": 120, "camera_route": "lab-only"},
    ]
    r = website_observations([s])
    assert r["cohorts"]["generated"] == {
        "sessions": 1,
        "complete": 1,
        "wrong_actions": 1,
        "events": 2,
        "median_duration_ms": 100,
    }
    assert not r["lab_telemetry_used"] and "camera_route" not in json.dumps(r)
    with pytest.raises(Refusal):
        website_observations([replace(s, cohort="human", consent_ref=None)])
