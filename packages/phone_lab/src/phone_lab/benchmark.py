from __future__ import annotations

import hashlib
import json
import math
import os
import random
import secrets
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

TASKS = ("tap", "drag", "entry", "menu", "overlay", "scroll")
SCHEMA = "phone-lab/2"


class Refusal(ValueError):
    """A refused observation/action has no state-changing effect."""


def finite(value: float, lo: float, hi: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Refusal(f"{name}: number required")
    if not math.isfinite(value) or not lo <= value <= hi:
        raise Refusal(f"{name}: outside finite bounds")
    return float(value)


def identifier(value: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 80:
        raise Refusal("invalid identity")
    if not all(c.isascii() and (c.isalnum() or c in "-_") for c in value):
        raise Refusal("invalid identity")
    return value


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    width: float
    height: float

    def contains(self, x: float, y: float, margin: float = 0) -> bool:
        return (
            self.x + margin <= x <= self.x + self.width - margin
            and self.y + margin <= y <= self.y + self.height - margin
        )

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.width / 2, self.y + self.height / 2


@dataclass(frozen=True)
class Target:
    id: str
    role: str
    text: str
    box: Box


def layout(seed: int, width: int, height: int, task: str, phase: int = 0) -> list[Target]:
    """The browser uses these same component definitions; no policy consumes this truth."""
    rng = random.Random(seed)
    x = rng.randint(20, max(21, width - 170))
    y = rng.randint(130, max(131, height - 230))

    def button(name, text, bx=x, by=y):
        return Target(name, "button", text, Box(bx, by, 140, 48))

    if task == "drag":
        return [
            Target("grip", "handle", "Grip", Box(24, y, 68, 52)),
            Target("goal", "destination", "Goal", Box(width - 115, y + 96, 88, 64)),
        ]
    if task == "entry":
        return [
            Target("value", "field", "Value", Box(24, y, width - 48, 54)),
            button("check", "Check", 24, y + 76),
        ]
    if task == "menu":
        return (
            [button("menu", "Menu")]
            if phase == 0
            else [button("orange", "Orange"), button("blue", "Blue", x, y + 65)]
        )
    if task == "overlay":
        return (
            [button("close", "Dismiss Overlay")] if phase == 0 else [button("continue", "Continue")]
        )
    if task == "scroll":
        return (
            [
                Target(
                    "list", "list", "Scroll down", Box(20, y, width - 40, min(300, height - y - 25))
                )
            ]
            if phase == 0
            else [button("finish", "Finish")]
        )
    return [button("continue", "Continue"), button("cancel", "Cancel", x, y + 65)]


@dataclass
class Session:
    id: str
    device: str
    seed: int
    width: int
    height: int
    task: str
    capability: str
    frame: int = 1
    phase: int = 0
    complete: bool = False
    value: str = ""
    focused: bool = False
    last_seq: int = 0
    last_time: float = -1
    active_pointer: dict | None = None
    wrong_actions: int = 0
    events: list[dict] = field(default_factory=list)
    cohort: str = "generated"
    participant: str = "generated"
    consent_ref: str | None = None

    @property
    def marker(self) -> str:
        return f"{self.id}:{self.frame}"

    @property
    def expected_value(self) -> str:
        return str(1000 + self.seed % 9000)

    def targets(self) -> list[Target]:
        return (
            []
            if self.complete
            else layout(self.seed, self.width, self.height, self.task, self.phase)
        )


class Benchmark:
    def __init__(self, root: Path, *, max_sessions: int = 1000, max_events: int = 5000):
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if root.is_symlink():
            raise Refusal("store symlink refused")
        self.root, self.max_sessions, self.max_events = root, max_sessions, max_events
        self.log = root / "evaluator.jsonl"
        self.keys = root / "session-keys"
        if self.keys.is_symlink():
            raise Refusal("credential store symlink refused")
        self.keys.mkdir(mode=0o700, exist_ok=True)
        self.sessions: dict[str, Session] = {}
        self.lock = threading.RLock()
        if self.log.exists():
            if self.log.is_symlink():
                raise Refusal("log symlink refused")
            for line in self.log.read_text().splitlines():
                try:
                    record = json.loads(line)
                    if record["schema"] != SCHEMA:
                        raise ValueError("schema")
                    previous = self.sessions.get(record["snapshot"]["id"])
                    events = previous.events.copy() if previous else []
                    if record.get("observation") is not None:
                        events.append(record["observation"])
                    snapshot = record["snapshot"]
                    key_path = self.keys / identifier(snapshot["id"])
                    if key_path.is_symlink():
                        raise Refusal("credential file symlink refused")
                    capability = key_path.read_text()
                    if len(capability) < 16:
                        raise Refusal("missing/invalid session credential; retained")
                    session = Session(**snapshot, capability=capability, events=events)
                    self.sessions[session.id] = session
                except (ValueError, KeyError, TypeError, OSError) as exc:
                    raise Refusal(
                        "corrupt/interrupted log retained; repair requires a new copy"
                    ) from exc

    def _save(self, session: Session, kind: str) -> None:
        snapshot = asdict(session)
        snapshot.pop("events")
        snapshot.pop("capability")
        record = {
            "schema": SCHEMA,
            "kind": kind,
            "time_ns": time.time_ns(),
            "snapshot": snapshot,
            "observation": session.events[-1] if kind == "observation" else None,
        }
        data = (json.dumps(record, allow_nan=False, separators=(",", ":")) + "\n").encode()
        if len(data) > 4_000_000:
            raise Refusal("record budget exhausted")
        if self.log.exists() and self.log.stat().st_size + len(data) > 128_000_000:
            raise Refusal("store byte budget exhausted")
        fd = os.open(self.log, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, "ab") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
        except BaseException:
            raise

    def create(
        self,
        device: str,
        seed: int,
        width: int,
        height: int,
        task: str,
        *,
        cohort: str = "generated",
        participant: str = "generated",
        consent_ref: str | None = None,
    ) -> Session:
        identifier(device)
        identifier(participant)
        if type(seed) is not int or not 0 <= seed <= 2**31 - 1 or task not in TASKS:
            raise Refusal("unknown task/seed")
        if (
            type(width) is not int
            or type(height) is not int
            or not 280 <= width <= 1200
            or not 400 <= height <= 2400
        ):
            raise Refusal("viewport bounds")
        if cohort not in {"generated", "human", "stylus", "accessibility", "robot"}:
            raise Refusal("unknown cohort")
        if cohort != "generated" and (not consent_ref or len(consent_ref) > 100):
            raise Refusal("real observation requires consent reference")
        with self.lock:
            if len(self.sessions) >= self.max_sessions:
                raise Refusal("session budget exhausted")
            session = Session(
                secrets.token_hex(12),
                device,
                seed,
                width,
                height,
                task,
                secrets.token_urlsafe(24),
                cohort=cohort,
                participant=participant,
                consent_ref=consent_ref,
            )
            fd = os.open(
                self.keys / session.id, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
            )
            with os.fdopen(fd, "w") as key_file:
                key_file.write(session.capability)
                key_file.flush()
                os.fsync(key_file.fileno())
            self._save(session, "create")
            self.sessions[session.id] = session
            return session

    def get(self, sid: str) -> Session:
        try:
            return self.sessions[identifier(sid)]
        except KeyError as exc:
            raise Refusal("unknown session") from exc

    def authorize(self, sid: str, capability: str) -> Session:
        session = self.get(sid)
        if not secrets.compare_digest(session.capability, capability):
            raise Refusal("wrong session capability")
        return session

    def reset(self, sid: str) -> Session:
        with self.lock:
            s = self.get(sid)
            new = Session(
                s.id,
                s.device,
                s.seed,
                s.width,
                s.height,
                s.task,
                s.capability,
                frame=s.frame + 1,
                last_seq=s.last_seq,
                last_time=s.last_time,
                events=s.events.copy(),
                cohort=s.cohort,
                participant=s.participant,
                consent_ref=s.consent_ref,
            )
            self._save(new, "reset")
            self.sessions[sid] = new
            return new

    def observe(self, sid: str, event: dict) -> dict:
        """Only registered client contact/input/scroll evidence determines task transitions."""
        allowed = {
            "device",
            "frame",
            "seq",
            "event_id",
            "kind",
            "x",
            "y",
            "time_ms",
            "pointer",
            "value",
            "pressure",
            "contact_width",
            "contact_height",
        }
        if set(event) - allowed:
            raise Refusal("unrecognized observation fields")
        with self.lock:
            original = self.get(sid)
            if original.complete:
                raise Refusal("completed episode requires reset")
            s = Session(**json.loads(json.dumps(asdict(original))))
            if event.get("device") != s.device or event.get("frame") != s.marker:
                raise Refusal("stale/wrong device frame")
            seq = event.get("seq")
            if type(seq) is not int or seq != s.last_seq + 1 or len(s.events) >= self.max_events:
                raise Refusal("duplicate/out-of-order event or budget")
            identifier(event.get("event_id", ""))
            if any(e["event_id"] == event["event_id"] for e in s.events):
                raise Refusal("duplicate event identity")
            x = finite(event.get("x"), 0, s.width, "x")
            y = finite(event.get("y"), 0, s.height, "y")
            timestamp = finite(event.get("time_ms"), 0, 1e15, "time")
            if timestamp < s.last_time:
                raise Refusal("time reversed")
            pointer = event.get("pointer", 1)
            if type(pointer) is not int or not 0 <= pointer <= 100:
                raise Refusal("pointer bounds")
            kind = event.get("kind")
            if kind not in {"down", "move", "up", "input", "scroll"}:
                raise Refusal("unsupported observation")
            for name, hi in (("pressure", 1), ("contact_width", 1000), ("contact_height", 1000)):
                if event.get(name) is not None:
                    finite(event[name], 0, hi, name)
            value = event.get("value", "")
            if not isinstance(value, str) or len(value) > 32:
                raise Refusal("text bounds")
            targets = {t.id: t for t in s.targets()}
            if kind == "down":
                if s.active_pointer is not None:
                    raise Refusal("one contact at a time")
                hit = next((t.id for t in targets.values() if t.box.contains(x, y)), None)
                s.active_pointer = {"pointer": pointer, "target": hit, "x": x, "y": y}
            elif kind in {"move", "up"}:
                if s.active_pointer is None or s.active_pointer["pointer"] != pointer:
                    raise Refusal("missing/mismatched pointer down")
                if kind == "up":
                    start = s.active_pointer
                    s.active_pointer = None
                    target = targets.get(start["target"])
                    same = target is not None and target.box.contains(x, y)
                    if s.task == "drag":
                        success = start["target"] == "grip" and targets["goal"].box.contains(x, y)
                        s.complete = success
                        s.wrong_actions += not success
                    elif same:
                        hit = target.id
                        if s.task == "entry" and hit == "value":
                            s.focused = True
                        elif s.task == "entry" and hit == "check":
                            s.complete = s.focused and s.value == s.expected_value
                            s.wrong_actions += not s.complete
                        elif (s.task, s.phase, hit) in {
                            ("menu", 0, "menu"),
                            ("overlay", 0, "close"),
                        }:
                            s.phase = 1
                        elif hit in {"continue", "orange", "finish"}:
                            s.complete = True
                        else:
                            s.wrong_actions += 1
                    else:
                        s.wrong_actions += 1
            elif kind == "input":
                if s.task != "entry" or not s.focused or not value.isascii() or not value.isdigit():
                    raise Refusal("unfocused/non-numeric input")
                s.value = value
            elif kind == "scroll":
                if s.task != "scroll" or s.phase != 0 or not value.isdigit() or int(value) < 100:
                    raise Refusal("unsupported/unproved scroll")
                s.phase = 1
            s.last_seq, s.last_time = seq, timestamp
            s.events.append(event)
            if (
                s.complete != original.complete
                or s.phase != original.phase
                or s.value != original.value
                or s.focused != original.focused
            ):
                s.frame += 1
            self._save(s, "observation")
            self.sessions[sid] = s
            return self.outcome(sid)

    def outcome(self, sid: str) -> dict:
        s = self.get(sid)
        return {
            "schema": SCHEMA,
            "session": s.id,
            "device": s.device,
            "frame": s.marker,
            "complete": s.complete,
            "phase": s.phase,
            "events": len(s.events),
            "wrong_actions": s.wrong_actions,
            "evidence_source": "owned-browser-observation",
            "evidence_sha256": hashlib.sha256(
                json.dumps(s.events, sort_keys=True).encode()
            ).hexdigest(),
        }
