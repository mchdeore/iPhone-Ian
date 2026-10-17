from phone_lab.metrics import detection_metrics, edit_distance, latency, ocr_metrics, overlap


def test_metrics_matching_does_not_double_count_or_merge_classes():
    box = {"x": 10, "y": 10, "width": 40, "height": 40}
    t = [{"role": "button", "box": box}]
    p = [
        {"role": "button", "box": box, "confidence": 0.9},
        {"role": "field", "box": box, "confidence": 0.99},
    ]
    assert overlap(box, box) == 1
    assert detection_metrics(t, p) == {
        "true_positive": 1,
        "false_positive": 1,
        "false_negative": 0,
        "safe_center_hits": 1,
        "truth": 1,
        "predictions": 2,
        "class_aware": True,
    }
    assert detection_metrics(t, p, class_aware=False)["true_positive"] == 1
    assert detection_metrics(t, [])["false_negative"] == 1


def test_ocr_counts_missing_and_wrong_text_and_latency():
    b = {"x": 0, "y": 0, "width": 40, "height": 40}
    labels = [{"box": b, "text": "Continue"}]
    assert ocr_metrics(labels, [])["character_errors"] == 8
    r = ocr_metrics(labels, [{"box": b, "text": "Contnue"}])
    assert r["character_errors"] == 1 and r["exact_targets"] == 0
    assert edit_distance("", "") == 0 and edit_distance("abc", "xyz") == 3
    assert latency([1, 2, 3, 4]) == {"count": 4, "p50_ms": 2.5, "p95_ms": 3.8499999999999996}
