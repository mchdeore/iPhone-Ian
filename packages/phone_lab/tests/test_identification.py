import copy

import pytest

from phone_lab.benchmark import Refusal
from phone_lab.sportsbook.evaluation import confusion_report, merge_confusions


def detection(role, x, *, ident="label", confidence=1):
    return {"id": ident, "role": role, "confidence": confidence,
            "box": {"x": x, "y": 0, "width": 10, "height": 10}}


def test_hand_calculated_wrong_class_missed_object_and_extra_prediction():
    truth = [detection("odds", 0, ident="odds"), detection("line", 20, ident="line")]
    predicted = [detection("line", 0, ident="wrong"), detection("odds", 40, ident="extra")]
    report = confusion_report(truth, predicted, ("odds", "line"))
    assert report["classes"] == ["odds", "line", "background"]
    assert report["matrix"] == [[0, 1, 0], [0, 0, 1], [1, 0, None]]
    assert report["per_class"]["odds"]["false_negative"] == 1
    assert report["per_class"]["line"]["false_positive"] == 1
    assert [f["kind"] for f in report["failures"]] == ["wrong_class", "missed", "unexpected"]


def test_matching_is_one_to_one_and_does_not_hide_wrong_classes():
    truth = [detection("odds", 0)]
    predicted = [detection("line", 0, ident="first"), detection("odds", 0, ident="second")]
    report = confusion_report(truth, predicted, ("odds", "line"))
    assert report["matrix"][0][1] == 1
    assert report["matrix"][2][0] == 1
    assert report["truth"] == 1 and report["predictions"] == 2


def test_frames_are_scored_separately_then_merged_without_cross_frame_box_matches():
    first = confusion_report([detection("odds", 0)], [], ("odds", "line"))
    second = confusion_report([], [detection("odds", 0)], ("odds", "line"))
    combined = merge_confusions([first, second])
    assert combined["matrix"][0][0] == 0
    assert combined["matrix"][0][2] == combined["matrix"][2][0] == 1
    assert combined["per_class"]["line"]["recall"] is None
    assert combined["most_missed"][0]["class"] == "odds"


def test_bad_roles_boxes_scores_and_mixed_taxonomy_refuse_without_mutating_inputs():
    truth = [detection("odds", 0)]
    before = copy.deepcopy(truth)
    for predicted in ([detection("unknown", 0)], [detection("odds", 0, confidence=float("nan"))],
                      [detection("odds", -1)], [detection("odds", 0) | {"box": {"x": 0, "y": 0, "width": 0, "height": 10}}]):
        with pytest.raises(Refusal):
            confusion_report(truth, predicted, ("odds", "line"))
    with pytest.raises(Refusal):
        merge_confusions([confusion_report([], [], ("odds",)), confusion_report([], [], ("line",))])
    assert truth == before
