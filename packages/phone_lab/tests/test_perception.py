from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from phone_lab.benchmark import Refusal


def detection(role="button", confidence=0.96, **box):
    return {
        "role": role,
        "confidence": confidence,
        "box": {"x": 100, "y": 200, "width": 100, "height": 50, **box},
    }


def text(value, confidence=1.0, **box):
    return {
        "text": value,
        "confidence": confidence,
        "box": {"x": 120, "y": 210, "width": 60, "height": 15, **box},
    }


def choose(predictions, recognized=(), *, role="button", name="Continue"):
    from phone_lab.perception import choose_target

    return choose_target(predictions, recognized, role=role, name=name, viewport=(390, 700))


def test_button_selection_uses_text_inside_its_own_box():
    predictions = [detection(), detection(x=230)]
    recognized = [text("Cancel"), text("Continue", x=240)]
    assert choose(predictions, recognized)["point"] == (280, 225)


def test_ocr_edit_score_is_propagated_instead_of_fixed_intent_confidence():
    result = choose([detection()], [text("Dismiss OverlayC")], name="Dismiss Overlay")
    assert result["point"] == (150, 225)
    assert result["confidence"] == pytest.approx(0.9375)


def test_unique_drag_destination_uses_class_and_real_detector_confidence():
    result = choose(
        [detection("handle"), detection("destination", 0.98), detection("destination", 0.33)],
        role="destination",
        name=None,
    )
    assert result["point"] == (150, 225)
    assert result["confidence"] == 0.98


@pytest.mark.parametrize("role", ["handle", "field", "list"])
def test_region_roles_require_one_high_confidence_detection(role):
    assert choose([detection(role)], role=role, name=None)["point"] == (150, 225)


@pytest.mark.parametrize(
    ("predictions", "recognized"),
    [
        ([detection(confidence=0.899)], [text("Continue")]),
        ([detection()], [text("Continue", confidence=0.899)]),
        ([detection()], [text("Continua")]),
        ([detection()], [text("Continue", y=50)]),
        ([detection(), detection(x=230)], [text("Continue"), text("Continue", x=240)]),
        ([], []),
    ],
)
def test_low_scores_unrelated_text_and_ambiguous_targets_refuse(predictions, recognized):
    with pytest.raises(Refusal, match="ambiguous/missing"):
        choose(predictions, recognized)


@pytest.mark.parametrize(
    "bad",
    [
        detection(confidence=float("nan")),
        detection(confidence=True),
        detection(confidence=1.01),
        detection(x=-1),
        detection(x=350),
        detection(width=0),
        detection("dialog-close"),
    ],
)
def test_malformed_or_unsupported_predictions_cannot_reach_control(bad):
    with pytest.raises(Refusal, match="invalid perception"):
        choose([bad], [text("Continue")])


def test_ocr_confidence_and_box_are_validated_before_matching():
    with pytest.raises(Refusal, match="invalid perception"):
        choose([detection()], [text("Continue", confidence=True)])
    with pytest.raises(Refusal, match="invalid perception"):
        choose([detection()], [text("Continue", x=-1)])


def test_buttons_cannot_be_selected_by_class_alone():
    with pytest.raises(Refusal, match="button label"):
        choose([detection()], role="button", name=None)


def test_unbounded_predictions_and_labels_refuse():
    with pytest.raises(Refusal, match="invalid perception"):
        choose([detection()] * 33, [text("Continue")])
    with pytest.raises(Refusal, match="invalid perception"):
        choose([detection()], [text("x" * 257)])


def test_json_array_class_is_a_controlled_refusal():
    with pytest.raises(Refusal, match="invalid perception"):
        choose([detection(role=[])], [text("Continue")])
    with pytest.raises(Refusal, match="invalid perception"):
        choose([], role=[], name=None)


def test_fixed_square_boxes_map_back_using_the_actual_rounded_padding():
    from phone_lab.perception import unletterbox_box

    result = unletterbox_box(
        (232.4285714286, 182.8571428571, 323.8571428571, 228.5714285714),
        viewport=(390, 700),
    )
    assert result == pytest.approx({"x": 100, "y": 200, "width": 100, "height": 50})


@pytest.mark.parametrize("box", [(0, 0, 100, 100), (100, 100, 99, 200), (0, 0, 650, 640)])
def test_padding_only_and_invalid_model_boxes_cannot_become_targets(box):
    from phone_lab.perception import unletterbox_box

    with pytest.raises(Refusal, match="invalid perception"):
        unletterbox_box(box, viewport=(390, 700))


@pytest.mark.parametrize(
    ("include_hash", "message"),
    [(False, "--detector requires --detector-sha256"), (True, "detector checkpoint hash mismatch")],
)
def test_detector_checkpoint_identity_refuses_before_starting_browser(tmp_path, include_hash, message):
    checkpoint = tmp_path / "fixture.pt"
    checkpoint.write_bytes(b"generated identity test; not a model")
    output = tmp_path / "workflow"
    command = [
        sys.executable,
        str(Path(__file__).parents[1] / "tools/owned_policy_smoke.py"),
        str(output),
        "--ocr", str(tmp_path / "unavailable-ocr"),
        "--chrome", str(tmp_path / "unavailable-browser"),
        "--detector", str(checkpoint),
    ]
    if include_hash:
        command.extend(["--detector-sha256", "0" * 64])
    process = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert process.returncode != 0 and message in process.stderr
    assert not output.exists()
