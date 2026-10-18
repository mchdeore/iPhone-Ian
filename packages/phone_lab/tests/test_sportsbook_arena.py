import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from phone_lab.benchmark import Refusal
from phone_lab.sportsbook.app import create_app, create_red_app
from phone_lab.sportsbook.arena import ArenaStore
from phone_lab.sportsbook.dataset import build_dataset

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    if not CHROME.is_file():
        pytest.skip("owned Chrome unavailable")
    root = tmp_path_factory.mktemp("arena") / "dataset"
    manifest = build_dataset(root, CHROME, seeds={"train": [31], "validation": [131], "test": [231]})
    return root, manifest


def submission(capture, attempt="first", quotes=None, **changes):
    return dict(attempt_id=attempt, capture_id=capture["capture_id"], image_sha256=capture["image_sha256"],
                actor_id="manual-pixel-test", model_sha256=None, parser_version="manual/1", latency_ms=250,
                quotes=[] if quotes is None else quotes, refusals=[], retry_of=None, **changes)


def test_red_receives_only_opaque_capture_pixels_and_training_hold(dataset, tmp_path):
    root, manifest = dataset
    red = TestClient(create_red_app(root, arena=tmp_path / "round.sqlite"))
    status = red.get("/api/status").json()
    assert status["training"]["state"] == "held" and status["surface"] == "red"
    captures = red.get("/api/captures").json()["captures"]
    assert len(captures) == len(manifest["samples"])
    assert all(set(row) == {"capture_id", "image_sha256", "image_url"} for row in captures)
    text = red.get("/").text + json.dumps(captures)
    assert all(row["sample_id"] not in text for row in manifest["samples"])
    assert "seed" not in text and "Training held" in text
    pixels = red.get(captures[0]["image_url"])
    assert pixels.headers["content-type"] == "image/png"
    assert pixels.content.startswith(b"\x89PNG")
    for path in ("/api/samples/anything", "/providers/provider-a", "/evaluation/", "/api/arena", "/samples/anything"):
        assert red.get(path).status_code == 404
    assert red.post("/api/attempts", json=submission(captures[0])).json()["status"] == "empty"
    assert red.post("/api/attempts", json={**submission(captures[0]), "truth": []}).status_code == 422
    assert red.post("/api/attempts", content=b"x" * 262145).status_code == 413
    assert red.post("/api/attempts", json={**submission(captures[0]), "refusals": [{"operation": [], "reason": "invalid"}]}).status_code == 422


def test_attempt_replay_retry_refusal_atomicity_and_reopen(dataset, tmp_path):
    root, manifest = dataset
    path = tmp_path / "round.sqlite"
    arena = ArenaStore(path, root)
    capture = next(c for c in arena.captures() if arena.sample(c["capture_id"])["tags"]["phase"] == 0)
    empty = submission(capture)
    assert arena.submit(empty)["status"] == "empty"
    assert arena.submit(empty)["replayed"] is True
    with pytest.raises(Refusal, match="conflicting attempt replay"):
        arena.submit({**empty, "latency_ms": 251})
    sample = arena.sample(capture["capture_id"])
    quotes = json.loads((root / sample["provider_truth"]).read_text())["quotes"]
    valid = {**submission(capture, "retry", quotes), "retry_of": "first"}
    assert arena.submit(valid)["status"] == "accepted"
    assert arena.store.counts()["latest"] == 4
    bad = copy.deepcopy(quotes)
    for q in bad[:-1]:
        q["event_id"] = "E999999"
    bad[-1]["odds"] = "1.99" if bad[-1]["odds"] != "1.99" else "2.01"
    result = arena.submit({**submission(capture, "conflict", bad), "retry_of": "retry"})
    assert result["status"] == "refused" and "same provider time" in result["reason"]
    assert arena.store.counts() == {"captures": 1, "observations": 4, "latest": 4}
    assert len(arena.attempts()) == 3
    with pytest.raises(Refusal, match="explicit retry"):
        arena.submit(submission(capture, "silent-retry"))
    with pytest.raises(Refusal, match="retry"):
        arena.submit({**submission(capture, "unknown-retry"), "retry_of": "absent"})
    with pytest.raises(Refusal, match="image commitment"):
        arena.submit({**submission(capture, "wrong-image"), "image_sha256": "0" * 64})
    arena.close()
    reopened = ArenaStore(path, root)
    assert len(reopened.attempts()) == 3 and capture in reopened.captures()
    score = reopened.evaluate()
    assert score["database"]["score"] == 1 and score["attempts"] == 3
    assert reopened.evaluations()[0]["score"] == score
    reopened.close()


def test_blue_evaluates_committed_empty_attempt_and_foreign_database_untouched(dataset, tmp_path):
    root, _ = dataset
    path = tmp_path / "round.sqlite"
    red = TestClient(create_red_app(root, arena=path))
    blue = TestClient(create_app(root, arena=path))
    assert blue.get("/api/status").json()["training"]["state"] == "held"
    assert blue.post("/api/arena/evaluate").json()["database"] is None
    capture = red.get("/api/captures").json()["captures"][0]
    refused = {**submission(capture), "refusals": [{"operation": "read-text", "reason": "low confidence"}]}
    assert red.post("/api/attempts", json=refused).json()["status"] == "refused"
    assert "New attempts are pending evaluation" in blue.get("/arena/").text
    score = blue.post("/api/arena/evaluate").json()
    assert score["attempts"] == 1 and score["database"]["score"] == 0
    assert score["database"]["missing_records"] == 4
    board = blue.get("/arena/")
    assert board.status_code == 200 and "low confidence" in board.text and "Stored exactly" in board.text
    assert blue.get("/api/arena").json()["attempts"][0]["payload"]["quotes"] == []
    foreign = tmp_path / "foreign.sqlite"
    foreign.write_bytes(b"keep these original bytes")
    before = foreign.read_bytes()
    with pytest.raises(Refusal):
        ArenaStore(foreign, root)
    assert foreign.read_bytes() == before


def test_simultaneous_identical_submission_has_one_durable_attempt(dataset, tmp_path):
    root, _ = dataset
    path = tmp_path / "concurrent.sqlite"
    arena = ArenaStore(path, root)
    payload = submission(arena.captures()[0])
    arena.close()


    def send(_):
        store = ArenaStore(path, root)
        try:
            return store.submit(payload)
        finally:
            store.close()

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(send, range(4)))
    assert sum(not row["replayed"] for row in results) == 1
    arena = ArenaStore(path, root)
    assert len(arena.attempts()) == 1
    arena.close()

def test_older_capture_is_retained_without_replacing_latest_quotes(dataset, tmp_path):
    root, _ = dataset
    arena = ArenaStore(tmp_path / "freshness.sqlite", root)
    captures = [c for c in arena.captures() if arena.sample(c["capture_id"])["tags"]["provider"] == "provider-a"]
    for phase in (2, 0):
        capture = next(c for c in captures if arena.sample(c["capture_id"])["tags"]["phase"] == phase)
        sample = arena.sample(capture["capture_id"])
        quotes = json.loads((root / sample["provider_truth"]).read_text())["quotes"]
        result = arena.submit(submission(capture, "phase-" + str(phase), quotes))
        assert result["status"] == "accepted"
        if phase == 0:
            assert result["ingest"]["stale_ignored"] == 4
    assert arena.store.counts() == {"captures": 2, "observations": 8, "latest": 4}
    assert arena.evaluate()["database"]["score"] == 1
    arena.close()
