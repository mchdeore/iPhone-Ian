"""Generated-only serial/calibration boundary. There is deliberately no physical driver."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass

import numpy as np

from .benchmark import Box, Refusal


@dataclass(frozen=True)
class Frame:
    device: str
    session: str
    marker: str
    captured_at: float
    width: int
    height: int


@dataclass(frozen=True)
class Calibration:
    device: str
    viewport: tuple[int, int]
    matrix: tuple[tuple[float, float, float], tuple[float, float, float]]
    workspace: Box
    error_mm: float
    verified: bool

    @classmethod
    def fit(
        cls,
        device,
        viewport,
        pixels,
        millimeters,
        held_pixels,
        held_mm,
        workspace,
        *,
        tolerance_mm=0.5,
    ):
        p, m = np.asarray(pixels, dtype=float), np.asarray(millimeters, dtype=float)
        hp, hm = np.asarray(held_pixels, dtype=float), np.asarray(held_mm, dtype=float)
        if (
            p.ndim != 2
            or p.shape[1] != 2
            or p.shape != m.shape
            or len(p) < 4
            or hp.ndim != 2
            or hp.shape[1] != 2
            or hp.shape != hm.shape
            or len(hp) < 2
        ):
            raise Refusal("four calibration and two independent holdout points required")
        if not all(np.isfinite(v).all() for v in [p, m, hp, hm]):
            raise Refusal("nonfinite calibration")
        design = np.column_stack([p, np.ones(len(p))])
        if np.linalg.matrix_rank(design) < 3:
            raise Refusal("degenerate calibration")
        matrix = np.linalg.lstsq(design, m, rcond=None)[0].T
        errors = np.linalg.norm(np.column_stack([hp, np.ones(len(hp))]) @ matrix.T - hm, axis=1)
        error = float(max(errors))
        if error > tolerance_mm or tolerance_mm <= 0 or abs(np.linalg.det(matrix[:, :2])) < 1e-9:
            raise Refusal("independent calibration error exceeds tolerance")
        c = cls(
            device,
            tuple(viewport),
            tuple(tuple(float(x) for x in row) for row in matrix),
            workspace,
            error,
            True,
        )
        for point in [*m, *hm]:
            if not workspace.contains(*point):
                raise Refusal("calibration outside allowed workspace")
        return c

    @property
    def digest(self):
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()

    def map(self, x, y):
        if (
            not self.verified
            or not math.isfinite(x)
            or not math.isfinite(y)
            or not 0 <= x <= self.viewport[0]
            or not 0 <= y <= self.viewport[1]
        ):
            raise Refusal("uncalibrated/outside screen")
        return tuple(float(v) for v in np.asarray(self.matrix) @ np.array([x, y, 1]))


def undo_letterbox(x, y, *, source, resized, pad):
    if min(*source, *resized) <= 0 or any(
        not math.isfinite(v) for v in [x, y, *source, *resized, *pad]
    ):
        raise Refusal("invalid image transform")
    point = ((x - pad[0]) * source[0] / resized[0], (y - pad[1]) * source[1] / resized[1])
    if not 0 <= point[0] <= source[0] or not 0 <= point[1] <= source[1]:
        raise Refusal("prediction in padding/outside image")
    return point


@dataclass(frozen=True)
class Intent:
    kind: str
    device: str
    session: str
    frame: str
    calibration: str
    points: tuple[tuple[float, float], ...]
    confidence: float
    expires_at: float
    token: str


class FakeSerial:
    simulated = True

    def __init__(self):
        self.commands = []
        self.fail_next = False

    def exchange(self, sequence, command):
        self.commands.append({"sequence": sequence, "command": command})
        if self.fail_next:
            self.fail_next = False
            return {"sequence": sequence + 1, "ok": False}
        return {"sequence": sequence, "ok": True}


class VirtualController:
    def __init__(self, serial: FakeSerial, calibration: Calibration, *, now=0):
        if type(serial) is not FakeSerial:
            raise Refusal("only generated fake serial is enabled")
        self.serial = serial
        self.calibration = calibration
        self.homed = False
        self.stopped = True
        self.sequence = 0
        self.token = None
        self.frame = None
        self.used = set()
        self.history = []
        self.now = now

    def _command(self, command):
        self.sequence += 1
        ack = self.serial.exchange(self.sequence, command)
        if ack != {"sequence": self.sequence, "ok": True}:
            self.stop("unconfirmed serial acknowledgement")
            raise Refusal("unconfirmed acknowledgement; stopped")

    def home(self):
        if not self.stopped:
            raise Refusal("stop before homing")
        self._command("HOME GENERATED")
        self.homed = True

    def arm(self, frame: Frame, token: str, now: float):
        if not self.homed or not self.calibration.verified or not token or token in self.used:
            raise Refusal("home/fresh arm token required")
        self._frame(frame, now)
        self.frame = frame
        self.token = token
        self.stopped = False
        self.now = now

    def _frame(self, frame, now):
        if (
            frame.device != self.calibration.device
            or (frame.width, frame.height) != self.calibration.viewport
            or not frame.marker.startswith(frame.session + ":")
        ):
            raise Refusal("wrong phone/session/viewport")
        if (
            not math.isfinite(now)
            or not math.isfinite(frame.captured_at)
            or not 0 <= now - frame.captured_at <= 2
        ):
            raise Refusal("stale/future frame")

    def stop(self, reason="operator stop"):
        self.stopped = True
        self.token = None
        self.serial.commands.append({"sequence": self.sequence, "command": "STOP GENERATED"})
        self.history.append({"kind": "stop", "reason": reason})

    def execute(self, intent: Intent, frame: Frame, now: float):
        if self.stopped or not self.homed:
            raise Refusal("stopped/unhomed")
        self._frame(frame, now)
        if (
            frame != self.frame
            or (intent.device, intent.session, intent.frame)
            != (frame.device, frame.session, frame.marker)
            or intent.calibration != self.calibration.digest
        ):
            raise Refusal("identity/calibration fence")
        if (
            intent.token != self.token
            or intent.token in self.used
            or not math.isfinite(intent.expires_at)
            or not now <= intent.expires_at <= now + 2
        ):
            raise Refusal("expired/replayed intent")
        if (
            intent.kind not in {"tap", "drag"}
            or len(intent.points) != (1 if intent.kind == "tap" else 2)
            or not math.isfinite(intent.confidence)
            or not 0.9 <= intent.confidence <= 1
        ):
            raise Refusal("typed high-confidence tap/drag only")
        mapped = [self.calibration.map(*p) for p in intent.points]
        margin = max(1, self.calibration.error_mm)
        if any(not self.calibration.workspace.contains(*p, margin=margin) for p in mapped):
            raise Refusal("outside inset phone workspace")
        # A convex rectangle contains the full straight drag segment. No raw policy G-code.
        self.used.add(intent.token)
        self.token = None
        try:
            self._command("LIFT GENERATED")
            for x, y in mapped:
                self._command(f"XY GENERATED {x:.5f} {y:.5f}")
            self._command(f"{intent.kind.upper()} GENERATED")
            self._command("LIFT GENERATED")
        finally:
            self.stopped = True
        encoded_intent = asdict(intent)
        encoded_intent.pop("token")
        encoded_intent["token_sha256"] = hashlib.sha256(intent.token.encode()).hexdigest()
        result = {
            "schema": "virtual-control/2",
            "intent": encoded_intent,
            "frame": asdict(frame),
            "mapped_mm": mapped,
            "calibration_sha256": self.calibration.digest,
            "simulated": True,
            "physical_acceptance": False,
            "commands": self.serial.commands.copy(),
        }
        self.history.append(result)
        return result


def replay(records, calibration):
    """Fresh offline controller reproduces accepted generated intentions, never hardware."""
    outputs = []
    for record in records:
        if record.get("schema") != "virtual-control/2":
            raise Refusal("older run schema retained; use a new copy")
        controller = VirtualController(FakeSerial(), calibration)
        controller.home()
        frame = Frame(**record["frame"])
        encoded = dict(record["intent"])
        digest = encoded.pop("token_sha256")
        encoded["token"] = "replay-" + digest[:32]
        encoded["points"] = tuple(tuple(p) for p in encoded["points"])
        intent = Intent(**encoded)
        controller.arm(frame, intent.token, frame.captured_at)
        outputs.append(controller.execute(intent, frame, frame.captured_at))
    return outputs
