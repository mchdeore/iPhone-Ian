import copy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from phone_lab.battle import combine_round, create_dashboard, dashboard_html, motion_settings
from phone_lab.benchmark import TASKS, Refusal
from phone_lab.blue import make_blue_packet
from phone_lab.workflow import append_run


def inputs():
    red = {"motion_profile": "fixed", "seed_offset": 0, "results": []}
    packets = []
    for index, task in enumerate(TASKS):
        sid = f"generated-{index}"
        red["results"].append(
            {
                "task": task,
                "outcome": {"session": sid, "complete": True, "wrong_actions": 0},
                "failure": None,
            }
        )
        packets.append(
            make_blue_packet(
                sid,
                (390, 700),
                [
                    {"kind": "down", "time_ms": 100, "x": 100, "y": 100, "pointer": 1},
                    {"kind": "up", "time_ms": 105, "x": 100, "y": 100, "pointer": 1},
                ],
            )
        )
    return red, packets


def test_blind_blue_score_then_independent_outcome_join():
    red, packets = inputs()
    first = combine_round(red, packets, round_number=1)
    assert first["red"]["completed"] == 6
    assert first["blue"]["flagged_sessions"] == 6
    changed = copy.deepcopy(red)
    changed["results"][0]["outcome"]["complete"] = False
    changed["results"][0]["outcome"]["robot_label"] = "private evaluator label"
    second = combine_round(changed, packets, round_number=1)
    assert second["red"]["completed"] == 5
    assert [row["blue"] for row in first["sessions"]] == [row["blue"] for row in second["sessions"]]
    assert "private evaluator label" not in str(second)


def test_round_identity_mismatch_duplicate_and_missing_task_refuse():
    red, packets = inputs()
    for bad in (
        packets[:-1],
        packets + [packets[0]],
        [packets[0] | {"run_id": "other"}, *packets[1:]],
    ):
        with pytest.raises(Refusal):
            combine_round(red, bad, round_number=1)
    red["results"] = red["results"][:-1]
    with pytest.raises(Refusal):
        combine_round(red, packets[:-1], round_number=1)


def test_profiles_are_declared_bounded_and_reproducible():
    fixed = motion_settings("fixed", 0)
    varied = motion_settings("varied", 0)
    assert fixed["tap_delay_ms"] == 0
    assert varied == motion_settings("varied", 0)
    assert 60 <= varied["tap_delay_ms"] <= 160
    assert varied["drag_duration_ms"] <= 400
    assert 6 <= varied["drag_steps"] <= 16
    for profile, seed in (("raw-firmware", 0), ([], 0), ("fixed", -1), ("fixed", True)):
        with pytest.raises(Refusal):
            motion_settings(profile, seed)


def test_dashboard_waits_then_reads_only_preserved_round_evidence(tmp_path):
    client = TestClient(create_dashboard(tmp_path))
    assert client.get("/api/status").json()["rounds"] == []
    red, packets = inputs()
    result = combine_round(red, packets, round_number=1)
    append_run(tmp_path / "battle_runs.jsonl", result)
    status = client.get("/api/status").json()
    assert status["rounds"][0]["red"]["completed"] == 6
    assert "Red team" in client.get("/").text
    assert "Blue team" in client.get("/").text
    assert client.post("/api/status", json={"run": True}).status_code == 405


def test_corrupt_dashboard_evidence_fails_closed(tmp_path):
    (tmp_path / "battle_runs.jsonl").write_bytes(b'{"private":"do not expose"')
    response = TestClient(create_dashboard(tmp_path)).get("/api/status")
    assert response.status_code == 503
    assert "do not expose" not in response.text


def test_dashboard_refuses_nested_privileged_or_malformed_saved_scores(tmp_path):
    red, packets = inputs()
    result = combine_round(red, packets, round_number=1)
    result["sessions"][0]["blue"]["features"]["camera"] = "private camera"
    append_run(tmp_path / "battle_runs.jsonl", result)
    response = TestClient(create_dashboard(tmp_path)).get("/api/status")
    assert response.status_code == 503
    assert "private camera" not in response.text


def test_dashboard_bootstrap_escapes_script_endings_in_actual_chrome():
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not Path(chrome).exists():
        pytest.skip("actual local Chrome unavailable")
    from playwright.sync_api import sync_playwright

    payload = {"state": "</script><script>window.pwned=1</script>", "rounds": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=chrome)
        page = browser.new_page()
        page.set_content(dashboard_html(payload))
        assert page.get_by_text("Red team", exact=True).count() == 1
        assert page.get_by_text("Blue team", exact=True).count() == 1
        assert page.evaluate("window.pwned") is None
        browser.close()
