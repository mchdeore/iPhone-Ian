import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from phone_lab.benchmark import Refusal
from phone_lab.blue import make_blue_packet
from phone_lab.sportsbook.app import create_app, create_red_app
from phone_lab.sportsbook.arena import ArenaStore
from phone_lab.sportsbook.behavior import BehaviorSessions, frozen_scorer
from phone_lab.sportsbook.dataset import build_dataset
from phone_lab.sportsbook.storage import QuoteStore, encoded

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    if not CHROME.is_file():
        pytest.skip("owned Chrome unavailable")
    root = tmp_path_factory.mktemp("provider-behavior") / "dataset"
    build_dataset(root, CHROME, seeds={"train": [42], "validation": [142], "test": [242]})
    return root


def contacts(session, dwells):
    events, at = [], 0
    for dwell in dwells:
        events.append(dict(kind="down", time_ms=at, x=20, y=40, pointer=1))
        for index in range(1, 5):
            events.append(dict(kind="move", time_ms=at + dwell * index / 5, x=20 + index * 10, y=40, pointer=1))
        events.append(dict(kind="up", time_ms=at + dwell, x=60, y=40, pointer=1))
        at += dwell + 40
    return make_blue_packet(session["session_id"], session["viewport"], events)


def test_frozen_provider_packet_history_replay_and_boundary(dataset, tmp_path):
    arena = ArenaStore(tmp_path / "round.sqlite", dataset)
    behavior = BehaviorSessions(arena)
    capture = arena.captures()[0]
    session = behavior.start(capture["capture_id"])
    assert session["policy"] == frozen_scorer()
    packet = contacts(session, [10, 10, 10, 10])
    for extra in ("labels", "text", "model_sha256", "camera", "motor", "truth"):
        with pytest.raises(Refusal):
            behavior.finish(session["session_id"], {**packet, extra: "forbidden"})
    assert behavior.sessions()[0]["packet"] is None
    result = behavior.finish(session["session_id"], packet)
    assert set(result["score"]["flags"]) == {"short_contact_dwell", "regular_contact_dwell", "straight_contact_path"}
    assert result["score"]["robot_probability"] is None and result["score"]["sanctions"] is False
    assert behavior.finish(session["session_id"], packet)["replayed"] is True
    with pytest.raises(Refusal, match="conflicting"):
        behavior.finish(session["session_id"], contacts(session, [60]))
    arena.close()
    reopened = ArenaStore(tmp_path / "round.sqlite", dataset)
    row = BehaviorSessions(reopened).sessions()[0]
    assert row["packet"] == packet and row["score"] == result["score"]
    assert reopened.evaluate()["database"] is None
    reopened.close()


def test_source_drift_empty_cancel_and_explicit_matching_attempt_links(dataset, tmp_path, monkeypatch):
    arena = ArenaStore(tmp_path / "round.sqlite", dataset)
    behavior = BehaviorSessions(arena)
    capture = arena.captures()[0]
    first, second = behavior.start(capture["capture_id"]), behavior.start(capture["capture_id"])
    real = frozen_scorer()
    monkeypatch.setattr("phone_lab.sportsbook.behavior.frozen_scorer", lambda: {**real, "version": "changed"})
    with pytest.raises(Refusal, match="frozen"):
        behavior.start(capture["capture_id"])
    with pytest.raises(Refusal, match="frozen"):
        behavior.finish(first["session_id"], contacts(first, []))
    monkeypatch.undo()
    result = behavior.finish(first["session_id"], contacts(first, []))
    assert result["score"]["features"]["contacts"] == 0 and result["score"]["flags"] == []
    behavior.cancel(second["session_id"], "operator ended before capture")
    assert behavior.sessions()[1]["state"] == "cancelled" and behavior.sessions()[1]["score"] is None
    payload=dict(attempt_id="manual", capture_id=capture["capture_id"], image_sha256=capture["image_sha256"], actor_id="manual",
                 model_sha256=None, parser_version="manual/1", latency_ms=0, quotes=[], refusals=[], retry_of=None)
    arena.submit(payload)
    assert behavior.link(first["session_id"], "manual")["replayed"] is False
    assert behavior.link(first["session_id"], "manual")["replayed"] is True
    another = next(c for c in arena.captures() if c["capture_id"] != capture["capture_id"])
    arena.submit({**payload, "attempt_id": "another", "capture_id": another["capture_id"], "image_sha256": another["image_sha256"]})
    with pytest.raises(Refusal, match="same capture"):
        behavior.link(first["session_id"], "another")
    arena.close()


def test_blue_operator_routes_keep_provider_pages_and_behavior_off_red(dataset, tmp_path):
    path = tmp_path / "round.sqlite"
    blue, red = TestClient(create_app(dataset, arena=path)), TestClient(create_red_app(dataset, arena=path))
    capture = red.get("/api/captures").json()["captures"][0]
    response = blue.post("/api/provider/sessions", json={"capture_id": capture["capture_id"]})
    assert response.status_code == 200
    session = response.json()
    page = blue.get("/provider-session/" + session["session_id"])
    assert page.status_code == 200 and "Save contacts" in page.text
    source = blue.get("/provider-session/" + session["session_id"] + "/page")
    assert source.status_code == 200 and "provider-contact-event" in source.text
    result = blue.post("/api/provider/sessions/" + session["session_id"] + "/contacts", json=contacts(session, [60, 110]))
    assert result.status_code == 200
    assert blue.get("/api/arena").json()["provider_sessions"][0]["score"]["features"]["contacts"] == 2
    for route in ("/provider-session/" + session["session_id"], "/provider-session/" + session["session_id"] + "/page", "/api/provider/sessions"):
        assert red.get(route).status_code == 404 and red.post(route, json={}).status_code == 404
    assert blue.post("/api/provider/sessions", json={"capture_id": capture["capture_id"], "seed": 42}).status_code == 422
    assert blue.post("/api/provider/sessions", json={"capture_id": []}).status_code == 422
    assert blue.post("/api/provider/sessions/" + session["session_id"] + "/link", json={"attempt_id": []}).status_code == 422
    assert blue.post("/api/provider/sessions/" + session["session_id"] + "/contacts", content=b"x" * 1048577).status_code == 413
    assert "Provider behavior" in blue.get("/arena/").text


def test_invalid_packet_does_not_partially_close_session(dataset, tmp_path):
    arena = ArenaStore(tmp_path / "round.sqlite", dataset)
    behavior = BehaviorSessions(arena)
    session = behavior.start(arena.captures()[0]["capture_id"])
    packet = contacts(session, [100])
    wrong = json.loads(json.dumps(packet))
    wrong["events"][-1]["time_ms"] = -1
    with pytest.raises(Refusal):
        behavior.finish(session["session_id"], wrong)
    row = behavior.sessions()[0]
    assert row["state"] == "open" and row["packet"] is None and row["score"] is None
    assert behavior.finish(session["session_id"], packet)["replayed"] is False
    arena.close()


def test_legacy_round_migration_preserves_quote_attempt_and_evaluation_history(dataset, tmp_path):
    path = tmp_path / "legacy.sqlite"
    manifest = json.loads((dataset / "dataset.json").read_text())
    sample = manifest["samples"][0]
    quotes = json.loads((dataset / sample["provider_truth"]).read_text())["quotes"]
    legacy = QuoteStore(path)
    legacy.ingest("a" * 64, quotes)
    # The four-table arena/1 fixture matches the previously shipped schema.
    with legacy.db:
        legacy.db.execute("CREATE TABLE arena_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        legacy.db.execute("CREATE TABLE challenges(id TEXT PRIMARY KEY,sample_id TEXT UNIQUE NOT NULL,image_sha256 TEXT NOT NULL)")
        legacy.db.execute("CREATE TABLE attempts(seq INTEGER PRIMARY KEY,id TEXT UNIQUE NOT NULL,capture_id TEXT NOT NULL,payload_sha256 TEXT NOT NULL,payload TEXT NOT NULL,result TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(capture_id) REFERENCES challenges(id))")
        legacy.db.execute("CREATE TABLE evaluations(seq INTEGER PRIMARY KEY,attempt_seq INTEGER NOT NULL,score TEXT NOT NULL,created_at TEXT NOT NULL)")
        legacy.db.executemany("INSERT INTO arena_meta VALUES (?,?)", [("schema", "sportsbook-arena/1"), ("dataset_id", manifest["dataset_id"]), ("run_id", "legacy-test")])
        legacy.db.execute("INSERT INTO challenges VALUES (?,?,?)", ("b" * 64, sample["sample_id"], sample["sha256"]["image"]))
        payload = encoded({"actor_id": "legacy-manual", "quotes": quotes})
        legacy.db.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?,?)", (1, "legacy-attempt", "b" * 64, "c" * 64, payload, encoded({"status": "accepted"}), "2026-10-17T12:00:00-04:00"))
        legacy.db.execute("INSERT INTO evaluations VALUES (?,?,?,?)", (1, 1, encoded({"fixture": "retained-history"}), "2026-10-17T12:01:00-04:00"))
    before_quotes, before_attempt = legacy.latest(), legacy.db.execute("SELECT * FROM attempts").fetchall()
    legacy.close()
    arena = ArenaStore(path, dataset)
    assert arena.meta["schema"] == "sportsbook-arena/2"
    assert arena.meta["blue_prior_attempts_unmeasured"] == "1"
    assert arena.store.latest() == before_quotes
    assert arena.store.db.execute("SELECT * FROM attempts").fetchall() == before_attempt
    assert arena.evaluations()[0]["score"] == {"fixture": "retained-history"}
    assert BehaviorSessions(arena).sessions() == []
    assert arena.evaluate()["database"]["score"] == 1
    arena.close()


def test_unsupported_legacy_tables_are_retained_byte_for_byte(dataset, tmp_path):
    path = tmp_path / "unsupported.sqlite"
    store = QuoteStore(path)
    manifest = json.loads((dataset / "dataset.json").read_text())
    with store.db:
        store.db.execute("CREATE TABLE arena_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        store.db.executemany("INSERT INTO arena_meta VALUES (?,?)", [("schema", "sportsbook-arena/1"), ("dataset_id", manifest["dataset_id"])])
    store.close()
    before = path.read_bytes()
    with pytest.raises(Refusal, match="unsupported arena tables"):
        ArenaStore(path, dataset)
    assert path.read_bytes() == before


def test_concurrent_provider_replay_keeps_one_packet_and_score(dataset, tmp_path):
    path = tmp_path / "concurrent.sqlite"
    arena = ArenaStore(path, dataset)
    session = BehaviorSessions(arena).start(arena.captures()[0]["capture_id"])
    packet = contacts(session, [100])
    arena.close()

    def send(_):
        store = ArenaStore(path, dataset)
        try:
            return BehaviorSessions(store).finish(session["session_id"], packet)
        finally:
            store.close()

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(send, range(4)))
    assert sum(not row["replayed"] for row in results) == 1
    reopened = ArenaStore(path, dataset)
    assert len(BehaviorSessions(reopened).sessions()) == 1
    reopened.close()
