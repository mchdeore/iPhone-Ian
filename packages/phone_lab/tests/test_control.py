from dataclasses import replace

import pytest

from phone_lab.benchmark import Box, Refusal
from phone_lab.control import (
    Calibration,
    FakeSerial,
    Frame,
    Intent,
    VirtualController,
    replay,
    undo_letterbox,
)


@pytest.fixture
def calibration():
    return Calibration.fit(
        "one",
        (400, 800),
        [[0, 0], [400, 0], [0, 800], [400, 800]],
        [[0, 0], [40, 0], [0, 80], [40, 80]],
        [[100, 200], [300, 600]],
        [[10, 20], [30, 60]],
        Box(0, 0, 40, 80),
    )


@pytest.fixture
def ready(calibration):
    c = VirtualController(FakeSerial(), calibration)
    c.home()
    f = Frame("one", "session", "session:1", 10, 400, 800)
    c.arm(f, "single-use", 10)
    i = Intent(
        "tap",
        "one",
        "session",
        "session:1",
        calibration.digest,
        ((200, 400),),
        0.95,
        11,
        "single-use",
    )
    return c, f, i


def test_calibration_independent_error_and_letterbox(calibration):
    assert calibration.map(200, 400) == pytest.approx((20, 40))
    assert undo_letterbox(
        320, 320, source=(400, 800), resized=(320, 640), pad=(160, 0)
    ) == pytest.approx((200, 400))
    with pytest.raises(Refusal):
        undo_letterbox(20, 100, source=(400, 800), resized=(320, 640), pad=(160, 0))
    with pytest.raises(Refusal, match="error"):
        Calibration.fit(
            "one",
            (400, 800),
            [[0, 0], [400, 0], [0, 800], [400, 800]],
            [[0, 0], [40, 0], [0, 80], [40, 80]],
            [[100, 200], [300, 600]],
            [[10, 25], [30, 60]],
            Box(0, 0, 40, 80),
        )
    with pytest.raises(Refusal, match="degenerate"):
        Calibration.fit(
            "one",
            (400, 800),
            [[0, 0], [1, 1], [2, 2], [3, 3]],
            [[0, 0], [1, 1], [2, 2], [3, 3]],
            [[4, 4], [5, 5]],
            [[4, 4], [5, 5]],
            Box(0, 0, 40, 80),
        )


def test_generated_tap_replay_and_restart_refusal(ready, calibration):
    c, f, i = ready
    r = c.execute(i, f, 10)
    assert r["mapped_mm"][0] == pytest.approx((20, 40))
    assert r["simulated"] and not r["physical_acceptance"]
    assert i.token not in str(r)
    assert replay([r], calibration)[0]["commands"] == r["commands"]
    with pytest.raises(Refusal):
        c.execute(i, f, 10)
    with pytest.raises(Refusal):
        c.arm(f, i.token, 10)
    cold = VirtualController(FakeSerial(), calibration)
    with pytest.raises(Refusal):
        cold.arm(f, "new", 10)


@pytest.mark.parametrize(
    "change",
    [
        {"kind": "G1 X900"},
        {"device": "two"},
        {"session": "other"},
        {"frame": "session:0"},
        {"calibration": "unverified"},
        {"token": "other"},
        {"expires_at": 9},
        {"expires_at": 100},
        {"confidence": 0.7},
        {"confidence": float("nan")},
        {"points": ((0, 0),)},
        {"points": ((999, 400),)},
        {"points": ((200, float("inf")),)},
        {"points": ((10, 10), (20, 20))},
    ],
)
def test_refusal_never_issues_motion(ready, change):
    c, f, i = ready
    before = c.serial.commands.copy()
    with pytest.raises(Refusal):
        c.execute(replace(i, **change), f, 10)
    assert c.serial.commands == before


def test_stale_two_phone_and_reset_identity(ready):
    c, f, i = ready
    for altered, now in [
        (f, 13),
        (replace(f, device="two"), 10),
        (replace(f, marker="session:2"), 10),
        (replace(f, captured_at=11), 10),
    ]:
        with pytest.raises(Refusal):
            c.execute(i, altered, now)


def test_stop_acknowledgement_failure_and_drag(ready):
    c, f, i = ready
    c.stop()
    with pytest.raises(Refusal):
        c.execute(i, f, 10)
    c.arm(f, "fresh", 10)
    c.serial.fail_next = True
    with pytest.raises(Refusal, match="acknowledgement"):
        c.execute(replace(i, token="fresh"), f, 10)
    assert c.stopped
    c.arm(f, "drag-token", 10)
    r = c.execute(
        replace(i, kind="drag", token="drag-token", points=((100, 200), (300, 600))), f, 10
    )
    assert len(r["mapped_mm"]) == 2
    assert any(x["command"] == "DRAG GENERATED" for x in r["commands"])


def test_two_phone_fixture_keeps_separate_calibration_and_frame_identity(calibration):
    second = Calibration.fit(
        "two",
        (400, 800),
        [[0, 0], [400, 0], [0, 800], [400, 800]],
        [[100, 0], [140, 0], [100, 80], [140, 80]],
        [[100, 200], [300, 600]],
        [[110, 20], [130, 60]],
        Box(100, 0, 40, 80),
    )
    frames = [
        Frame("one", "first", "first:1", 10, 400, 800),
        Frame("two", "second", "second:1", 10, 400, 800),
    ]
    results = []
    for cal, frame, other in [(calibration, frames[0], frames[1]), (second, frames[1], frames[0])]:
        c = VirtualController(FakeSerial(), cal)
        c.home()
        c.arm(frame, "fixture-token", 10)
        i = Intent(
            "tap",
            frame.device,
            frame.session,
            frame.marker,
            cal.digest,
            ((200, 400),),
            0.95,
            11,
            "fixture-token",
        )
        with pytest.raises(Refusal):
            c.execute(i, other, 10)
        results.append(c.execute(i, frame, 10))
    assert results[0]["mapped_mm"][0] == pytest.approx((20, 40))
    assert results[1]["mapped_mm"][0] == pytest.approx((120, 40))
    assert results[0]["calibration_sha256"] != results[1]["calibration_sha256"]
