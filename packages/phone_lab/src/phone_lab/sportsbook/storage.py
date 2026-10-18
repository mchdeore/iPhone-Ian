from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from pathlib import Path

from ..benchmark import Refusal
from .contracts import FIELDS, PROVIDERS, quote_key, validate_quote

APPLICATION_ID = 0x49414E53


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def identity(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


class QuoteStore:
    """Versioned local observations; immutable quote history and monotone latest state."""

    def __init__(self, path):
        self.path = Path(path)
        if self.path.is_symlink():
            raise Refusal("database symlink refused")
        new = not self.path.exists()
        if not new:
            try:
                readonly = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
                try:
                    if readonly.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID or readonly.execute("PRAGMA user_version").fetchone()[0] != 1:
                        raise Refusal("foreign database retained unchanged")
                finally:
                    readonly.close()
            except sqlite3.DatabaseError:
                raise Refusal("unsupported database retained unchanged") from None
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            os.close(fd)
        self.db = sqlite3.connect(self.path, timeout=5)
        self.db.execute("PRAGMA foreign_keys=ON")
        if new:
            self.db.executescript(f"""
PRAGMA application_id={APPLICATION_ID}; PRAGMA user_version=1;
CREATE TABLE providers(id TEXT PRIMARY KEY);
CREATE TABLE events(provider TEXT, event_id TEXT, home TEXT, away TEXT, start_time TEXT,
 PRIMARY KEY(provider,event_id), FOREIGN KEY(provider) REFERENCES providers(id));
CREATE TABLE markets(id TEXT PRIMARY KEY, provider TEXT, event_id TEXT, market TEXT, period TEXT,
 FOREIGN KEY(provider,event_id) REFERENCES events(provider,event_id));
CREATE TABLE selections(id TEXT PRIMARY KEY, market_id TEXT, name TEXT,
 FOREIGN KEY(market_id) REFERENCES markets(id));
CREATE TABLE captures(id TEXT PRIMARY KEY, payload_sha256 TEXT NOT NULL, model_sha256 TEXT, parser_version TEXT NOT NULL);
CREATE TABLE observations(capture_id TEXT, row_id TEXT, quote_time TEXT, payload TEXT,
 PRIMARY KEY(capture_id,row_id), FOREIGN KEY(capture_id) REFERENCES captures(id), FOREIGN KEY(row_id) REFERENCES selections(id));
CREATE TABLE latest(row_id TEXT PRIMARY KEY, capture_id TEXT, quote_time TEXT, payload TEXT,
 FOREIGN KEY(row_id) REFERENCES selections(id), FOREIGN KEY(capture_id) REFERENCES captures(id));
""")

    def ingest(self, capture_id, quotes, *, model_sha256=None, parser_version="typed-contract/1"):
        with self.db:
            return self._ingest(capture_id, quotes, model_sha256=model_sha256, parser_version=parser_version)

    def _ingest(self, capture_id, quotes, *, model_sha256=None, parser_version="typed-contract/1"):
        """Caller owns the transaction, allowing a quote batch and attempt to commit together."""
        if not isinstance(capture_id, str) or not re.fullmatch(r"[0-9a-f]{64}", capture_id):
            raise Refusal("capture hash required")
        if model_sha256 is not None and (not isinstance(model_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", model_sha256)):
            raise Refusal("model hash required")
        if not isinstance(parser_version, str) or not 1 <= len(parser_version) <= 80 or not parser_version.isascii():
            raise Refusal("parser version required")
        if not isinstance(quotes, list) or not 1 <= len(quotes) <= 1000:
            raise Refusal("bounded nonempty observation batch required")
        accepted = sorted((validate_quote(q) for q in quotes), key=quote_key)
        keys = [quote_key(q) for q in accepted]
        if len(set(keys)) != len(keys):
            raise Refusal("duplicate row in observation batch")
        digest = identity({"quotes": accepted, "model_sha256": model_sha256, "parser_version": parser_version})
        replay = self.db.execute("SELECT payload_sha256 FROM captures WHERE id=?", (capture_id,)).fetchone()
        if replay:
            if replay[0] != digest:
                raise Refusal("conflicting capture replay")
            return {"inserted": 0, "updated": 0, "stale_ignored": 0, "unchanged": 0, "replayed": True}
        result = {"inserted": 0, "updated": 0, "stale_ignored": 0, "unchanged": 0, "replayed": False}
        try:
            self.db.execute("INSERT INTO captures VALUES (?,?,?,?)", (capture_id, digest, model_sha256, parser_version))
            for q in accepted:
                self.db.execute("INSERT OR IGNORE INTO providers VALUES (?)", (q["provider_id"],))
                event = self.db.execute("SELECT home,away,start_time FROM events WHERE provider=? AND event_id=?", (q["provider_id"], q["event_id"])).fetchone()
                metadata = (q["home"], q["away"], q["start_time"])
                if event is not None and tuple(event) != metadata:
                    raise Refusal("conflicting event metadata")
                self.db.execute("INSERT OR IGNORE INTO events VALUES (?,?,?,?,?)", (q["provider_id"], q["event_id"], *metadata))
                market_id = identity(quote_key(q)[:-1])
                row_id = identity(quote_key(q))
                self.db.execute("INSERT OR IGNORE INTO markets VALUES (?,?,?,?,?)", (market_id, q["provider_id"], q["event_id"], q["market"], q["period"]))
                self.db.execute("INSERT OR IGNORE INTO selections VALUES (?,?,?)", (row_id, market_id, q["selection"]))
                payload = encoded(q)
                prior = self.db.execute("SELECT quote_time,payload FROM latest WHERE row_id=?", (row_id,)).fetchone()
                if prior and prior[0] == q["quote_time"] and prior[1] != payload:
                    raise Refusal("conflicting values at the same provider time")
                self.db.execute("INSERT INTO observations VALUES (?,?,?,?)", (capture_id, row_id, q["quote_time"], payload))
                if prior is None:
                    self.db.execute("INSERT INTO latest VALUES (?,?,?,?)", (row_id, capture_id, q["quote_time"], payload))
                    result["inserted"] += 1
                elif q["quote_time"] > prior[0]:
                    self.db.execute("UPDATE latest SET capture_id=?,quote_time=?,payload=? WHERE row_id=?", (capture_id, q["quote_time"], payload, row_id))
                    result["updated"] += 1
                elif q["quote_time"] < prior[0]:
                    result["stale_ignored"] += 1
                else:
                    result["unchanged"] += 1
        except sqlite3.DatabaseError:
            raise Refusal("database transaction failed; original retained") from None
        return result

    def latest(self):
        rows = [validate_quote(json.loads(row[0])) for row in self.db.execute("SELECT payload FROM latest")]
        return sorted(rows, key=quote_key)

    def counts(self):
        return {name: self.db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in ("captures", "observations", "latest")}

    def close(self):
        self.db.close()


def score_database(store, expected, *, provider_id=None):
    """Read persisted latest rows; evaluator truth is never used for ingestion."""
    if not isinstance(expected, list) or len(expected) > 1000:
        raise Refusal("bounded expected snapshot required")
    gold = {quote_key(q): q for q in map(validate_quote, expected)}
    if len(gold) != len(expected):
        raise Refusal("duplicate expected row")
    if provider_id is not None and (provider_id not in PROVIDERS or any(q["provider_id"] != provider_id for q in gold.values())):
        raise Refusal("explicit provider scope must contain all expected rows")
    actual = {quote_key(q): q for q in store.latest() if provider_id is None or q["provider_id"] == provider_id}
    shared = set(gold) & set(actual)
    correct = sum(gold[key] == actual[key] for key in shared)
    fields = {field: sum(gold[key][field] != actual[key][field] for key in shared)
              for field in sorted(FIELDS)}
    failures = []
    for key in sorted(set(gold) | set(actual)):
        if key not in actual:
            failures.append({"kind": "missing_record", "key": list(key), "expected": gold[key]})
        elif key not in gold:
            failures.append({"kind": "unexpected_record", "key": list(key), "observed": actual[key]})
        elif gold[key] != actual[key]:
            failures.append({"kind": "wrong_record", "key": list(key), "expected": gold[key], "observed": actual[key]})
    return {"schema": "sportsbook-database-score/1", "expected_records": len(gold), "stored_records": len(actual),
            "correct_records": correct, "wrong_records": len(actual) - correct,
            "missing_records": len(set(gold) - set(actual)), "unexpected_records": len(set(actual) - set(gold)),
            "row_precision": len(shared) / len(actual) if actual else 0,
            "row_recall": len(shared) / len(gold) if gold else None,
            "score": correct / len(gold) if gold else None,
            "field_errors": fields, "field_missing": {field: len(set(gold) - set(actual)) for field in fields},
            "field_support": {field: len(gold) for field in fields},
            "scope": {"provider_id": provider_id},
            "failures": failures, "source": "persisted SQLite latest rows"}
