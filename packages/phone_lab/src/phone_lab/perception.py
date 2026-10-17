"""Bounded, class-aware candidate selection from detector and OCR pixels only."""

from __future__ import annotations

import math
import re
import unicodedata

from phone_lab.benchmark import Refusal
from phone_lab.metrics import edit_distance

ROLES = frozenset({"button", "field", "handle", "destination", "list"})


def _number(value):
    if type(value) not in {int, float} or not math.isfinite(value):
        raise Refusal("invalid perception number")
    return value


def _box(value, viewport):
    if not isinstance(value, dict) or set(value) != {"x", "y", "width", "height"}:
        raise Refusal("invalid perception box")
    x, y, w, h = (_number(value[k]) for k in ("x", "y", "width", "height"))
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > viewport[0] or y + h > viewport[1]:
        raise Refusal("invalid perception bounds")
    return x, y, w, h


def _confidence(value):
    score = _number(value)
    if not 0 <= score <= 1:
        raise Refusal("invalid perception confidence")
    return score


def _label(value):
    if not isinstance(value, str) or len(value) > 256:
        raise Refusal("invalid perception label")
    return " ".join(re.findall(r"\w+", unicodedata.normalize("NFKC", value).casefold()))


def unletterbox_box(value, *, viewport):
    """Undo the exact rounded padding of a fixed 640-square LetterBox input."""
    if (
        not isinstance(viewport, (tuple, list)) or len(viewport) != 2
        or any(type(v) is not int or not 1 <= v <= 4096 for v in viewport)
        or not isinstance(value, (tuple, list)) or len(value) != 4
    ):
        raise Refusal("invalid perception model box")
    x1, y1, x2, y2 = (_number(v) for v in value)
    if not 0 <= x1 < x2 <= 640 or not 0 <= y1 < y2 <= 640:
        raise Refusal("invalid perception model bounds")
    width, height = viewport
    gain = min(640 / width, 640 / height)
    left = round((640 - round(width * gain)) / 2 - 0.1)
    top = round((640 - round(height * gain)) / 2 - 0.1)
    x1, x2 = (max(0, min(width, (v - left) / gain)) for v in (x1, x2))
    y1, y2 = (max(0, min(height, (v - top) / gain)) for v in (y1, y2))
    box = {"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1}
    _box(box, viewport)
    return box


def choose_target(predictions, recognized, *, role, name=None, viewport):
    """Return one target with its measured minimum score, or refuse.

    Button semantics require OCR inside the predicted button. Region classes
    permit only the caller's separately typed gesture, never generic taps.
    Scores are development gates, not calibrated real-device probabilities.
    """
    if (
        not isinstance(role, str)
        or role not in ROLES
        or not isinstance(viewport, (tuple, list))
        or len(viewport) != 2
        or any(type(v) is not int or not 1 <= v <= 4096 for v in viewport)
        or not isinstance(predictions, (tuple, list))
        or not isinstance(recognized, (tuple, list))
        or len(predictions) > 32
        or len(recognized) > 32
    ):
        raise Refusal("invalid perception input")
    if role == "button" and (not isinstance(name, str) or not name.strip()):
        raise Refusal("button label required")
    wanted = _label(name) if name is not None else None
    texts = []
    for item in recognized:
        if not isinstance(item, dict):
            raise Refusal("invalid perception OCR")
        label = _label(item.get("text"))
        score = _confidence(item.get("confidence"))
        box = _box(item.get("box"), viewport)
        texts.append((label, score, box))
    matches = []
    for item in predictions:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("role"), str)
            or item["role"] not in ROLES
        ):
            raise Refusal("invalid perception class")
        score = _confidence(item.get("confidence"))
        x, y, w, h = _box(item.get("box"), viewport)
        if item["role"] != role or score < 0.9:
            continue
        if wanted is not None:
            inside = [
                t for t in texts if x <= t[2][0] + t[2][2] / 2 <= x + w
                and y <= t[2][1] + t[2][3] / 2 <= y + h
            ]
            observed = " ".join(t[0] for t in sorted(inside, key=lambda t: (t[2][1], t[2][0])))
            if not inside or not wanted or not observed:
                continue
            similarity = 1 - edit_distance(wanted, observed) / max(len(wanted), len(observed))
            score = min(score, similarity, *(t[1] for t in inside))
        if score >= 0.9:
            matches.append({"point": (x + w / 2, y + h / 2), "confidence": score, "role": role})
    if len(matches) != 1:
        raise Refusal("ambiguous/missing trained target")
    return matches[0]
