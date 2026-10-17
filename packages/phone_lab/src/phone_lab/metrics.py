from __future__ import annotations

import math
from statistics import median


def overlap(a, b):
    x = max(0, min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"]))
    y = max(0, min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"]))
    area = x * y
    union = a["width"] * a["height"] + b["width"] * b["height"] - area
    return area / union if union > 0 else 0


def detection_metrics(truth, predictions, *, class_aware=True, threshold=0.5):
    used = set()
    hits = []
    for p in sorted(predictions, key=lambda p: p.get("confidence", 1), reverse=True):
        eligible = [
            (overlap(p["box"], t["box"]), i)
            for i, t in enumerate(truth)
            if i not in used and (not class_aware or p["role"] == t["role"])
        ]
        best = max(eligible, default=(0, -1))
        if best[0] >= threshold:
            used.add(best[1])
            hits.append((p, truth[best[1]]))
    centers = []
    for p, t in hits:
        b = p["box"]
        gt = t["box"]
        x = b["x"] + b["width"] / 2
        y = b["y"] + b["height"] / 2
        centers.append(
            gt["x"] + 4 <= x <= gt["x"] + gt["width"] - 4
            and gt["y"] + 4 <= y <= gt["y"] + gt["height"] - 4
        )
    return {
        "true_positive": len(hits),
        "false_positive": len(predictions) - len(hits),
        "false_negative": len(truth) - len(hits),
        "safe_center_hits": sum(centers),
        "truth": len(truth),
        "predictions": len(predictions),
        "class_aware": class_aware,
    }


def edit_distance(left, right):
    row = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        updated = [i]
        for j, b in enumerate(right, 1):
            updated.append(min(updated[-1] + 1, row[j] + 1, row[j - 1] + (a != b)))
        row = updated
    return row[-1]


def ocr_metrics(labels, recognized):
    errors = characters = exact = targets = 0
    for target in labels:
        expected = target.get("text")
        if not expected:
            continue
        b = target["box"]
        inside = []
        for text in recognized:
            box = text["box"]
            x = box["x"] + box["width"] / 2
            y = box["y"] + box["height"] / 2
            if b["x"] <= x <= b["x"] + b["width"] and b["y"] <= y <= b["y"] + b["height"]:
                inside.append(text)
        actual = " ".join(
            t["text"] for t in sorted(inside, key=lambda t: (t["box"]["y"], t["box"]["x"]))
        )
        targets += 1
        characters += len(expected)
        errors += edit_distance(expected, actual)
        exact += expected == actual
    return {
        "targets": targets,
        "characters": characters,
        "character_errors": errors,
        "exact_targets": exact,
    }


def latency(values):
    if not values:
        return {"count": 0, "p50_ms": None, "p95_ms": None}
    values = sorted(values)
    index = 0.95 * (len(values) - 1)
    low = math.floor(index)
    high = math.ceil(index)
    p95 = values[low] + (values[high] - values[low]) * (index - low)
    return {"count": len(values), "p50_ms": median(values), "p95_ms": p95}
