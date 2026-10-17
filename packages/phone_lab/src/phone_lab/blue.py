"""A provider-only contact channel and frozen descriptive pattern rules."""

from __future__ import annotations

import math
import statistics

from .benchmark import Refusal, finite, identifier
from .metrics import latency

PACKET_SCHEMA = "website-contact-session/1"
EVENT_FIELDS = {"kind", "time_ms", "x", "y", "pointer"}
KINDS = {"down", "move", "up", "cancel", "input", "scroll"}


def make_blue_packet(session_id, viewport, events):
    """Export observed contacts, excluding text, labels and controller secrets."""
    if not isinstance(events, list) or len(events) > 5000:
        raise Refusal("contact event budget")
    if not isinstance(viewport, (list, tuple)) or len(viewport) != 2:
        raise Refusal("viewport required")
    narrow = []
    for event in events:
        if not isinstance(event, dict):
            raise Refusal("contact event required")
        narrow.append(
            {key: event.get(key, 1 if key == "pointer" else None) for key in EVENT_FIELDS}
        )
    packet = {
        "schema": PACKET_SCHEMA,
        "run_id": session_id,
        "viewport": list(viewport),
        "events": narrow,
    }
    _contacts(packet)
    return packet


def _contacts(packet):
    if not isinstance(packet, dict) or set(packet) != {"schema", "run_id", "viewport", "events"}:
        raise Refusal("provider-only packet required")
    if packet["schema"] != PACKET_SCHEMA:
        raise Refusal("contact schema")
    identifier(packet["run_id"])
    viewport = packet["viewport"]
    if (
        not isinstance(viewport, list)
        or len(viewport) != 2
        or any(type(v) is not int or not 1 <= v <= 4096 for v in viewport)
    ):
        raise Refusal("contact viewport")
    events = packet["events"]
    if not isinstance(events, list) or len(events) > 5000:
        raise Refusal("contact event budget")
    active, complete, cancelled, previous = {}, [], 0, -1.0
    for event in events:
        if not isinstance(event, dict) or set(event) != EVENT_FIELDS:
            raise Refusal("provider-only event required")
        kind = event["kind"]
        if not isinstance(kind, str) or kind not in KINDS:
            raise Refusal("contact kind")
        timestamp = finite(event["time_ms"], 0, 1e15, "time")
        if timestamp < previous:
            raise Refusal("contact time reversed")
        previous = timestamp
        x = finite(event["x"], 0, viewport[0], "x")
        y = finite(event["y"], 0, viewport[1], "y")
        pointer = event["pointer"]
        if type(pointer) is not int or not 0 <= pointer <= 100:
            raise Refusal("contact pointer")
        if kind == "down":
            if pointer in active:
                raise Refusal("duplicate contact down")
            active[pointer] = {"start": timestamp, "points": [(x, y)], "moves": 0}
        elif kind == "move" and pointer in active:
            active[pointer]["points"].append((x, y))
            active[pointer]["moves"] += 1
        elif kind in {"up", "cancel"}:
            if pointer not in active:
                raise Refusal("unpaired contact ending")
            contact = active.pop(pointer)
            if kind == "cancel":
                cancelled += 1
            else:
                contact["points"].append((x, y))
                contact["dwell_ms"] = timestamp - contact["start"]
                complete.append(contact)
    return complete, cancelled, len(active)


def score_contacts(packet):
    """Describe patterns without estimating robot identity or imposing sanctions."""
    contacts, cancelled, incomplete = _contacts(packet)
    dwells = [c["dwell_ms"] for c in contacts]
    paths = []
    for contact in contacts:
        points = contact["points"]
        length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
        paths.append(
            {
                "length_px": length,
                "linearity": math.dist(points[0], points[-1]) / length if length else 0,
                "moves": contact["moves"],
            }
        )
    flags = []
    median = statistics.median(dwells) if dwells else None
    if median is not None and median < 30:
        flags.append("short_contact_dwell")
    mean = statistics.fmean(dwells) if dwells else 0
    if len(dwells) >= 4 and (mean == 0 or statistics.pstdev(dwells) / mean <= 0.05):
        flags.append("regular_contact_dwell")
    if any(p["length_px"] >= 30 and p["moves"] >= 4 and p["linearity"] >= 0.995 for p in paths):
        flags.append("straight_contact_path")
    return {
        "schema": "blue-contact-score/1",
        "run_id": packet["run_id"],
        "features": {
            "contacts": len(contacts),
            "dwell_ms": latency(dwells),
            "contact_paths": paths,
            "cancelled_contacts": cancelled,
            "incomplete_contacts": incomplete,
        },
        "flags": flags,
        "robot_probability": None,
        "human_validation": "pending consented controls",
        "sanctions": False,
        "rule_version": "declared-contact-patterns/1",
    }
