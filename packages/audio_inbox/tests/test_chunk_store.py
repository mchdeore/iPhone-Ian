from __future__ import annotations

import hashlib
import sqlite3
import wave
from pathlib import Path

import pytest

from audio_inbox.chunk_store import ChunkedTranscriber
from audio_inbox.core import RefusedNotAcceptedError
from audio_inbox.models import AssetRef, Segment, TranscriptReply


def _wav_asset(tmp_path: Path, sec: float = 1.2, sr: int = 8000) -> AssetRef:
    n = int(sec * sr)
    p = tmp_path / "a.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"\x00\x00" * n)
    raw = p.read_bytes()
    return AssetRef(
        id="a",
        path=p,
        sha256=hashlib.sha256(raw).hexdigest(),
        media_type="audio/wav",
        duration=n / sr,
        size_bytes=len(raw),
    )


def _ok(model: str):
    calls = {"n": 0}

    def cb(asset: AssetRef) -> TranscriptReply:
        calls["n"] += 1
        return TranscriptReply(
            model=model,
            text=asset.id,
            segments=[Segment(segment_id="s", text="x", start=0.0, end=min(0.1, asset.duration))],
        )

    return cb, calls


def test_notaccepted_then_retry_only_unfinished(tmp_path: Path):
    asset = _wav_asset(tmp_path, sec=1.8)
    db = tmp_path / "AudioInbox.sqlite3"
    seen: set[str] = set()

    def cb(a: AssetRef):
        if not seen:
            seen.add(a.id)
            raise RefusedNotAcceptedError("429")
        return TranscriptReply(
            model="m", text=a.id, segments=[Segment("s", "x", 0.0, min(0.1, a.duration))]
        )

    t = ChunkedTranscriber(db, cb, "m", "r", {"window_seconds": 0.8, "overlap_seconds": 0.0})
    with pytest.raises(RefusedNotAcceptedError):
        t(asset)
    out = t(asset)
    assert out.model == "m"


def test_timeout_marks_uncertain_and_blocks_resume_without_calls(tmp_path: Path):
    asset = _wav_asset(tmp_path)
    db = tmp_path / "AudioInbox.sqlite3"
    n = {"v": 0}

    def cb(_: AssetRef):
        n["v"] += 1
        raise TimeoutError("t")

    t = ChunkedTranscriber(db, cb, "m", "r")
    with pytest.raises(TimeoutError):
        t(asset)
    with pytest.raises(TimeoutError, match="uncertain"):
        t(asset)
    assert n["v"] == 1


def test_cancel_keeps_completed_cache(tmp_path: Path):
    asset = _wav_asset(tmp_path, sec=2.0)
    db = tmp_path / "AudioInbox.sqlite3"
    n = {"v": 0}
    cancel = {"v": False}

    def cb(a: AssetRef):
        n["v"] += 1
        return TranscriptReply(
            model="m", text=a.id, segments=[Segment("s", "x", 0.0, min(0.1, a.duration))]
        )

    def should_cancel():
        return cancel["v"]

    t = ChunkedTranscriber(
        db, cb, "m", "r", {"window_seconds": 0.9, "overlap_seconds": 0.0}, should_cancel
    )
    cancel["v"] = True
    with pytest.raises(RuntimeError, match="cancelled"):
        t(asset)
    cancel["v"] = False
    t(asset)
    first = n["v"]
    t(asset)
    assert n["v"] == first


def test_token_fencing_blocks_stale_finish(tmp_path: Path):
    asset = _wav_asset(tmp_path)
    db = tmp_path / "AudioInbox.sqlite3"
    t = ChunkedTranscriber(
        db, lambda _: TranscriptReply("m", "x", [Segment("s", "x", 0.0, 0.1)]), "m", "r"
    )
    with pytest.raises(RuntimeError, match="claim_lost"):
        t._finish(asset.sha256, "cid", "bad", "completed", "{}", None)


def test_recipe_model_identity_mismatch_produces_new_cache_key(tmp_path: Path):
    asset = _wav_asset(tmp_path)
    db = tmp_path / "AudioInbox.sqlite3"
    cb1, c1 = _ok("m1")
    cb2, c2 = _ok("m2")
    ChunkedTranscriber(db, cb1, "m1", "r1")(asset)
    ChunkedTranscriber(db, cb1, "m1", "r1")(asset)
    ChunkedTranscriber(db, cb1, "m1", "r2")(asset)
    ChunkedTranscriber(db, cb2, "m2", "r1")(asset)
    assert c1["n"] >= 2
    assert c2["n"] >= 1


def test_live_dead_running_pid_behavior(tmp_path: Path):
    asset = _wav_asset(tmp_path)
    db = tmp_path / "AudioInbox.sqlite3"
    with sqlite3.connect(db) as con:
        con.execute("""CREATE TABLE chunk_attempts(
          original_asset_hash TEXT,chunk_id TEXT,requested_model TEXT,recipe TEXT,
          state TEXT,running_pid INTEGER,claim_token TEXT,reply_json TEXT,safe_error TEXT,
          updated_at INTEGER,PRIMARY KEY(original_asset_hash,chunk_id,requested_model,recipe))""")
        con.execute(
            "INSERT INTO chunk_attempts VALUES(?,?,?,?,?,?,?,?,?,0)",
            (asset.sha256, "x", "m", "r", "running", 1, "t", None, None),
        )
    t = ChunkedTranscriber(
        db, lambda _: TranscriptReply("m", "x", [Segment("s", "x", 0.0, 0.1)]), "m", "r"
    )
    row = t._read_row(asset.sha256, "x")
    assert row[0] == "running"


def test_db_foreign_keys_on_and_rollback_safe(tmp_path: Path):
    db = tmp_path / "AudioInbox.sqlite3"
    t = ChunkedTranscriber(
        db, lambda _: TranscriptReply("m", "x", [Segment("s", "x", 0.0, 0.1)]), "m", "r"
    )
    tok = t._claim("h", "c")
    with pytest.raises(RuntimeError):
        t._finish("h", "c", "wrong", "completed", "{}", None)
    row = t._read_row("h", "c")
    assert row[0] == "running" and row[2] == tok


def test_later_refusal_preserves_completed_chunks(tmp_path):
    asset = _wav_asset(tmp_path, sec=1.8)
    seen = []
    refused = [False]

    def callback(part):
        seen.append(part.id)
        if len(seen) == 2 and not refused[0]:
            refused[0] = True
            raise RefusedNotAcceptedError("quota")
        return TranscriptReply("m", "word", [Segment("s", "word", 0, 0.1)])

    transcriber = ChunkedTranscriber(
        tmp_path / "AudioInbox.sqlite3",
        callback,
        "m",
        "r",
        {"window_seconds": 0.7, "overlap_seconds": 0},
    )
    with pytest.raises(RefusedNotAcceptedError):
        transcriber(asset)
    first, second = seen
    transcriber(asset)
    assert seen.count(first) == 1 and seen.count(second) == 2
    count = len(seen)
    transcriber(asset)
    assert len(seen) == count


def test_dead_owner_persists_uncertainty_without_provider_replay(tmp_path):
    from audio_inbox.chunks import pcm_chunks

    asset = _wav_asset(tmp_path)
    with pcm_chunks(asset) as chunks:
        identifier = chunks[0].asset.id
    transcriber = ChunkedTranscriber(
        tmp_path / "AudioInbox.sqlite3", lambda part: pytest.fail("replay"), "m", "r"
    )
    token = transcriber._claim(asset.sha256, identifier)
    with sqlite3.connect(tmp_path / "AudioInbox.sqlite3") as db:
        db.execute("UPDATE chunk_attempts SET running_pid=999999 WHERE claim_token=?", (token,))
    with pytest.raises(TimeoutError, match="uncertain"):
        transcriber(asset)
    assert transcriber._read_row(asset.sha256, identifier)[0] == "uncertain"


def test_live_owner_refuses_concurrent_dispatch(tmp_path):
    from audio_inbox.chunks import pcm_chunks

    asset = _wav_asset(tmp_path)
    with pcm_chunks(asset) as chunks:
        identifier = chunks[0].asset.id
    transcriber = ChunkedTranscriber(
        tmp_path / "AudioInbox.sqlite3", lambda part: pytest.fail("duplicate"), "m", "r"
    )
    token = transcriber._claim(asset.sha256, identifier)
    with pytest.raises(RuntimeError, match="chunk_running"):
        transcriber(asset)
    assert transcriber._read_row(asset.sha256, identifier)[2] == token


def test_private_configuration_wraps_chunker_on_same_inbox_database(tmp_path):
    import json

    from audio_inbox.config import providers

    config = tmp_path / "providers.json"
    config.write_text(
        json.dumps(
            {
                "key_ref": "key.env:KEY",
                "transcription": {
                    "endpoint": "https://example.test/audio/transcriptions",
                    "model": "m",
                },
                "goals": None,
                "chunking": {"window_seconds": 1, "overlap_seconds": 0},
            }
        )
    )
    transcriber, suggester = providers(config, db_path=tmp_path / "inbox.sqlite3")
    assert isinstance(transcriber, ChunkedTranscriber)
    assert transcriber._db_path == tmp_path / "inbox.sqlite3"
    assert suggester is None and not (tmp_path / "key.env").exists()


def test_inbox_safe_retry_does_not_repeat_completed_chunk(tmp_path):
    import time

    from audio_inbox.core import AudioInbox

    drop = tmp_path / "drop"
    drop.mkdir()
    _wav_asset(drop, sec=1.8)
    seen = []

    def callback(part):
        seen.append(part.id)
        if len(seen) == 2:
            raise RefusedNotAcceptedError("known refusal")
        return TranscriptReply("m", "word", [Segment("s", "word", 0, 0.1)])

    box = AudioInbox(
        root=tmp_path / "store",
        inbox=drop,
        transcriber=callback,
        suggester=lambda version: [],
        clock=lambda: time.time() + 10,
    )
    coordinator = ChunkedTranscriber(
        box.db_path, callback, "m", "r", {"window_seconds": 0.7, "overlap_seconds": 0}
    )
    box.transcriber = coordinator
    identifier = box.scan()[0]
    with pytest.raises(RefusedNotAcceptedError):
        box.process(identifier)
    version = box.process(identifier)
    assert box.transcript(version).model == "m"
    assert seen.count(seen[0]) == 1 and len(seen) == 4
