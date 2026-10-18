import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from phone_lab.benchmark import Refusal
from phone_lab.sportsbook.app import create_app, create_red_app
from phone_lab.sportsbook.dataset import build_dataset
from phone_lab.sportsbook.jobs import JobRunner, JobStopped, JobStore, prepare_executor
from phone_lab.sportsbook.pilot import evaluate_dataset

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
SEEDS = {"train": [41, 42], "validation": [141, 142], "test": [241, 242]}


def request(key="first"):
    return {"request_id": key, "kind": "dataset", "seeds": SEEDS}


@pytest.fixture(scope="module")
def executor():
    if not CHROME.is_file():
        pytest.skip("owned Chrome unavailable")
    return prepare_executor(CHROME)


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    if not CHROME.is_file():
        pytest.skip("owned Chrome unavailable")
    root = tmp_path_factory.mktemp("job-dataset") / "dataset"
    build_dataset(root, CHROME, seeds={"train": [7], "validation": [107], "test": [207]})
    return root


def wait_for(store, jid, predicate, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        row = store.get(jid)
        if predicate(row):
            return row
        time.sleep(0.03)
    pytest.fail("job did not reach expected state: " + json.dumps(store.get(jid)))


def test_exact_requests_training_hold_replay_cancel_restart_and_queue_bound(tmp_path, executor):
    store = JobStore(tmp_path / "jobs")
    for bad in ({**request(), "command": "train"}, {"request_id": "train", "kind": "training"},
                {**request(), "seeds": {**SEEDS, "test": [41]}},
                {**request(), "seeds": {**SEEDS, "train": list(range(9))}},
                {**request(), "seeds": {**SEEDS, "test": [True]}}):
        with pytest.raises(Refusal):
            store.enqueue(bad, executor)
    assert not store.rows() and not list((store.root / "runs").iterdir())
    row = store.enqueue(request(), executor)
    assert store.enqueue(request(), executor)["job_id"] == row["job_id"]
    with pytest.raises(Refusal, match="conflicting"):
        store.enqueue({**request(), "seeds": {**SEEDS, "test": [999]}}, executor)
    assert store.cancel(row["job_id"])["state"] == "cancelled"
    restarted = store.restart(row["job_id"], "retry-1")
    assert restarted["job_id"] != row["job_id"] and restarted["restart_of"] == row["job_id"]
    assert restarted["request"]["seeds"] == SEEDS
    assert store.restart(row["job_id"], "retry-1")["job_id"] == restarted["job_id"]
    with pytest.raises(Refusal):
        store.restart(restarted["job_id"], "not-terminal")
    for index in range(15):
        store.enqueue(request("queued-" + str(index)), executor)
    with pytest.raises(Refusal, match="queue"):
        store.enqueue(request("overflow"), executor)
    assert JobStore(store.root).get(row["job_id"])["state"] == "cancelled"


def test_catalog_copies_frozen_inputs_and_refuses_mutation_or_user_paths(tmp_path, dataset, executor):
    store = JobStore(tmp_path / "jobs")
    frozen = store.import_dataset(dataset)
    assert frozen["samples"] == 9
    assert store.import_dataset(dataset)["dataset_id"] == frozen["dataset_id"]
    for value in ("../dataset", str(dataset), "a" * 64):
        with pytest.raises(Refusal):
            store.enqueue({"request_id": "unsafe", "kind": "evaluation", "dataset_id": value}, executor)
    with pytest.raises(Refusal, match="OCR"):
        store.enqueue({"request_id": "no-ocr", "kind": "evaluation", "dataset_id": frozen["dataset_id"]}, executor)
    snapshot = store.dataset_path(frozen["dataset_id"])
    before = hashlib.sha256((dataset / "dataset.json").read_bytes()).hexdigest()
    manifest = json.loads((snapshot / "dataset.json").read_text())
    image = snapshot / manifest["samples"][0]["image"]
    image.write_bytes(b"changed owned fixture")
    with pytest.raises(Refusal):
        store.dataset_path(frozen["dataset_id"])
    assert hashlib.sha256((dataset / "dataset.json").read_bytes()).hexdigest() == before


def test_claim_is_atomic_single_active_job_and_stale_workers_cannot_write(tmp_path, executor):
    store = JobStore(tmp_path / "jobs")
    rows = [store.enqueue(request(str(i)), executor) for i in range(4)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        claims = list(pool.map(lambda _: store.claim(), range(4)))
    active = [c for c in claims if c is not None]
    assert len(active) == 1
    claim = active[0]
    with pytest.raises(Refusal):
        store.progress(claim["job_id"], "bad-lease", 1, 18)
    store.progress(claim["job_id"], claim["lease"], 1, 18)
    with pytest.raises(Refusal):
        store.progress(claim["job_id"], claim["lease"], 0, 18)
    store.terminal(claim["job_id"], claim["lease"], "failed", error="owned test failure")
    with pytest.raises(Refusal):
        store.progress(claim["job_id"], claim["lease"], 2, 18)
    assert store.claim() is not None and len(rows) == 4


def test_real_child_cancel_restart_keeps_artifacts_and_exclusive_owner(tmp_path, executor):
    store = JobStore(tmp_path / "jobs")
    row = store.enqueue(request(), executor)
    runner = JobRunner(store, timeout=60)
    runner.start()
    try:
        with pytest.raises(Refusal, match="owner"):
            JobRunner(JobStore(store.root)).start()
        wait_for(store, row["job_id"], lambda r: r["state"] == "running" and r["completed"] >= 1)
        store.cancel(row["job_id"])
        ended = wait_for(store, row["job_id"], lambda r: r["state"] == "cancelled")
        assert ended["result"] is None and ended["completed"] >= 1
        old = store.root / "runs" / row["job_id"]
        old_files = {str(p.relative_to(old)): p.read_bytes() for p in old.rglob("*") if p.is_file()}
        assert old_files
        retry = store.restart(row["job_id"], "actual-retry")
        done = wait_for(store, retry["job_id"], lambda r: r["state"] in {"succeeded", "failed"}, timeout=60)
        assert done["state"] == "succeeded", done["error"]
        assert done["completed"] == done["total"] == 18
        assert store.dataset_path(done["result"]["dataset_id"]).is_dir()
        assert {str(p.relative_to(old)): p.read_bytes() for p in old.rglob("*") if p.is_file()} == old_files
        assert all("lease" not in r and "executor" not in r for r in store.rows())
    finally:
        runner.stop()
    reopened = JobStore(store.root)
    assert reopened.get(retry["job_id"])["state"] == "succeeded"
    assert reopened.get(row["job_id"])["state"] == "cancelled"


def test_exclusive_recovery_and_source_drift_preserve_unfinished_history(tmp_path, executor, monkeypatch):
    store = JobStore(tmp_path / "jobs")
    row = store.enqueue(request(), executor)
    claim = store.claim()
    runner = JobRunner(store)
    runner.start()
    try:
        assert store.get(row["job_id"])["state"] == "interrupted"
        with pytest.raises(Refusal):
            store.terminal(row["job_id"], claim["lease"], "failed", error="stale")
    finally:
        runner.stop()
    from phone_lab.sportsbook import jobs
    real = jobs.worker_policy("dataset")
    retry = store.restart(row["job_id"], "drift-retry")
    monkeypatch.setattr(jobs, "worker_policy", lambda kind: {**real, "schema": "changed"})
    with pytest.raises(Refusal, match="source"):
        store.execution(retry["job_id"])


def test_blue_job_api_is_bounded_and_completely_absent_on_red(tmp_path, dataset):
    app = create_app(dataset, jobs=tmp_path / "jobs", browser=CHROME)
    blue = TestClient(app)
    assert "Dataset and evaluation jobs" in blue.get("/jobs/").text
    assert blue.post("/api/jobs", json=request()).status_code == 200
    row = blue.get("/api/jobs").json()["jobs"][0]
    assert row["state"] == "queued" and "executor" not in row and "lease" not in row
    assert blue.post("/api/jobs", json={**request("bad"), "command": "train"}).status_code == 422
    assert blue.post("/api/jobs", content=b"x" * 4097).status_code == 413
    assert blue.post("/api/jobs/"+row["job_id"]+"/cancel", json={"reason": "arbitrary"}).status_code == 422
    assert blue.post("/api/jobs/"+row["job_id"]+"/cancel", json={}).json()["state"] == "cancelled"
    retry = blue.post("/api/jobs/"+row["job_id"]+"/restart", json={"request_id": "api-retry"})
    assert retry.status_code == 200 and retry.json()["restart_of"] == row["job_id"]
    red = TestClient(create_red_app(dataset, arena=tmp_path / "round.sqlite"))
    for path in ("/jobs/", "/api/jobs", "/api/jobs/"+row["job_id"], "/jobs/artifacts/"+row["job_id"]+"/dataset/dataset.json"):
        assert red.get(path).status_code == red.post(path, json={}).status_code == 404


def test_runtime_limit_is_terminal_and_never_accepts_partial_artifacts(tmp_path, executor):
    store = JobStore(tmp_path / "jobs")
    row = store.enqueue(request(), executor)
    runner = JobRunner(store, timeout=0.1)
    runner.start()
    try:
        done = wait_for(store, row["job_id"], lambda r: r["state"] == "failed")
        assert done["result"] is None and done["error"] == "runtime budget exceeded"
        assert (store.root / "runs" / row["job_id"]).exists()
        with pytest.raises(Refusal):
            store.artifact(row["job_id"], "worker.log")
    finally:
        runner.stop()


def test_live_child_keeps_exclusive_lease_after_supervisor_death(tmp_path, executor):
    store = JobStore(tmp_path / "jobs")
    seeds = {"train": list(range(10, 18)), "validation": list(range(110, 118)), "test": list(range(210, 218))}
    row = store.enqueue({**request(), "seeds": seeds}, executor)
    script = "import sys,time;from phone_lab.sportsbook.jobs import JobRunner,JobStore;r=JobRunner(JobStore(sys.argv[1]),timeout=30);r.start();time.sleep(40)"
    env = os.environ.copy()
    import phone_lab
    env["PYTHONPATH"] = str(Path(phone_lab.__file__).resolve().parent.parent)
    parent = subprocess.Popen([sys.executable, "-c", script, str(store.root)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_for(store, row["job_id"], lambda r: r["state"] == "running" and r["completed"] >= 1)
        assert parent.poll() is None
        parent.kill()
        parent.wait(timeout=5)
        with pytest.raises(Refusal, match="owner"):
            JobRunner(JobStore(store.root)).start()
        ended = wait_for(store, row["job_id"], lambda r: r["state"] in {"succeeded", "failed"}, timeout=30)
        assert ended["state"] == "succeeded", ended["error"]
        # A terminal SQLite receipt precedes the child releasing its descriptor.
        deadline = time.monotonic() + 5
        while True:
            runner = JobRunner(JobStore(store.root))
            try:
                runner.start()
                break
            except Refusal:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.03)
        runner.stop()
        assert store.get(row["job_id"])["state"] == "succeeded"
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait(timeout=5)


def test_partial_evaluation_cancel_keeps_observation_and_database(dataset, tmp_path):
    output = tmp_path / "cancelled-evaluation"

    def progress(completed, total):
        assert total == 9
        if completed == 1:
            raise JobStopped("owned cancellation fixture")

    with pytest.raises(JobStopped):
        evaluate_dataset(dataset, output, recognize=lambda image: [], provenance={"recognizer": "empty pixel-only fixture"}, progress=progress)
    observations = list((output / "red-observations").glob("*.json"))
    assert len(observations) == 1 and json.loads(observations[0].read_text())["ocr"] == []
    assert json.loads((output / "failure.json").read_text())["type"] == "JobStopped"
    import sqlite3
    db = sqlite3.connect(output / "observations.sqlite")
    assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    db.close()


def test_stop_after_terminal_commit_cannot_reopen_or_reclassify_a_job(tmp_path, executor):
    store = JobStore(tmp_path / "jobs")
    row = store.enqueue(request(), executor)
    claim = store.claim()
    store.terminal(row["job_id"], claim["lease"], "failed", error="original terminal evidence")
    before = store.get(row["job_id"])
    after = store.request_stop(row["job_id"], claim["lease"], "server shutdown")
    assert after == before and store.get(row["job_id"]) == before
    for index in range(8):
        race = store.enqueue(request("finish-race-" + str(index)), executor)
        claim = store.claim()
        with ThreadPoolExecutor(max_workers=2) as pool:
            finish = pool.submit(store.terminal, race["job_id"], claim["lease"], "failed", error="original worker failure")
            stop = pool.submit(store.request_stop, race["job_id"], claim["lease"], "server shutdown")
            finish.result()
            stop.result()
        assert store.get(race["job_id"])["state"] in {"failed", "interrupted"}
