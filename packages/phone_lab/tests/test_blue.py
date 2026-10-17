import copy

import pytest

from phone_lab.benchmark import Refusal
from phone_lab.blue import make_blue_packet, score_contacts


def event(kind, timestamp, x=100, y=100):
    return {"kind": kind, "time_ms": timestamp, "x": x, "y": y, "pointer": 1}


def taps(durations):
    events = []
    for index, duration in enumerate(durations):
        start = 1000 + index * 1000
        events.extend([event("down", start), event("up", start + duration)])
    return make_blue_packet("generated-session", (390, 700), events)


def test_known_contact_dwell_patterns_are_hypotheses():
    result = score_contacts(taps([5, 5, 5, 5]))
    assert result["features"]["contacts"] == 4
    assert result["features"]["dwell_ms"]["p50_ms"] == 5
    assert result["flags"] == ["short_contact_dwell", "regular_contact_dwell"]
    assert result["robot_probability"] is None
    assert result["human_validation"] == "pending consented controls"
    assert result["sanctions"] is False
    assert score_contacts(taps([65, 100, 130, 160]))["flags"] == []


def test_hand_checked_straight_contact_path():
    events = [event("down", 1000, 10, 20)]
    events.extend(event("move", 1000 + index * 10, 10 + index * 10, 20) for index in range(1, 6))
    events.append(event("up", 1060, 60, 20))
    result = score_contacts(make_blue_packet("drag-session", (390, 700), events))
    assert result["features"]["contact_paths"][0]["length_px"] == 50
    assert result["features"]["contact_paths"][0]["linearity"] == 1
    assert result["flags"] == ["straight_contact_path"]


def test_export_excludes_privileged_labels_and_entered_text():
    raw = event("down", 1) | {"device": "owned", "frame": "a:1", "value": "private text"}
    packet = make_blue_packet("generated-session", (390, 700), [raw])
    assert set(packet["events"][0]) == {"kind", "time_ms", "x", "y", "pointer"}
    assert "private text" not in str(packet)
    assert score_contacts(packet)["features"]["incomplete_contacts"] == 1


def test_cancel_and_no_contacts_do_not_invent_observations():
    empty = score_contacts(taps([]))
    assert empty["features"]["contacts"] == 0
    assert empty["flags"] == []
    packet = make_blue_packet("cancel-session", (390, 700), [event("down", 1), event("cancel", 2)])
    result = score_contacts(packet)
    assert result["features"]["contacts"] == 0
    assert result["features"]["cancelled_contacts"] == 1


@pytest.mark.parametrize(
    "field", ["robot_label", "motor_path", "camera", "target_boxes", "capability"]
)
def test_blue_packet_rejects_privileged_side_channels(field):
    packet = taps([100])
    with pytest.raises(Refusal):
        score_contacts(packet | {field: "generated"})
    packet["events"][0][field] = "generated"
    with pytest.raises(Refusal):
        score_contacts(packet)


@pytest.mark.parametrize(
    "change",
    [{"x": float("nan")}, {"x": True}, {"y": 701}, {"pointer": -1}, {"kind": "hover-camera"}],
)
def test_bad_contact_values_refuse(change):
    packet = taps([100])
    packet["events"][0].update(change)
    with pytest.raises(Refusal):
        score_contacts(packet)


def test_timestamp_regression_and_duplicate_down_refuse():
    for events in (
        [event("down", 100), event("up", 99)],
        [event("down", 100), event("down", 101)],
    ):
        with pytest.raises(Refusal):
            score_contacts(make_blue_packet("bad-session", (390, 700), events))


def test_scoring_does_not_mutate_the_immutable_input():
    packet = taps([100, 130])
    before = copy.deepcopy(packet)
    score_contacts(packet)
    assert packet == before
