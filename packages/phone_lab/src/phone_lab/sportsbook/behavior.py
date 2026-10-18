"""Frozen descriptive Blue scoring over provider-visible pointer contacts only."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

from ..benchmark import Refusal
from ..blue import score_contacts
from .storage import encoded

SESSION_COLUMNS = ("id", "capture_id", "image_sha256", "viewport", "policy", "started_at", "state",
                   "closed_at", "packet_sha256", "packet", "score", "cancel_reason")


def _now():
    return datetime.now(ZoneInfo("America/Toronto")).isoformat()


def frozen_scorer():
    root = Path(__file__).parents[1]
    components = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                  for name in ("blue.py", "metrics.py", "benchmark.py")}
    return {"schema": "blue-frozen-scorer/1", "version": "declared-contact-patterns/1", "components": components,
            "boundary": "provider-only packet; no labels, entered text, camera, motors or model observations",
            "human_validation": "pending consented controls", "sanctions": False}


def initialize_behavior(db):
    """Caller owns the schema transaction. Earlier observations stay unmeasured."""
    db.execute("CREATE TABLE provider_sessions(id TEXT PRIMARY KEY,capture_id TEXT NOT NULL,image_sha256 TEXT NOT NULL,viewport TEXT NOT NULL,policy TEXT NOT NULL,started_at TEXT NOT NULL,state TEXT NOT NULL,closed_at TEXT,packet_sha256 TEXT,packet TEXT,score TEXT,cancel_reason TEXT,FOREIGN KEY(capture_id) REFERENCES challenges(id))")
    db.execute("CREATE TABLE provider_attempt_links(session_id TEXT,attempt_id TEXT,created_at TEXT NOT NULL,PRIMARY KEY(session_id,attempt_id),FOREIGN KEY(session_id) REFERENCES provider_sessions(id),FOREIGN KEY(attempt_id) REFERENCES attempts(id))")
    db.executemany("INSERT INTO arena_meta VALUES (?,?)", [("blue_policy", encoded(frozen_scorer())), ("blue_frozen_at", _now()),
                                                          ("blue_prior_attempts_unmeasured", str(db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]))])


class BehaviorSessions:
    def __init__(self, arena):
        self.arena, self.db = arena, arena.store.db

    def _policy(self):
        policy = json.loads(self.arena.meta["blue_policy"])
        if policy != frozen_scorer():
            raise Refusal("frozen Blue scorer changed; start a fresh round with the reviewed version")
        return policy

    def _row(self, session_id):
        if not isinstance(session_id, str) or not re.fullmatch(r"[0-9a-f]{32}", session_id):
            raise Refusal("provider session identity required")
        row = self.db.execute("SELECT * FROM provider_sessions WHERE id=?", (session_id,)).fetchone()
        if row is None:
            raise Refusal("unknown provider session")
        result = dict(zip(SESSION_COLUMNS, row))
        result["session_id"] = result.pop("id")
        for name in ("viewport", "policy", "packet", "score"):
            if result[name] is not None:
                result[name] = json.loads(result[name])
        result["attempt_links"] = [r[0] for r in self.db.execute("SELECT attempt_id FROM provider_attempt_links WHERE session_id=? ORDER BY created_at,attempt_id", (session_id,))]
        return result

    def start(self, capture_id):
        if not isinstance(capture_id, str) or not re.fullmatch(r"[0-9a-f]{64}", capture_id):
            raise Refusal("capture hash required")
        policy = self._policy()
        image = self.arena.image(capture_id)
        with Image.open(image) as pixels:
            viewport = list(pixels.size)
        if any(not 1 <= size <= 4096 for size in viewport):
            raise Refusal("provider viewport budget")
        session_id = secrets.token_hex(16)
        with self.db:
            self.db.execute("INSERT INTO provider_sessions(id,capture_id,image_sha256,viewport,policy,started_at,state) VALUES (?,?,?,?,?,?,?)",
                            (session_id, capture_id, hashlib.sha256(image.read_bytes()).hexdigest(), encoded(viewport), encoded(policy), _now(), "open"))
        return self._row(session_id)

    def finish(self, session_id, packet):
        try:
            raw = encoded(packet)
        except (TypeError, ValueError):
            raise Refusal("JSON provider packet required") from None
        if len(raw.encode()) > 1048576:
            raise Refusal("provider packet byte budget")
        digest = hashlib.sha256(raw.encode()).hexdigest()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            session = self._row(session_id)
            if session["state"] != "open":
                if session["state"] != "closed" or session["packet_sha256"] != digest:
                    raise Refusal("conflicting provider session replay")
                return {"session_id": session_id, "score": session["score"], "replayed": True}
            self._policy()
            # The scorer sees this narrow provider packet, never scene truth or Red output.
            score = score_contacts(packet)
            if packet["run_id"] != session_id or packet["viewport"] != session["viewport"]:
                raise Refusal("provider session or viewport mismatch")
            self.arena.image(session["capture_id"])
            self.db.execute("UPDATE provider_sessions SET state='closed',closed_at=?,packet_sha256=?,packet=?,score=? WHERE id=?",
                            (_now(), digest, raw, encoded(score), session_id))
        return {"session_id": session_id, "score": score, "replayed": False}

    def cancel(self, session_id, reason):
        if not isinstance(reason, str) or not 1 <= len(reason) <= 500 or not reason.isprintable():
            raise Refusal("bounded cancellation reason required")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            session = self._row(session_id)
            if session["state"] != "open":
                if session["state"] == "cancelled" and session["cancel_reason"] == reason:
                    return {"session_id": session_id, "state": "cancelled", "replayed": True}
                raise Refusal("conflicting provider session cancellation")
            self.db.execute("UPDATE provider_sessions SET state='cancelled',closed_at=?,cancel_reason=? WHERE id=?", (_now(), reason, session_id))
        return {"session_id": session_id, "state": "cancelled", "replayed": False}

    def link(self, session_id, attempt_id):
        if not isinstance(attempt_id, str) or not 1 <= len(attempt_id) <= 80 or not attempt_id.isascii() or not attempt_id.isprintable():
            raise Refusal("bounded saved attempt identity required")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            session = self._row(session_id)
            attempt = self.db.execute("SELECT capture_id FROM attempts WHERE id=?", (attempt_id,)).fetchone()
            if session["state"] == "open" or attempt is None or attempt[0] != session["capture_id"]:
                raise Refusal("closed provider session and saved attempt must refer to the same capture")
            prior = self.db.execute("SELECT 1 FROM provider_attempt_links WHERE session_id=? AND attempt_id=?", (session_id, attempt_id)).fetchone()
            if prior is None:
                self.db.execute("INSERT INTO provider_attempt_links VALUES (?,?,?)", (session_id, attempt_id, _now()))
        return {"session_id": session_id, "attempt_id": attempt_id, "replayed": prior is not None}

    def sessions(self):
        return [self._row(row[0]) for row in self.db.execute("SELECT id FROM provider_sessions ORDER BY rowid")]
