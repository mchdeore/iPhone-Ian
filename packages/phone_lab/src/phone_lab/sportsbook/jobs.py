"""Owned local jobs; no training, arbitrary commands, remote input or shared hosting."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import secrets
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ..benchmark import Refusal
from ..training_policy import read_policy
from .dataset import _inside, _seeds, audit_dataset

ACTIVE = {"queued", "running", "cancelling"}
TERMINAL = {"succeeded", "failed", "cancelled", "interrupted"}
MAX_BYTES = 64 * 1024 * 1024


class JobStopped(RuntimeError):
    pass


def _now():
    return datetime.now(ZoneInfo("America/Toronto")).isoformat()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _id(value, length):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{" + str(length) + "}", value):
        raise Refusal("owned artifact identity required")
    return value


def _key(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 80 or not value.isascii() or not value.isprintable():
        raise Refusal("bounded printable replay key required")
    return value


def prepare_executor(browser=None, ocr=None, ocr_sha256=None):
    def executable(path, digest=None):
        if path is None:
            return None
        path = Path(path).resolve()
        if not path.is_file() or not os.access(path, os.X_OK):
            raise Refusal("configured executable unavailable")
        actual = _sha(path)
        if digest is not None and digest != actual:
            raise Refusal("reviewed OCR executable digest mismatch")
        return {"path": str(path), "sha256": actual}

    if ocr is not None and not isinstance(ocr_sha256, str):
        raise Refusal("reviewed OCR digest required")
    return {"schema": "owned-job-executor/1", "chrome": executable(browser),
            "ocr": executable(ocr, ocr_sha256)}


def worker_policy(kind):
    source = Path(__file__).parent
    names = ("jobs.py", "job_worker.py", "dataset.py", "contracts.py", "fixtures.py", "pages.py",
             "pilot.py", "extract.py", "evaluation.py", "reports.py", "storage.py")
    return {"schema": "owned-job-source/1", "kind": kind, "training": read_policy(),
            "source_sha256": {name: _sha(source / name) for name in names},
            "helper_sha256": {name: _sha(source.parent / name) for name in ("benchmark.py", "metrics.py", "training_policy.py", "training-policy.json")}}


class JobStore:
    def __init__(self, root):
        root = Path(root)
        if root.is_symlink():
            raise Refusal("job root symlink refused")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.root = root.resolve()
        for name in ("runs", "imports"):
            path = self.root / name
            if path.is_symlink():
                raise Refusal("job folder symlink refused")
            path.mkdir(exist_ok=True, mode=0o700)
        self.path = self.root / "jobs.sqlite"
        if self.path.is_symlink():
            raise Refusal("job database symlink refused")
        new = not self.path.exists()
        with self._db() as db:
            if not new:
                try:
                    if dict(db.execute("SELECT key,value FROM job_meta")).get("schema") != "blue-jobs/1":
                        raise Refusal("unsupported job database; preserve original")
                except sqlite3.Error:
                    raise Refusal("unsupported job database; preserve original") from None
            else:
                db.executescript('''BEGIN IMMEDIATE;
CREATE TABLE job_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
INSERT INTO job_meta VALUES('schema','blue-jobs/1');
CREATE TABLE datasets(dataset_id TEXT PRIMARY KEY,path TEXT NOT NULL,samples INTEGER NOT NULL,manifest_sha256 TEXT NOT NULL);
CREATE TABLE jobs(job_id TEXT PRIMARY KEY,request_id TEXT UNIQUE NOT NULL,kind TEXT NOT NULL,request TEXT NOT NULL,
executor TEXT NOT NULL,policy TEXT NOT NULL,spec_sha256 TEXT NOT NULL,restart_of TEXT REFERENCES jobs(job_id),
created_at TEXT NOT NULL,started_at TEXT,ended_at TEXT,state TEXT NOT NULL,completed INTEGER NOT NULL,total INTEGER NOT NULL,
lease TEXT,error TEXT,result TEXT,stop_reason TEXT);
COMMIT;''')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
        finally:
            db.close()

    def _row(self, db, jid):
        row = db.execute("SELECT * FROM jobs WHERE job_id=?", (_id(jid, 32),)).fetchone()
        if row is None:
            raise Refusal("unknown owned job")
        return dict(row)

    def _public(self, row):
        return {key: json.loads(value) if key in {"request", "policy", "result"} and value is not None else value
                for key, value in row.items() if key not in {"executor", "lease", "stop_reason"}}

    def get(self, jid):
        with self._db() as db:
            return self._public(self._row(db, jid))

    def rows(self):
        with self._db() as db:
            return [self._public(dict(row)) for row in db.execute("SELECT * FROM jobs ORDER BY rowid DESC")]

    def datasets(self):
        with self._db() as db:
            return [{key: row[key] for key in ("dataset_id", "samples", "manifest_sha256")} for row in db.execute("SELECT * FROM datasets ORDER BY rowid")]

    def dataset_path(self, did):
        with self._db() as db:
            row = db.execute("SELECT * FROM datasets WHERE dataset_id=?", (_id(did, 24),)).fetchone()
        if row is None:
            raise Refusal("unknown frozen dataset")
        path = _inside(self.root, row["path"])
        if _sha(path / "dataset.json") != row["manifest_sha256"]:
            raise Refusal("frozen dataset manifest changed")
        audit_dataset(path)
        return path

    def import_dataset(self, source):
        source = Path(source)
        audit_dataset(source)
        manifest = json.loads((source / "dataset.json").read_text())
        did = _id(manifest["dataset_id"], 24)
        if not 1 <= len(manifest["samples"]) <= 288:
            raise Refusal("dataset sample budget exceeded")
        files = {"dataset.json", "dataset.yaml", "audit.json"}
        for row in manifest["samples"]:
            files.update(row[key] for key in ("image", "annotation", "labels", "provider_truth", "source_page"))
        if sum(_inside(source, rel).stat().st_size for rel in files) > MAX_BYTES:
            raise Refusal("dataset byte budget exceeded")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT * FROM datasets WHERE dataset_id=?", (did,)).fetchone()
            if existing:
                db.execute("COMMIT")
                self.dataset_path(did)
                return {key: existing[key] for key in ("dataset_id", "samples", "manifest_sha256")}
            path = self.root / "imports" / secrets.token_hex(16)
            path.mkdir(mode=0o700)
            for rel in sorted(files):
                target = path / rel
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with target.open("xb") as handle:
                    handle.write(_inside(source, rel).read_bytes())
            audit_dataset(path)
            sha = _sha(path / "dataset.json")
            db.execute("INSERT INTO datasets VALUES(?,?,?,?)", (did, str(path.relative_to(self.root)), len(manifest["samples"]), sha))
            db.execute("COMMIT")
        return {"dataset_id": did, "samples": len(manifest["samples"]), "manifest_sha256": sha}

    def enqueue(self, request, executor, *, restart_of=None, policy=None):
        if not isinstance(request, dict):
            raise Refusal("exact owned job request required")
        kind = request.get("kind")
        fields = {"request_id", "kind", "seeds" if kind == "dataset" else "dataset_id"}
        if kind not in {"dataset", "evaluation"} or set(request) != fields:
            raise Refusal("only dataset capture and native OCR evaluation jobs are allowed; training held")
        key = _key(request["request_id"])
        request = json.loads(_json(request))
        with self._db() as db:
            old = db.execute("SELECT * FROM jobs WHERE request_id=?", (key,)).fetchone()
            if old:
                if old["request"] != _json(request) or old["restart_of"] != restart_of:
                    raise Refusal("conflicting job replay")
                return self._public(dict(old))
        if not isinstance(executor, dict) or executor.get("schema") != "owned-job-executor/1" or set(executor) != {"schema", "chrome", "ocr"}:
            raise Refusal("reviewed executor configuration required")
        if kind == "dataset":
            _seeds(request["seeds"])
            if any(len(seeds) > 8 for seeds in request["seeds"].values()):
                raise Refusal("job split seed budget exceeded")
            if executor["chrome"] is None:
                raise Refusal("configured Chrome unavailable")
            total = 3 * sum(map(len, request["seeds"].values()))
        else:
            if executor["ocr"] is None:
                raise Refusal("reviewed OCR unavailable")
            manifest = json.loads((self.dataset_path(request["dataset_id"]) / "dataset.json").read_text())
            total = len(manifest["samples"])
        policy = policy if policy is not None else worker_policy(kind)
        spec = _json({"request": request, "executor": executor, "policy": policy})
        jid = secrets.token_hex(16)
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM jobs WHERE request_id=?", (key,)).fetchone()
            if old:
                if old["request"] != _json(request) or old["restart_of"] != restart_of:
                    raise Refusal("conflicting job replay")
                db.execute("COMMIT")
                return self._public(dict(old))
            if db.execute("SELECT count(*) FROM jobs WHERE state IN ('queued','running','cancelling')").fetchone()[0] >= 16:
                raise Refusal("owned job queue limit reached")
            db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (jid, key, kind, _json(request), _json(executor), _json(policy), hashlib.sha256(spec.encode()).hexdigest(),
                        restart_of, _now(), None, None, "queued", 0, total, None, None, None, None))
            db.execute("COMMIT")
        return self.get(jid)

    def restart(self, jid, key):
        with self._db() as db:
            row = self._row(db, jid)
        if row["state"] not in {"failed", "cancelled", "interrupted"}:
            raise Refusal("restart requires a failed, cancelled or interrupted job")
        request = {**json.loads(row["request"]), "request_id": _key(key)}
        return self.enqueue(request, json.loads(row["executor"]), restart_of=jid, policy=json.loads(row["policy"]))

    def cancel(self, jid):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._row(db, jid)
            if row["state"] == "queued":
                db.execute("UPDATE jobs SET state='cancelled',ended_at=?,stop_reason='operator cancel' WHERE job_id=?", (_now(), jid))
            elif row["state"] == "running":
                db.execute("UPDATE jobs SET state='cancelling',stop_reason='operator cancel' WHERE job_id=?", (jid,))
            db.execute("COMMIT")
        return self.get(jid)

    def claim(self):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM jobs WHERE state IN ('running','cancelling')").fetchone():
                return None
            row = db.execute("SELECT job_id FROM jobs WHERE state='queued' ORDER BY rowid LIMIT 1").fetchone()
            if row is None:
                return None
            lease = secrets.token_hex(16)
            db.execute("UPDATE jobs SET state='running',lease=?,started_at=? WHERE job_id=?", (lease, _now(), row["job_id"]))
            result = self._row(db, row["job_id"])
            db.execute("COMMIT")
            return result

    def _owned(self, db, jid, lease):
        row = self._row(db, jid)
        if row["lease"] != lease or row["state"] not in {"running", "cancelling"}:
            raise Refusal("stale job worker lease")
        return row

    def progress(self, jid, lease, completed, total):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._owned(db, jid, lease)
            if row["state"] == "cancelling":
                raise JobStopped("job stop requested")
            if type(completed) is not int or type(total) is not int or total != row["total"] or not row["completed"] <= completed <= total:
                raise Refusal("job progress must stay within its frozen sample count")
            db.execute("UPDATE jobs SET completed=? WHERE job_id=?", (completed, jid))
            db.execute("COMMIT")

    def execution(self, jid):
        with self._db() as db:
            row = self._row(db, jid)
        request, executor, policy = (json.loads(row[key]) for key in ("request", "executor", "policy"))
        spec = _json({"request": request, "executor": executor, "policy": policy})
        if hashlib.sha256(spec.encode()).hexdigest() != row["spec_sha256"] or policy != worker_policy(row["kind"]):
            raise Refusal("frozen job source or request changed")
        for value in executor.values():
            if isinstance(value, dict) and (not Path(value["path"]).is_file() or _sha(value["path"]) != value["sha256"]):
                raise Refusal("frozen executable changed or unavailable")
        if row["kind"] == "evaluation":
            self.dataset_path(request["dataset_id"])
        return {"request": request, "executor": executor, "policy": policy}

    def request_stop(self, jid, lease, reason):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._row(db, jid)
            if row["lease"] != lease:
                raise Refusal("stale job worker lease")
            if row["state"] == "running":
                db.execute("UPDATE jobs SET state='cancelling',stop_reason=? WHERE job_id=? AND lease=?", (reason, jid, lease))
            db.execute("COMMIT")
        return self.get(jid)

    def _artifacts(self, jid):
        run = _inside(self.root, "runs/" + _id(jid, 32))
        files, size = {}, 0
        for path in sorted(run.rglob("*")):
            if path.is_symlink():
                raise Refusal("job artifact symlink refused")
            if path.is_file():
                size += path.stat().st_size
                if size > MAX_BYTES or len(files) >= 2048:
                    raise Refusal("job artifact budget exceeded")
                files[str(path.relative_to(run))] = {"sha256": _sha(path), "bytes": path.stat().st_size}
        return files

    def check_budget(self, jid):
        run = _inside(self.root, "runs/" + _id(jid, 32))
        size, count = 0, 0
        for path in run.rglob("*"):
            if path.is_symlink():
                raise Refusal("job artifact symlink refused")
            if path.is_file():
                size += path.stat().st_size
                count += 1
                if size > MAX_BYTES or count > 2048:
                    raise Refusal("job artifact budget exceeded")

    def terminal(self, jid, lease, state, *, error=None, result=None):
        if state not in TERMINAL:
            raise Refusal("terminal job state required")
        if state == "succeeded":
            result = {**result, "files": self._artifacts(jid)}
            if not result["files"]:
                raise Refusal("accepted job has no artifacts")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._owned(db, jid, lease)
            if row["state"] == "cancelling":
                state = {"operator cancel": "cancelled", "server shutdown": "interrupted"}.get(row["stop_reason"], "failed")
                error, result = row["stop_reason"], None
            if state == "succeeded":
                if row["completed"] != row["total"]:
                    raise Refusal("accepted job progress incomplete")
                if row["kind"] == "dataset":
                    path = _inside(self.root, "runs/" + jid + "/dataset")
                    audit_dataset(path)
                    manifest = json.loads((path / "dataset.json").read_text())
                    if result["dataset_id"] != manifest["dataset_id"] or len(manifest["samples"]) != row["total"]:
                        raise Refusal("accepted dataset differs from frozen job")
                    db.execute("INSERT OR IGNORE INTO datasets VALUES(?,?,?,?)", (manifest["dataset_id"], str(path.relative_to(self.root)), row["total"], _sha(path / "dataset.json")))
            db.execute("UPDATE jobs SET state=?,ended_at=?,error=?,result=? WHERE job_id=?",
                       (state, _now(), str(error)[:500] if error is not None else None, _json(result) if result is not None else None, jid))
            db.execute("COMMIT")
        return self.get(jid)

    def _recover_exclusive(self):
        with self._db() as db:
            db.execute("UPDATE jobs SET state='interrupted',ended_at=?,error='worker lease no longer held; original artifacts retained' WHERE state IN ('running','cancelling')", (_now(),))

    def artifact(self, jid, relative):
        row = self.get(jid)
        if row["state"] != "succeeded" or relative not in row["result"]["files"]:
            raise Refusal("accepted artifact required")
        path = _inside(self.root, "runs/" + jid + "/" + relative)
        if _sha(path) != row["result"]["files"][relative]["sha256"]:
            raise Refusal("accepted artifact changed")
        return path


class JobRunner:
    """One leased child at a time; child retains the owner lock after parent death."""

    def __init__(self, store, *, timeout=120):
        if not 0 < timeout <= 600:
            raise Refusal("bounded job runtime required")
        self.store, self.timeout = store, timeout
        self._fd, self._thread = None, None
        self._stop = threading.Event()
        self.last_error = None

    def start(self):
        if self._fd is not None:
            raise Refusal("job owner already active")
        path = self.store.root / "owner.lock"
        if path.is_symlink():
            raise Refusal("job owner lock symlink refused")
        fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            raise Refusal("another job owner or child remains live") from None
        self._fd = fd
        self.store._recover_exclusive()
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="owned-blue-jobs")
        self._thread.start()

    def stop(self):
        if self._fd is None:
            return
        self._stop.set()
        self._thread.join(timeout=8)
        if self._thread.is_alive():
            raise Refusal("job child still live; owner lease retained")
        os.close(self._fd)
        self._fd = None

    def _loop(self):
        try:
            while not self._stop.is_set():
                claim = self.store.claim()
                if claim is not None:
                    self._run(claim)
                else:
                    self._stop.wait(0.05)
        except Exception as error:
            self.last_error = type(error).__name__

    def _run(self, claim):
        jid, lease = claim["job_id"], claim["lease"]
        try:
            self.store.execution(jid)
            run = self.store.root / "runs" / jid
            run.mkdir(mode=0o700)
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
            with (run / "worker.log").open("xb") as log:
                child = subprocess.Popen([sys.executable, "-m", "phone_lab.sportsbook.job_worker", str(self.store.root), jid, lease],
                                         cwd=run, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, pass_fds=(self._fd,))
                started, signalled = time.monotonic(), None
                while child.poll() is None:
                    row = self.store.get(jid)
                    reason = "server shutdown" if self._stop.is_set() else "runtime budget exceeded" if time.monotonic() - started > self.timeout else "log byte budget exceeded" if (run / "worker.log").stat().st_size > 2 * 1024 * 1024 else None
                    if reason and row["state"] == "running":
                        self.store.request_stop(jid, lease, reason)
                        row = self.store.get(jid)
                    if row["state"] == "cancelling" and signalled is None:
                        try:
                            child.send_signal(signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                        signalled = time.monotonic()
                    if signalled is not None and time.monotonic() - signalled > 5:
                        try:
                            os.killpg(child.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    time.sleep(0.03)
                child.wait()
            if self.store.get(jid)["state"] in {"running", "cancelling"}:
                self.store.terminal(jid, lease, "failed", error="worker exited without a terminal receipt")
        except Exception as error:
            if self.store.get(jid)["state"] in {"running", "cancelling"}:
                self.store.terminal(jid, lease, "failed", error=str(error) if isinstance(error, Refusal) else type(error).__name__)
