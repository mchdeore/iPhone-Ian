from __future__ import annotations

import json
import math
import stat

import pytest
from fastapi.testclient import TestClient

from phone_lab.benchmark import TASKS, Benchmark, Refusal, layout
from phone_lab.web import create_app


@pytest.fixture
def lab(tmp_path):
    return Benchmark(tmp_path / "lab")


def emit(lab, sid, observation_kind, x=0, y=0, **changes):
    s = lab.get(sid)
    event = {
        "device": s.device,
        "frame": s.marker,
        "seq": s.last_seq + 1,
        "event_id": f"e-{s.last_seq + 1}",
        "kind": observation_kind,
        "x": x,
        "y": y,
        "time_ms": max(0, s.last_time) + 10,
        "pointer": 1,
    }
    event.update(changes)
    return lab.observe(sid, event)


def tap(lab, sid, target):
    t = next(t for t in lab.get(sid).targets() if t.id == target)
    x, y = t.box.center
    emit(lab, sid, "down", x, y)
    return emit(lab, sid, "up", x, y)


@pytest.mark.parametrize("task", TASKS)
@pytest.mark.parametrize("viewport", [(280, 400), (390, 700), (800, 1200)])
def test_seeded_components_reproduce_and_fit(task, viewport):
    for seed in (0, 19, 47):
        targets = layout(seed, *viewport, task)
        assert targets == layout(seed, *viewport, task)
        for target in targets:
            b = target.box
            assert 0 <= b.x < b.x + b.width <= viewport[0]
            assert 0 <= b.y < b.y + b.height <= viewport[1]


@pytest.mark.parametrize("task", TASKS)
def test_independent_task_outcomes_and_restart(lab, task):
    s = lab.create("phone-a", 73, 390, 700, task)
    assert not lab.outcome(s.id)["complete"]
    if task == "drag":
        points = {t.id: t.box.center for t in s.targets()}
        emit(lab, s.id, "down", *points["grip"])
        emit(lab, s.id, "move", 200, 300)
        emit(lab, s.id, "up", *points["goal"])
    elif task == "entry":
        tap(lab, s.id, "value")
        emit(lab, s.id, "input", value=s.expected_value)
        tap(lab, s.id, "check")
    elif task == "menu":
        tap(lab, s.id, "menu")
        tap(lab, s.id, "orange")
    elif task == "overlay":
        tap(lab, s.id, "close")
        tap(lab, s.id, "continue")
    elif task == "scroll":
        emit(lab, s.id, "scroll", value="200")
        tap(lab, s.id, "finish")
    else:
        tap(lab, s.id, "continue")
    result = lab.outcome(s.id)
    assert result["complete"] and result["events"] >= 2
    restored = Benchmark(lab.root)
    assert restored.outcome(s.id) == result
    assert restored.get(s.id).events == lab.get(s.id).events
    with pytest.raises(Refusal, match="completed"):
        emit(lab, s.id, "down")


@pytest.mark.parametrize(
    "changes",
    [
        {"frame": "old"},
        {"device": "phone-b"},
        {"seq": 0},
        {"seq": True},
        {"x": math.nan},
        {"x": math.inf},
        {"x": -1},
        {"x": True},
        {"y": 701},
        {"time_ms": -1},
        {"pointer": 1000},
        {"pointer": False},
        {"pressure": 2},
        {"contact_width": -1},
        {"event_id": "../bad"},
        {"kind": "success"},
        {"success": True},
        {"value": "x" * 33},
    ],
)
def test_refused_observations_do_not_change_state_or_log(lab, changes):
    s = lab.create("phone-a", 1, 390, 700, "tap")
    before = lab.log.read_bytes()
    with pytest.raises(Refusal):
        emit(lab, s.id, "down", **changes)
    assert lab.log.read_bytes() == before
    assert lab.get(s.id).last_seq == 0


def test_pointer_pairing_wrong_target_and_duplicate_identity(lab):
    s = lab.create("phone-a", 1, 390, 700, "tap")
    with pytest.raises(Refusal, match="missing"):
        emit(lab, s.id, "up")
    assert not tap(lab, s.id, "cancel")["complete"]
    assert lab.get(s.id).wrong_actions == 1
    emit(lab, s.id, "down", 1, 1)
    with pytest.raises(Refusal, match="one contact"):
        emit(lab, s.id, "down")
    with pytest.raises(Refusal, match="mismatched"):
        emit(lab, s.id, "up", pointer=2)
    with pytest.raises(Refusal, match="duplicate event"):
        emit(lab, s.id, "up", event_id="e-1")


def test_focus_numeric_accuracy_and_changed_frame(lab):
    s = lab.create("phone-a", 19, 390, 700, "entry")
    with pytest.raises(Refusal, match="unfocused"):
        emit(lab, s.id, "input", value=s.expected_value)
    old_frame = s.marker
    tap(lab, s.id, "value")
    assert lab.get(s.id).marker != old_frame
    emit(lab, s.id, "input", value="1111")
    assert not tap(lab, s.id, "check")["complete"]
    with pytest.raises(Refusal, match="numeric"):
        emit(lab, s.id, "input", value="１２３４")
    emit(lab, s.id, "input", value=s.expected_value)
    assert tap(lab, s.id, "check")["complete"]


def test_reset_invalidates_frame_preserves_evidence_and_time(lab):
    s = lab.create("phone-a", 4, 390, 700, "tap")
    emit(lab, s.id, "down", 1, 1)
    old = lab.get(s.id)
    reset = lab.reset(s.id)
    assert reset.marker != old.marker and reset.active_pointer is None
    assert reset.events == old.events and reset.last_seq == old.last_seq
    with pytest.raises(Refusal, match="stale"):
        emit(lab, s.id, "up", frame=old.marker)
    with pytest.raises(Refusal, match="time reversed"):
        emit(lab, s.id, "down", time_ms=0)
    assert tap(lab, s.id, "continue")["complete"]


def test_budget_write_failure_corruption_and_private_storage(tmp_path):
    lab = Benchmark(tmp_path / "lab", max_sessions=1, max_events=1)
    s = lab.create("phone-a", 1, 390, 700, "tap")
    assert stat.S_IMODE(lab.log.stat().st_mode) == 0o600
    with pytest.raises(Refusal, match="session budget"):
        lab.create("phone-b", 1, 390, 700, "tap")
    emit(lab, s.id, "down")
    with pytest.raises(Refusal, match="budget"):
        emit(lab, s.id, "up")
    with lab.log.open("a") as f:
        f.write('{"interrupted":')
    original = lab.log.read_bytes()
    with pytest.raises(Refusal, match="interrupted"):
        Benchmark(lab.root)
    assert lab.log.read_bytes() == original
    link = tmp_path / "link"
    link.symlink_to(lab.root)
    with pytest.raises(Refusal, match="symlink"):
        Benchmark(link)


def test_failed_persistence_does_not_commit_in_memory(lab, monkeypatch):
    s = lab.create("phone-a", 1, 390, 700, "tap")

    def failed(*args):
        raise OSError("disk full")

    monkeypatch.setattr(lab, "_save", failed)
    with pytest.raises(OSError):
        emit(lab, s.id, "down")
    assert lab.get(s.id).last_seq == 0


def test_consent_and_schema_boundaries(lab):
    with pytest.raises(Refusal, match="consent"):
        lab.create("phone-a", 1, 390, 700, "tap", cohort="human")
    s = lab.create(
        "phone-a", 1, 390, 700, "tap", cohort="accessibility", consent_ref="local-consent-1"
    )
    assert s.cohort == "accessibility"
    with pytest.raises(Refusal):
        lab.create("../phone", 1, 390, 700, "tap")
    with pytest.raises(Refusal):
        lab.create("phone-a", True, 390, 700, "tap")


def test_api_truth_operator_observation_separation(lab):
    client = TestClient(create_app(lab, "operator-0123456789", "evaluator-0123456789"))
    body = {"device": "phone-a", "seed": 1}
    assert client.post("/api/session", json=body).status_code == 409
    r = client.post("/api/session", json=body, headers={"X-Operator-Key": "operator-0123456789"})
    sid = r.json()["session"]
    s = lab.get(sid)
    assert client.get(f"/s/{sid}").status_code == 200
    assert client.get(f"/api/labels/{sid}").status_code == 409
    assert (
        client.get(f"/api/labels/{sid}", headers={"X-Evaluator-Key": s.capability}).status_code
        == 409
    )
    labels = client.get(f"/api/labels/{sid}", headers={"X-Evaluator-Key": "evaluator-0123456789"})
    assert labels.json()["targets"][0]["text"] == "Continue"
    r = client.post(
        f"/api/touch/{sid}", json={"success": True}, headers={"X-Session-Capability": s.capability}
    )
    assert r.status_code == 409 and not lab.outcome(sid)["complete"]
    assert (
        client.post(f"/api/reset/{sid}", headers={"X-Operator-Key": s.capability}).status_code
        == 409
    )
    events = client.get(f"/api/events/{sid}")
    assert "text/event-stream" in events.headers["content-type"]
    assert all(word not in events.text for word in ("capability", "cohort", "targets"))
    assert (
        client.post(
            "/api/session",
            json={**body, "success": True},
            headers={"X-Operator-Key": "operator-0123456789"},
        ).status_code
        == 422
    )
    records = [json.loads(line) for line in lab.log.read_text().splitlines()]
    assert all("events" not in record["snapshot"] for record in records)


def test_http_request_byte_budget(lab):
    client = TestClient(create_app(lab, "operator-0123456789", "evaluator-0123456789"))
    r = client.post(
        "/api/session",
        json={"device": "a" * 70000, "seed": 1},
        headers={"X-Operator-Key": "operator-0123456789"},
    )
    assert r.status_code == 413 and not lab.sessions


def test_credentials_survive_restart_without_entering_evidence_log(tmp_path):
    bench = Benchmark(tmp_path / "private")
    s = bench.create("generated", 3, 390, 700, "tap")
    assert s.capability not in bench.log.read_text()
    recovered = Benchmark(tmp_path / "private")
    assert recovered.authorize(s.id, s.capability).id == s.id
    key = bench.keys / s.id
    assert stat.S_IMODE(key.stat().st_mode) == 0o600
    key.write_text("")
    with pytest.raises(Refusal):
        Benchmark(tmp_path / "private")
