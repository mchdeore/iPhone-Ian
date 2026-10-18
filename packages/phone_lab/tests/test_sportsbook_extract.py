import copy

import pytest

from phone_lab.benchmark import Refusal
from phone_lab.sportsbook.extract import parse_page
from phone_lab.sportsbook.fixtures import provider_snapshot


def text(value, x, y, width=60, confidence=1):
    return {"text": value, "confidence": confidence,
            "box": {"x": x, "y": y, "width": width, "height": 14}}


def observed_page():
    snapshot = provider_snapshot(17, 0)
    q = snapshot["quotes"][0]
    values = [text("Provider A", 20, 30), text("Decimal odds", 260, 30),
              text("Updated " + q["quote_time"].replace("T", " ").replace("Z", " UTC"), 20, 70, 200),
              text("Event " + q["event_id"], 20, 105),
              text(q["away"] + " @ " + q["home"], 20, 135, 250),
              text("Start " + q["start_time"].replace("T", " ").replace("Z", " UTC"), 20, 165, 200)]
    for index, market in enumerate(("moneyline", "spread")):
        y = 220 + index * 220
        values += [text(market.title(), 20, y), text("Full game", 300, y),
                   text("Selection", 20, y + 30), text("Line", 180, y + 30, 30),
                   text("Odds", 230, y + 30, 30), text("State", 300, y + 30, 30)]
        for number, quote in enumerate([r for r in snapshot["quotes"] if r["market"] == market]):
            row_y = y + 70 + number * 55
            values += [text(quote["selection"], 20, row_y, 100),
                       text(quote["line"] or "—", 180, row_y, 30),
                       text(quote["odds"], 230, row_y, 45), text("Open", 300, row_y, 45)]
    return snapshot, values


def test_ocr_only_page_association_does_not_receive_hidden_truth_and_is_order_independent():
    snapshot, values = observed_page()
    result = parse_page(list(reversed(values)))
    assert result["quotes"] == snapshot["quotes"]
    assert result["refusals"] == []
    assert result["inputs"] == "OCR text, confidence and observed boxes only"
    assert len(result["fields"]) > 20


def test_uncertain_or_missing_row_value_rejects_that_record_without_guessing():
    _, values = observed_page()
    bad = copy.deepcopy(values)
    price = next(v for v in bad if v["text"].startswith("1.") and v["box"]["y"] == 290)
    price["confidence"] = 0.1
    result = parse_page(bad)
    assert len(result["quotes"]) == 3
    assert len(result["refusals"]) == 1
    assert result["refusals"][0]["operation"] == "extract-row"


def test_duplicate_global_identity_bad_calendar_and_unsupported_format_refuse():
    _, values = observed_page()
    with pytest.raises(Refusal):
        parse_page(values + [text("Provider B", 200, 30)])
    for replacement in ("Updated 2026-02-30 18:00:00 UTC", "Updated 2026-01-18 18:00:00"):
        changed = [v | {"text": replacement} if v["text"].startswith("Updated ") else v for v in values]
        with pytest.raises(Refusal):
            parse_page(changed)
    changed = [v | {"text": "American odds"} if v["text"] == "Decimal odds" else v for v in values]
    with pytest.raises(Refusal):
        parse_page(changed)


def test_participant_fragments_join_only_adjacent_confident_regions_inside_event_header():
    snapshot, values = observed_page()
    values = [v for v in values if "@" not in v["text"]]
    fragments = [text("Lake Wolves @", 30, 135, 130), text("East Hawks", 170, 135, 96)]
    assert parse_page(values + fragments)["quotes"] == snapshot["quotes"]
    for bad in (
        [fragments[0], fragments[1] | {"confidence": 0.2}],
        [fragments[0], text("East Hawks", 290, 135, 96)],
        [fragments[0], fragments[1], text("Other @ Pair", 280, 135, 60)],
        [text("Lake Wolves @", 30, 700, 130), text("East Hawks", 170, 700, 96)],
    ):
        with pytest.raises(Refusal):
            parse_page(values + bad)


def test_missing_observed_moneyline_dash_is_not_filled_from_market_rules():
    _, values = observed_page()
    values = [v for v in values if not (v["text"] == "—" and v["box"]["y"] == 345)]
    result = parse_page(values)
    assert len(result["quotes"]) == 3
    assert len(result["refusals"]) == 1
