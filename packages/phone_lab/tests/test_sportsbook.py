import copy
import sqlite3

import pytest

from phone_lab.benchmark import Refusal
from phone_lab.sportsbook.contracts import validate_quote
from phone_lab.sportsbook.fixtures import provider_snapshot
from phone_lab.sportsbook.storage import QuoteStore, score_database


def test_synthetic_provider_sequence_is_deterministic_and_changed_values_are_explicit():
    initial = provider_snapshot(17, 0, provider="provider-a")
    assert initial == provider_snapshot(17, 0, provider="provider-a")
    changed = provider_snapshot(17, 1, provider="provider-a")
    suspended = provider_snapshot(17, 2, provider="provider-a")
    assert len(initial["quotes"]) == 4
    assert changed["quotes"][0]["odds"] != initial["quotes"][0]["odds"]
    assert suspended["quotes"][1]["status"] == "suspended"
    assert suspended["quotes"][1]["odds"] is None
    assert initial["sequence_group"] == changed["sequence_group"] == suspended["sequence_group"]
    for seed, phase in ((True, 0), (-1, 0), (0, True), (0, 3)):
        with pytest.raises(Refusal):
            provider_snapshot(seed, phase)


def test_exact_decimal_and_line_contract_refuses_ambiguous_or_untyped_values():
    quote = provider_snapshot(0, 0)["quotes"][2]
    assert validate_quote(quote)["line"] == quote["line"]
    assert isinstance(validate_quote(quote)["odds"], str)
    for change in ({"odds": 1.91}, {"odds": "1e2"}, {"odds": "1,91"}, {"odds": "1.910"},
                   {"line": "-2,5"}, {"line": -2.5}, {"quote_time": "2026-01-01 18:00"},
                   {"status": "maybe"}, {"capability": "private"}):
        with pytest.raises(Refusal):
            validate_quote(quote | change)


def test_canonical_half_point_boundaries_and_calendar_errors():
    quote = provider_snapshot(0, 0)["quotes"][2]
    for line in ("0", "100", "-100", "199.5", "-199.5"):
        assert validate_quote(quote | {"line": line})["line"] == line
    for change in ({"line": "-0"}, {"line": "200.5"}, {"line": "2.25"},
                   {"quote_time": "2026-02-30T18:00:00Z"}, {"event_id": "E١٢٣٤٥٦"}):
        with pytest.raises(Refusal):
            validate_quote(quote | change)


def test_actual_database_update_sequence_replay_and_stale_quote_history(tmp_path):
    database = tmp_path / "observations.sqlite"
    store = QuoteStore(database)
    initial, changed, suspended = [provider_snapshot(17, phase) for phase in range(3)]
    first = store.ingest("a" * 64, initial["quotes"])
    assert first["inserted"] == 4
    assert store.ingest("a" * 64, initial["quotes"])["replayed"] is True
    assert store.ingest("b" * 64, changed["quotes"])["updated"] == 4
    assert store.ingest("c" * 64, suspended["quotes"])["updated"] == 4
    assert store.ingest("d" * 64, initial["quotes"])["stale_ignored"] == 4
    store.close()
    reopened = QuoteStore(database)
    report = score_database(reopened, suspended["quotes"])
    assert report["correct_records"] == report["expected_records"] == 4
    assert report["row_precision"] == report["row_recall"] == 1
    assert report["wrong_records"] == report["missing_records"] == 0
    assert reopened.counts() == {"captures": 4, "observations": 16, "latest": 4}
    assert reopened.latest() == suspended["quotes"]
    reopened.close()


def test_invalid_batch_and_conflicting_replay_have_no_partial_writes(tmp_path):
    store = QuoteStore(tmp_path / "observations.sqlite")
    quotes = provider_snapshot(0, 0)["quotes"]
    bad = copy.deepcopy(quotes)
    bad[-1]["odds"] = "1.19oops"
    with pytest.raises(Refusal):
        store.ingest("a" * 64, bad)
    assert store.counts() == {"captures": 0, "observations": 0, "latest": 0}
    store.ingest("a" * 64, quotes)
    changed = copy.deepcopy(quotes)
    changed[-1]["odds"] = "9.99"
    with pytest.raises(Refusal):
        store.ingest("a" * 64, changed)
    with pytest.raises(Refusal):
        store.ingest("b" * 64, changed)
    assert store.counts() == {"captures": 1, "observations": 4, "latest": 4}
    with pytest.raises(Refusal):
        store.ingest("c" * 64, quotes + [quotes[0]])
    assert store.counts()["captures"] == 1
    store.close()


def test_scoring_reads_persisted_rows_and_exposes_price_and_join_losses(tmp_path):
    store = QuoteStore(tmp_path / "observations.sqlite")
    expected = provider_snapshot(17, 0)["quotes"]
    observed = copy.deepcopy(expected)
    observed[0]["odds"] = "1.19"
    observed[1]["event_id"] = "E999999"
    store.ingest("a" * 64, observed)
    report = score_database(store, expected)
    assert report["correct_records"] == 2
    assert report["wrong_records"] == 2
    assert report["missing_records"] == 1
    assert report["unexpected_records"] == 1
    assert report["field_errors"]["odds"] == 1
    assert report["score"] == 0.5
    store.close()


def test_database_scoring_scope_is_explicit_and_still_exposes_wrong_events(tmp_path):
    store = QuoteStore(tmp_path / "observations.sqlite")
    a = provider_snapshot(17, 0, provider="provider-a")["quotes"]
    b = provider_snapshot(17, 0, provider="provider-b")["quotes"]
    store.ingest("a" * 64, a)
    store.ingest("b" * 64, b)
    assert score_database(store, a)["unexpected_records"] == 4
    scoped = score_database(store, a, provider_id="provider-a")
    assert scoped["score"] == 1
    assert scoped["scope"] == {"provider_id": "provider-a"}
    wrong = [a[0] | {"event_id": "E999999"}]
    store.ingest("c" * 64, wrong)
    assert score_database(store, a, provider_id="provider-a")["unexpected_records"] == 1
    with pytest.raises(Refusal):
        score_database(store, a + b, provider_id="provider-a")
    store.close()


def test_missing_database_rows_count_as_missing_for_every_field(tmp_path):
    store = QuoteStore(tmp_path / "observations.sqlite")
    quotes = provider_snapshot(17, 0)["quotes"]
    store.ingest("a" * 64, quotes[:3])
    report = score_database(store, quotes)
    assert set(report["field_missing"].values()) == {1}
    assert set(report["field_support"].values()) == {4}
    assert set(report["field_errors"].values()) == {0}
    assert report["score"] == 0.75
    store.close()


def test_store_refuses_foreign_database_and_symlink_without_modifying_original(tmp_path):
    foreign = tmp_path / "foreign.sqlite"
    with sqlite3.connect(foreign) as db:
        db.execute("CREATE TABLE unrelated(value TEXT)")
        db.execute("INSERT INTO unrelated VALUES ('preserve original')")
    before = foreign.read_bytes()
    with pytest.raises(Refusal):
        QuoteStore(foreign)
    assert foreign.read_bytes() == before
    link = tmp_path / "link.sqlite"
    link.symlink_to(foreign)
    with pytest.raises(Refusal):
        QuoteStore(link)
    assert foreign.read_bytes() == before


def test_sql_failure_rolls_back_capture_entities_quotes_and_latest(tmp_path):
    store = QuoteStore(tmp_path / "observations.sqlite")
    initial = provider_snapshot(17, 0)["quotes"]
    changed = provider_snapshot(17, 1)["quotes"]
    store.ingest("a" * 64, initial)
    store.db.execute("CREATE TRIGGER forced_failure BEFORE INSERT ON observations BEGIN SELECT RAISE(ABORT,'controlled failure'); END")
    store.db.commit()
    with pytest.raises(Refusal):
        store.ingest("b" * 64, changed)
    assert store.latest() == initial
    assert store.counts() == {"captures": 1, "observations": 4, "latest": 4}
    store.close()
