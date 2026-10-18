"""Local, training-free round coordination; actor submissions precede evaluator truth."""

from __future__ import annotations

import hashlib
import json
import math
import re
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ..benchmark import Refusal
from .behavior import initialize_behavior
from .contracts import quote_key
from .dataset import _inside, audit_dataset
from .reports import operation_registry
from .storage import QuoteStore, encoded, identity, score_database

SCHEMA = "sportsbook-arena/2"
OPERATIONS = set(operation_registry())
ATTEMPT_FIELDS = {"attempt_id", "capture_id", "image_sha256", "actor_id", "model_sha256", "parser_version",
                  "latency_ms", "quotes", "refusals", "retry_of"}


def _text(value, maximum=80):
    if not isinstance(value, str) or not 1 <= len(value) <= maximum or not value.isascii() or not value.isprintable():
        raise Refusal("bounded printable identifier required")
    return value


def _hash(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise Refusal("SHA-256 required")
    return value


def _now():
    return datetime.now(ZoneInfo("America/Toronto")).isoformat()


class ArenaStore:
    """One frozen local round per owned database, with explicit retries and durable scores."""

    def __init__(self, path, root):
        self.root, path = Path(root), Path(path)
        audit_dataset(self.root)
        self.manifest = json.loads((self.root / "dataset.json").read_text())
        self.samples = {row["sample_id"]: row for row in self.manifest["samples"]}
        new = not path.exists()
        legacy = False
        if path.is_symlink():
            raise Refusal("arena database symlink refused")
        if not new:
            try:
                db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
                try:
                    meta = dict(db.execute("SELECT key,value FROM arena_meta"))
                    if meta.get("schema") not in ("sportsbook-arena/1", SCHEMA) or meta.get("dataset_id") != self.manifest["dataset_id"]:
                        raise Refusal("arena schema or frozen dataset mismatch; original retained")
                    legacy = meta["schema"] == "sportsbook-arena/1"
                    required = {"arena_meta": {"key", "value"}, "challenges": {"id", "sample_id", "image_sha256"},
                                "attempts": {"seq", "id", "capture_id", "payload_sha256", "payload", "result", "created_at"},
                                "evaluations": {"seq", "attempt_seq", "score", "created_at"}}
                    if any({row[1] for row in db.execute(f"PRAGMA table_info({table})")} != columns for table, columns in required.items()):
                        raise Refusal("unsupported arena tables; original retained")
                finally:
                    db.close()
            except sqlite3.DatabaseError:
                raise Refusal("foreign arena database retained unchanged") from None
        self.store = QuoteStore(path)
        db = self.store.db
        if new:
            with db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("CREATE TABLE arena_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
                db.execute("CREATE TABLE challenges(id TEXT PRIMARY KEY,sample_id TEXT UNIQUE NOT NULL,image_sha256 TEXT NOT NULL)")
                db.execute("CREATE TABLE attempts(seq INTEGER PRIMARY KEY,id TEXT UNIQUE NOT NULL,capture_id TEXT NOT NULL,payload_sha256 TEXT NOT NULL,payload TEXT NOT NULL,result TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(capture_id) REFERENCES challenges(id))")
                db.execute("CREATE TABLE evaluations(seq INTEGER PRIMARY KEY,attempt_seq INTEGER NOT NULL,score TEXT NOT NULL,created_at TEXT NOT NULL)")
                db.executemany("INSERT INTO arena_meta VALUES (?,?)", [("schema", SCHEMA), ("dataset_id", self.manifest["dataset_id"]), ("run_id", secrets.token_hex(16))])
                db.executemany("INSERT INTO challenges VALUES (?,?,?)", [(secrets.token_hex(32), row["sample_id"], row["sha256"]["image"]) for row in self.samples.values()])
                initialize_behavior(db)
        elif legacy:
            with db:
                db.execute("BEGIN IMMEDIATE")
                # Another connection may have completed this migration while we waited.
                if db.execute("SELECT value FROM arena_meta WHERE key='schema'").fetchone()[0] == "sportsbook-arena/1":
                    initialize_behavior(db)
                    db.execute("UPDATE arena_meta SET value=? WHERE key='schema'", (SCHEMA,))
        self.meta = dict(db.execute("SELECT key,value FROM arena_meta"))

    def captures(self):
        return [{"capture_id": cid, "image_sha256": sha, "image_url": "/images/" + cid}
                for cid, sha in self.store.db.execute("SELECT id,image_sha256 FROM challenges ORDER BY id")]

    def sample(self, capture_id):
        row = self.store.db.execute("SELECT sample_id FROM challenges WHERE id=?", (capture_id,)).fetchone()
        if row is None:
            raise Refusal("unknown round capture")
        return self.samples[row[0]]

    def image(self, capture_id):
        sample = self.sample(capture_id)
        path = _inside(self.root, sample["image"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != sample["sha256"]["image"]:
            raise Refusal("capture pixels changed after registration")
        return path

    def submit(self, payload):
        if not isinstance(payload, dict) or set(payload) != ATTEMPT_FIELDS:
            raise Refusal("exact attempt fields required")
        for field in ("attempt_id", "actor_id", "parser_version"):
            _text(payload[field])
        _hash(payload["capture_id"])
        _hash(payload["image_sha256"])
        if payload["model_sha256"] is not None:
            _hash(payload["model_sha256"])
        ms = payload["latency_ms"]
        if isinstance(ms, bool) or not isinstance(ms, (int, float)) or not math.isfinite(ms) or not 0 <= ms <= 600000:
            raise Refusal("bounded finite latency required")
        if not isinstance(payload["quotes"], list) or len(payload["quotes"]) > 1000:
            raise Refusal("quote budget exceeded")
        if not isinstance(payload["refusals"], list) or len(payload["refusals"]) > 100:
            raise Refusal("refusal budget exceeded")
        for refusal in payload["refusals"]:
            if (not isinstance(refusal, dict) or set(refusal) != {"operation", "reason"}
                    or not isinstance(refusal["operation"], str) or refusal["operation"] not in OPERATIONS):
                raise Refusal("typed operation refusal required")
            _text(refusal["reason"], 500)
        self.image(payload["capture_id"])
        if self.sample(payload["capture_id"])["sha256"]["image"] != payload["image_sha256"]:
            raise Refusal("image commitment mismatch")
        try:
            raw = encoded(payload)
        except (TypeError, ValueError):
            raise Refusal("JSON attempt required") from None
        if len(raw.encode()) > 262144:
            raise Refusal("attempt byte budget exceeded")
        digest = hashlib.sha256(raw.encode()).hexdigest()
        db = self.store.db
        with db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute("SELECT payload_sha256,result FROM attempts WHERE id=?", (payload["attempt_id"],)).fetchone()
            if prior:
                if prior[0] != digest:
                    raise Refusal("conflicting attempt replay")
                return dict(json.loads(prior[1]), replayed=True)
            retry = payload["retry_of"]
            if retry is not None:
                _text(retry)
                prior = db.execute("SELECT capture_id,payload FROM attempts WHERE id=?", (retry,)).fetchone()
                if prior is None or prior[0] != payload["capture_id"] or json.loads(prior[1])["actor_id"] != payload["actor_id"]:
                    raise Refusal("retry must reference an earlier attempt by this actor on this capture")
            elif db.execute("SELECT 1 FROM attempts WHERE capture_id=? AND json_extract(payload,'$.actor_id')=?", (payload["capture_id"], payload["actor_id"])).fetchone():
                raise Refusal("another attempt on this capture requires an explicit retry reference")
            result = {"attempt_id": payload["attempt_id"], "status": "refused" if payload["refusals"] else "empty", "ingest": None, "replayed": False}
            if payload["quotes"]:
                db.execute("SAVEPOINT quote_batch")
                try:
                    result["ingest"] = self.store._ingest(identity([self.meta["run_id"], payload["attempt_id"]]), payload["quotes"],
                                                          model_sha256=payload["model_sha256"], parser_version=payload["parser_version"])
                    result["status"] = "partial" if payload["refusals"] else "accepted"
                except Refusal as error:
                    db.execute("ROLLBACK TO quote_batch")
                    result.update(status="refused", reason=str(error))
                finally:
                    db.execute("RELEASE quote_batch")
            db.execute("INSERT INTO attempts(id,capture_id,payload_sha256,payload,result,created_at) VALUES (?,?,?,?,?,?)",
                       (payload["attempt_id"], payload["capture_id"], digest, raw, encoded(result), _now()))
        return result

    def attempts(self):
        return [{"seq": seq, "payload": json.loads(payload), "result": json.loads(result), "created_at": at}
                for seq, payload, result, at in self.store.db.execute("SELECT seq,payload,result,created_at FROM attempts ORDER BY seq")]

    def evaluate(self):
        """Called separately after submissions commit; reopens the database for scoring."""
        if self.store.db.in_transaction:
            raise Refusal("evaluation requires committed actor observations")
        db = self.store.db
        # Lock the round snapshot against a concurrent submission while selecting truth and scoring.
        db.execute("BEGIN IMMEDIATE")
        try:
            attempts = self.attempts()
            expected = {}
            for sample_id, in db.execute("SELECT DISTINCT c.sample_id FROM attempts a JOIN challenges c ON a.capture_id=c.id"):
                sample = self.samples[sample_id]
                truth = json.loads(_inside(self.root, sample["provider_truth"]).read_text())
                for quote in truth["quotes"]:
                    key = quote_key(quote)
                    if key not in expected or expected[key]["quote_time"] < quote["quote_time"]:
                        expected[key] = quote
            reopened = QuoteStore(self.store.path)
            try:
                score = score_database(reopened, list(expected.values())) if expected else None
            finally:
                reopened.close()
            result = {"schema": "sportsbook-arena-score/1", "attempts": len(attempts), "database": score,
                      "scope": "round aggregate of saved quotes and latest truth from every attempted capture, including empty and refused attempts; not per-actor attribution",
                      "training": "held; no training performed by this coordinator"}
            db.execute("INSERT INTO evaluations(attempt_seq,score,created_at) VALUES (?,?,?)", (attempts[-1]["seq"] if attempts else 0, encoded(result), _now()))
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise

    def evaluations(self):
        return [{"attempt_seq": seq, "score": json.loads(score), "created_at": at}
                for seq, score, at in self.store.db.execute("SELECT attempt_seq,score,created_at FROM evaluations ORDER BY seq")]

    def close(self):
        self.store.close()
