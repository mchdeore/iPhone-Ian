"""Class-independent identification confusion, preserving misses and false positives."""

from __future__ import annotations

import re

from ..benchmark import Refusal, finite, identifier
from ..metrics import overlap

SPORTS_ROLES = ("provider", "event", "participant", "event_time", "market", "period",
                "selection", "line", "odds", "status", "quote_time", "navigation")


def _objects(objects, classes, prefix):
    if not isinstance(objects, list) or len(objects) > 1000:
        raise Refusal("identification object budget")
    result = []
    for i, obj in enumerate(objects):
        if not isinstance(obj, dict) or obj.get("role") not in classes:
            raise Refusal("unknown identification role")
        box = obj.get("box")
        if not isinstance(box, dict) or set(box) != {"x", "y", "width", "height"}:
            raise Refusal("identified box required")
        b = {k: finite(box[k], 0 if k in ("x", "y") else 0.000001, 4096, k) for k in box}
        if b["x"] + b["width"] > 4096 or b["y"] + b["height"] > 4096:
            raise Refusal("identified box bounds")
        result.append({"id": identifier(obj.get("id", f"{prefix}-{i}")), "role": obj["role"],
                       "confidence": finite(obj.get("confidence", 1), 0, 1, "confidence"), "box": b})
    return result


def _summary(classes, matrix, failures, *, operation, threshold):
    per_class = {}
    for i, role in enumerate(classes[:-1]):
        tp = matrix[i][i]
        support = sum(matrix[i])
        predicted = sum(row[i] for row in matrix)
        per_class[role] = {"support": support, "true_positive": tp,
                           "false_negative": support - tp, "false_positive": predicted - tp,
                           "precision": tp / predicted if predicted else None,
                           "recall": tp / support if support else None}
    worst = [{"class": role, "misses": stats["false_negative"], "support": stats["support"],
              "failure_rate": stats["false_negative"] / stats["support"]}
             for role, stats in per_class.items() if stats["false_negative"]]
    worst.sort(key=lambda item: (-item["misses"], -item["failure_rate"], item["class"]))
    return {"schema": "identification-confusion/1", "operation": operation, "classes": list(classes),
            "matrix": matrix, "matching": "global IoU greedy; class independent; one-to-one; fixed index ties",
            "overlap_threshold": threshold, "truth": sum(sum(row) for row in matrix[:-1]),
            "predictions": sum(sum(row[:-1]) for row in matrix), "per_class": per_class,
            "most_missed": worst, "failures": failures,
            "background_true_negatives": "unmeasured; cell is null"}


def confusion_report(truth, predictions, roles=SPORTS_ROLES, *, threshold=0.5, operation="identify-ui"):
    if (not isinstance(roles, (list, tuple)) or not 1 <= len(roles) <= 64
            or any(not isinstance(r, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,39}", r) or r == "background" for r in roles)
            or len(set(roles)) != len(roles)):
        raise Refusal("unique bounded identification classes required")
    if not isinstance(operation, str) or not re.fullmatch(r"[a-z][a-z0-9_.-]{0,79}", operation):
        raise Refusal("operation identity required")
    threshold = finite(threshold, 0.01, 1, "overlap threshold")
    truth = _objects(truth, roles, "truth")
    predictions = _objects(predictions, roles, "prediction")
    classes = [*roles, "background"]
    matrix = [[0] * len(classes) for _ in classes]
    matrix[-1][-1] = None
    pairs = []
    for ti, target in enumerate(truth):
        for pi, predicted in enumerate(predictions):
            iou = overlap(target["box"], predicted["box"])
            if iou >= threshold:
                pairs.append((iou, ti, pi))
    pairs.sort(key=lambda pair: (-pair[0], pair[1], pair[2]))
    used_truth, used_predictions, failures = set(), set(), []
    for iou, ti, pi in pairs:
        if ti in used_truth or pi in used_predictions:
            continue
        used_truth.add(ti)
        used_predictions.add(pi)
        target, predicted = truth[ti], predictions[pi]
        matrix[classes.index(target["role"])][classes.index(predicted["role"])] += 1
        if target["role"] != predicted["role"]:
            failures.append({"kind": "wrong_class", "expected": target, "predicted": predicted, "iou": iou})
    for ti, target in enumerate(truth):
        if ti not in used_truth:
            matrix[classes.index(target["role"])][-1] += 1
            failures.append({"kind": "missed", "expected": target, "predicted": None})
    for pi, predicted in enumerate(predictions):
        if pi not in used_predictions:
            matrix[-1][classes.index(predicted["role"])] += 1
            failures.append({"kind": "unexpected", "expected": None, "predicted": predicted})
    return _summary(classes, matrix, failures, operation=operation, threshold=threshold)


def merge_confusions(reports):
    if not isinstance(reports, list) or not 1 <= len(reports) <= 10000:
        raise Refusal("confusion report budget")
    first = reports[0]
    if not isinstance(first, dict) or not isinstance(first.get("classes"), list):
        raise Refusal("confusion schema")
    classes = first["classes"]
    # Validate the taxonomy through the same public boundary.
    confusion_report([], [], classes[:-1], operation=first.get("operation"), threshold=first.get("overlap_threshold"))
    if classes[-1] != "background":
        raise Refusal("confusion background class")
    combined = [[0] * len(classes) for _ in classes]
    combined[-1][-1] = None
    failures = []
    for report in reports:
        if (not isinstance(report, dict) or report.get("schema") != "identification-confusion/1"
                or report.get("classes") != classes or report.get("operation") != first["operation"]
                or report.get("overlap_threshold") != first["overlap_threshold"]):
            raise Refusal("mixed confusion recipe")
        matrix = report.get("matrix")
        if not isinstance(matrix, list) or len(matrix) != len(classes):
            raise Refusal("confusion matrix shape")
        for i, row in enumerate(matrix):
            if not isinstance(row, list) or len(row) != len(classes):
                raise Refusal("confusion row shape")
            for j, value in enumerate(row):
                if i == j == len(classes) - 1:
                    if value is not None:
                        raise Refusal("unmeasured true negatives")
                elif type(value) is not int or not 0 <= value <= 10_000_000:
                    raise Refusal("confusion count bounds")
                else:
                    combined[i][j] += value
        if not isinstance(report.get("failures"), list):
            raise Refusal("confusion failure evidence")
        failures.extend(report["failures"])
    return _summary(classes, combined, failures, operation=first["operation"], threshold=first["overlap_threshold"])
