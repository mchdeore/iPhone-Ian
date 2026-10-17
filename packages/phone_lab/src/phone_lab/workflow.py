from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import asdict
from pathlib import Path
from statistics import median

import numpy as np
from PIL import Image

from .benchmark import Refusal
from .control import Frame


def save_capture(
    root: Path, image: Path, frame: Frame, *, permission: str, source="owned-generated-render"
):
    if not permission or source not in {"owned-generated-render", "owned-consented-phone"}:
        raise Refusal("owned capture provenance required")
    if root.exists() or image.is_symlink():
        raise Refusal("immutable new capture directory required")
    data = image.read_bytes()
    with Image.open(image) as im:
        if im.size != (frame.width, frame.height):
            raise Refusal("capture viewport mismatch")
        im.verify()
    root.mkdir(parents=True, mode=0o700)
    (root / "frame.png").write_bytes(data)
    manifest = {
        "schema": "owned-capture/1",
        "frame": asdict(frame),
        "sha256": hashlib.sha256(data).hexdigest(),
        "source": source,
        "permission_reference": permission,
        "real_phone": source == "owned-consented-phone",
    }
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    for p in root.iterdir():
        p.chmod(0o400)
    return manifest


def load_capture(root):
    manifest = json.loads((root / "manifest.json").read_text())
    path = root / "frame.png"
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != manifest["sha256"]:
        raise Refusal("capture bytes changed")
    return Frame(**manifest["frame"]), path


def color_candidates(path):
    """CPU development baseline uses only border pixels, with no class/action claims."""
    with Image.open(path) as image:
        pixels = np.asarray(image.convert("RGB"))
    mask = np.max(np.abs(pixels.astype(int) - np.array([97, 147, 205])), axis=2) <= 4
    visited = np.zeros(mask.shape, dtype=bool)
    boxes = []
    for y, x in np.argwhere(mask):
        if visited[y, x]:
            continue
        stack = [(int(x), int(y))]
        component = []
        visited[y, x] = True
        while stack:
            xx, yy = stack.pop()
            component.append((xx, yy))
            for nx, ny in [
                (xx + dx, yy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy
            ]:
                if (
                    0 <= ny < mask.shape[0]
                    and 0 <= nx < mask.shape[1]
                    and mask[ny, nx]
                    and not visited[ny, nx]
                ):
                    visited[ny, nx] = True
                    stack.append((nx, ny))
        if len(component) < 30:
            continue
        xs, ys = zip(*component)
        w = max(xs) - min(xs) + 1
        h = max(ys) - min(ys) + 1
        if w >= 25 and h >= 25:
            boxes.append(
                {
                    "box": {"x": min(xs), "y": min(ys), "width": w, "height": h},
                    "role": "unknown",
                    "source": "pixel-border-baseline",
                    "actionable": False,
                }
            )
    return boxes


def website_observations(sessions):
    """Descriptive owned-site counts only; lab motor/camera telemetry is excluded."""
    groups = {}
    for s in sessions:
        if s.cohort != "generated" and not s.consent_ref:
            raise Refusal("participant consent reference required")
        group = groups.setdefault(
            s.cohort,
            {"sessions": 0, "complete": 0, "wrong_actions": 0, "events": 0, "durations_ms": []},
        )
        group["sessions"] += 1
        group["complete"] += bool(s.complete)
        group["wrong_actions"] += s.wrong_actions
        group["events"] += len(s.events)
        times = [e["time_ms"] for e in s.events if math.isfinite(e["time_ms"])]
        if len(times) >= 2:
            group["durations_ms"].append(max(times) - min(times))
    for g in groups.values():
        times = g.pop("durations_ms")
        g["median_duration_ms"] = median(times) if times else None
    return {
        "schema": "owned-site-observation/1",
        "cohorts": groups,
        "scope": "website contact/timing/outcome only",
        "lab_telemetry_used": False,
        "sanctions": False,
        "causal_or_real_participant_claim": False,
    }


def append_run(path, record):
    """Append and sync accepted workflow evidence; retain interrupted tails on replay."""
    data = (json.dumps(record, sort_keys=True, allow_nan=False) + "\n").encode()
    if len(data) > 1_000_000 or (path.exists() and path.stat().st_size + len(data) > 128_000_000):
        raise Refusal("run byte budget")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "ab") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def read_runs(path):
    try:
        return [json.loads(line) for line in path.read_text().splitlines()]
    except ValueError as e:
        raise Refusal("corrupt/interrupted run evidence retained") from e
