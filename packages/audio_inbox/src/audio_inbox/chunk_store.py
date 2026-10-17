from __future__ import annotations

import json
import os
import secrets
import sqlite3
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from .chunks import merge_transcripts, pcm_chunks
from .core import RefusedNotAcceptedError
from .models import AssetRef, Segment, TranscriptReply
from .providers import ProviderAdapterError
from .validation import validate_transcript

_MAX_JSON = 200_000


def _reply_to_json(reply: TranscriptReply) -> str:
    payload = {
        "model": reply.model,
        "text": reply.text,
        "segments": [asdict(s) for s in reply.segments],
    }
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    if len(blob.encode("utf-8")) > _MAX_JSON:
        raise ValueError("reply_json_too_large")
    return blob


def _json_to_reply(blob: str, expected_model: str) -> TranscriptReply:
    if not isinstance(blob, str) or len(blob.encode("utf-8")) > _MAX_JSON:
        raise ValueError("invalid_cached_reply")
    obj = json.loads(blob)
    segs = [Segment(**seg) for seg in obj.get("segments", [])]
    rep = TranscriptReply(model=obj.get("model", ""), text=obj.get("text", ""), segments=segs)
    if rep.model != expected_model:
        raise ValueError("cached_model_mismatch")
    return rep


def _pid_alive(pid: int | None) -> bool:
    if type(pid) is not int or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextmanager
def _connect(db_path: Path):
    p = Path(db_path)
    if p.is_symlink():
        raise ValueError("db_symlink_not_allowed")
    if not p.exists():
        fd = os.open(str(p), os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
    os.chmod(p, 0o600)
    con = sqlite3.connect(str(p), timeout=5.0, isolation_level=None)
    try:
        con.execute("PRAGMA foreign_keys=ON")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS chunk_attempts(
              original_asset_hash TEXT NOT NULL,
              chunk_id TEXT NOT NULL,
              requested_model TEXT NOT NULL,
              recipe TEXT NOT NULL,
              state TEXT NOT NULL,
              running_pid INTEGER,
              claim_token TEXT,
              reply_json TEXT,
              safe_error TEXT,
              updated_at INTEGER NOT NULL DEFAULT (unixepoch()),
              PRIMARY KEY(original_asset_hash, chunk_id, requested_model, recipe)
            )
            """
        )
        yield con
    finally:
        con.close()


class ChunkedTranscriber:
    def __init__(
        self,
        db_path: str | Path,
        transcriber: Callable[[AssetRef], TranscriptReply],
        model: str,
        recipe: str,
        chunk_options: dict | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("invalid_model")
        if not isinstance(recipe, str) or not recipe.strip():
            raise ValueError("invalid_recipe")
        self._db_path = Path(db_path)
        self._transcriber = transcriber
        self._model = model
        self._recipe = recipe
        self._chunk_options = dict(chunk_options or {})
        self._should_cancel = should_cancel
        self.last_overlap_requires_review = False

    def _read_row(self, ah: str, cid: str):
        with _connect(self._db_path) as con:
            return con.execute(
                """
                SELECT state,running_pid,claim_token,reply_json,safe_error
                FROM chunk_attempts
                WHERE original_asset_hash=? AND chunk_id=? AND requested_model=? AND recipe=?
                """,
                (ah, cid, self._model, self._recipe),
            ).fetchone()

    def _recover_dead(self, ah: str, cid: str):
        with _connect(self._db_path) as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT state,running_pid FROM chunk_attempts WHERE original_asset_hash=? "
                "AND chunk_id=? AND requested_model=? AND recipe=?",
                (ah, cid, self._model, self._recipe),
            ).fetchone()
            if row is not None and row[0] == "running" and not _pid_alive(row[1]):
                con.execute(
                    "UPDATE chunk_attempts SET "
                    "state='uncertain',claim_token=NULL,safe_error='dead_owner' WHERE "
                    "original_asset_hash=? AND chunk_id=? AND requested_model=? AND recipe=?",
                    (ah, cid, self._model, self._recipe),
                )
            con.execute("COMMIT")

    def _claim(self, ah: str, cid: str) -> str:
        token = secrets.token_hex(16)
        pid = os.getpid()
        with _connect(self._db_path) as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                """
                SELECT state,running_pid,reply_json FROM chunk_attempts
                WHERE original_asset_hash=? AND chunk_id=? AND requested_model=? AND recipe=?
                """,
                (ah, cid, self._model, self._recipe),
            ).fetchone()
            if row is None:
                con.execute(
                    """
                    INSERT INTO chunk_attempts(
                      original_asset_hash,chunk_id,requested_model,recipe,state,
                      running_pid,claim_token,reply_json,safe_error
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (ah, cid, self._model, self._recipe, "running", pid, token, None, None),
                )
            elif row[0] == "completed":
                con.execute("COMMIT")
                return ""
            elif row[0] in ("uncertain", "running"):
                con.execute("ROLLBACK")
                raise TimeoutError("chunk_uncertain")
            else:
                cur = con.execute(
                    """
                    UPDATE chunk_attempts
                    SET state='running',running_pid=?,claim_token=?,safe_error=NULL,
                        updated_at=unixepoch()
                    WHERE original_asset_hash=? AND chunk_id=? AND requested_model=? AND recipe=?
                      AND state='notaccepted'
                    """,
                    (pid, token, ah, cid, self._model, self._recipe),
                )
                if cur.rowcount != 1:
                    con.execute("ROLLBACK")
                    raise RuntimeError("claim_conflict")
            con.execute("COMMIT")
        return token

    def _finish(
        self, ah: str, cid: str, token: str, state: str, reply_json: str | None, err: str | None
    ):
        with _connect(self._db_path) as con:
            con.execute("BEGIN IMMEDIATE")
            cur = con.execute(
                """
                UPDATE chunk_attempts
                SET state=?,running_pid=NULL,claim_token=NULL,reply_json=?,safe_error=?,
                    updated_at=unixepoch()
                WHERE original_asset_hash=? AND chunk_id=? AND requested_model=? AND recipe=?
                  AND claim_token=? AND state='running'
                """,
                (state, reply_json, err, ah, cid, self._model, self._recipe, token),
            )
            if cur.rowcount != 1:
                con.execute("ROLLBACK")
                raise RuntimeError("claim_lost")
            con.execute("COMMIT")

    def __call__(self, asset: AssetRef) -> TranscriptReply:
        with pcm_chunks(
            asset,
            **(
                self._chunk_options
                | {"max_chunks": min(64, self._chunk_options.get("max_chunks", 64))}
            ),
        ) as chunks:
            if len(chunks) > 64:
                raise ValueError("max_chunks_exceeded")
            # Refuse resume if any uncertain/running chunk exists for this identity.
            for c in chunks:
                row = self._read_row(asset.sha256, c.asset.id)
                if not row:
                    continue
                state, pid, _, _, _ = row
                if state == "uncertain":
                    raise TimeoutError("chunk_uncertain")
                if state == "running":
                    if _pid_alive(pid):
                        raise RuntimeError("chunk_running")
                    self._recover_dead(asset.sha256, c.asset.id)
                    raise TimeoutError("chunk_uncertain")

            replies: list[TranscriptReply] = []
            for c in chunks:
                if self._should_cancel and self._should_cancel():
                    raise RuntimeError("cancelled")
                row = self._read_row(asset.sha256, c.asset.id)
                if row and row[0] == "completed" and row[3]:
                    cached = _json_to_reply(row[3], self._model)
                    validate_transcript(cached, c.asset.duration)
                    replies.append(cached)
                    continue

                token = self._claim(asset.sha256, c.asset.id)
                if token == "":
                    row2 = self._read_row(asset.sha256, c.asset.id)
                    cached = _json_to_reply(row2[3], self._model)
                    validate_transcript(cached, c.asset.duration)
                    replies.append(cached)
                    continue

                try:
                    rep = self._transcriber(c.asset)
                    if rep.model != self._model:
                        raise ValueError("model_identity_mismatch")
                    validate_transcript(rep, c.asset.duration)
                    blob = _reply_to_json(rep)
                    self._finish(asset.sha256, c.asset.id, token, "completed", blob, None)
                    replies.append(rep)
                except RefusedNotAcceptedError:
                    self._finish(
                        asset.sha256, c.asset.id, token, "notaccepted", None, "not_accepted"
                    )
                    raise
                except TimeoutError:
                    self._finish(asset.sha256, c.asset.id, token, "uncertain", None, "timeout")
                    raise TimeoutError("chunk_uncertain") from None
                except ProviderAdapterError:
                    self._finish(
                        asset.sha256, c.asset.id, token, "uncertain", None, "provider_error"
                    )
                    raise
                except Exception:
                    self._finish(
                        asset.sha256, c.asset.id, token, "uncertain", None, "unknown_error"
                    )
                    raise

        merged = merge_transcripts(chunks, replies, max_text_chars=_MAX_JSON)
        self.last_overlap_requires_review = merged.overlap_requires_review
        return merged.reply
