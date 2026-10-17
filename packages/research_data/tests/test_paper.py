import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

from research_data.paper import tennis_report

CSV = (
    b"tourney_id,tourney_date,match_num,winner_id,loser_id,score\n"
    b"old,20200101,1,2,1,6-4 6-4\n"
    b"test,20210101,1,2,1,6-4 6-4\n"
)
SOURCE = {
    "dataset_id": "generated-tennis",
    "source_url": "https://example.invalid/generated.csv",
    "provenance": "Generated outcome-only test rows",
    "license_status": "review_required",
    "fetched": "2026-10-17T12:00:00-04:00",
    "published": "unknown",
    "observed": "unknown",
}


def report(data=CSV, source=None, digest=None, **kwargs):
    return tennis_report(
        data,
        expected_sha256=digest or hashlib.sha256(data).hexdigest(),
        source=SOURCE if source is None else source,
        holdout_start="20210101",
        **kwargs,
    )


def test_hand_calculated_outcome_and_provenance():
    result = report()
    p = 1 / (1 + 10 ** (20 / 400))
    assert math.isclose(result["baseline"]["heldout"]["elo"]["brier"], p * p)
    assert result["baseline"]["heldout"]["neutral"]["brier"] == 0.25
    assert result["source"]["license_status"] == "review_required"
    assert result["source"]["published"] == "unknown"
    assert result["source"]["rows"] == 2
    assert result["source"]["sha256"] == hashlib.sha256(CSV).hexdigest()
    assert result["market_prices_used"] is False
    assert result["live_execution"] is False
    assert result["distribution_rights_approved"] is False


def test_repeat_and_row_order_preserve_outcome_recipe():
    assert report() == report()
    lines = CSV.splitlines(keepends=True)
    reversed_rows = lines[0] + lines[2] + lines[1]
    shuffled = report(reversed_rows)
    assert shuffled["baseline"] == report()["baseline"]
    assert shuffled["source"]["sha256"] != report()["source"]["sha256"]


def test_post_match_columns_and_unvalidated_prices_are_not_features():
    extra = (
        b"tourney_id,tourney_date,match_num,winner_id,loser_id,score,winner_aces,odds\n"
        b"old,20200101,1,2,1,6-4 6-4,999,1.5\n"
        b"test,20210101,1,2,1,6-4 6-4,0,9.0\n"
    )
    result = report(extra)
    assert result["baseline"] == report()["baseline"]
    assert result["market_prices_used"] is False
    assert result["price_and_execution_validation"] == "not performed"


@pytest.mark.parametrize(
    "data",
    [
        b"version https://git-lfs.github.com/spec/v1\n",
        b"\xff",
        b"tourney_id,tourney_id\nold,old\n",
        b"tourney_id,,winner_id\nold,1,2\n",
        b"tourney_date,winner_id,loser_id,score\n20200101,1,2,6-4\n",
        CSV + b"bad,row\n",
        CSV + b"bad,row,with,too,many,columns,here\n",
        b'tourney_id,tourney_date,match_num,winner_id,loser_id,score\n"unclosed',
    ],
)
def test_bad_schema_and_payloads_refuse(data):
    with pytest.raises(ValueError):
        report(data)


@pytest.mark.parametrize("digest", ["0" * 64, "invalid", "A" * 64])
def test_reviewed_digest_required(digest):
    with pytest.raises(ValueError):
        report(digest=digest)


@pytest.mark.parametrize(
    "change",
    [
        {"source_url": "https://example.invalid/data?token=generated-secret"},
        {"fetched": "2026-10-17T12:00:00"},
        {"license_status": ""},
        {"provenance": ""},
        {"dataset_id": "../generated"},
        {"published": None},
        {"unexpected_secret_field": "generated"},
        {"source_url": "https://example.invalid/" + "x" * 2048},
        {"fetched": "2026-10-17T12:00:00." + "1" * 128 + "-04:00"},
    ],
)
def test_invalid_source_metadata_refuses(change):
    with pytest.raises(ValueError):
        report(source=SOURCE | change)


def test_no_training_or_holdout_is_not_completed_baseline():
    header, train, heldout = CSV.splitlines(keepends=True)
    for data in (header, header + train, header + heldout):
        with pytest.raises(ValueError):
            report(data)


def cli(tmp_path, *, digest=None, input_path=None, timeout=10):
    data = tmp_path / "input.csv" if input_path is None else input_path
    metadata = tmp_path / "source.json"
    output = tmp_path / "result.json"
    if input_path is None:
        data.write_bytes(CSV)
    metadata.write_text(json.dumps(SOURCE))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    process = subprocess.run(
        [
            sys.executable, "-m", "research_data.paper", str(data),
            "--source", str(metadata), "--sha256", digest or hashlib.sha256(CSV).hexdigest(),
            "--holdout-start", "20210101", "--output", str(output),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return process, output


def test_cli_writes_private_deterministic_report(tmp_path):
    process, output = cli(tmp_path)
    assert process.returncode == 0, process.stderr
    assert json.loads(output.read_text()) == report()
    assert output.stat().st_mode & 0o777 == 0o600


def test_cli_never_overwrites_result(tmp_path):
    output = tmp_path / "result.json"
    output.write_bytes(b"existing evidence")
    process, output = cli(tmp_path)
    assert process.returncode != 0
    assert output.read_bytes() == b"existing evidence"


def test_cli_hash_failure_leaves_no_result(tmp_path):
    process, output = cli(tmp_path, digest="0" * 64)
    assert process.returncode != 0
    assert not output.exists()


def test_cli_named_pipe_refuses_without_waiting_for_writer(tmp_path):
    fifo = tmp_path / "input.fifo"
    os.mkfifo(fifo, 0o600)
    process, output = cli(tmp_path, input_path=fifo, timeout=2)
    assert process.returncode != 0
    assert not output.exists()


def test_cli_symlink_input_refuses(tmp_path):
    source = tmp_path / "generated.csv"
    source.write_bytes(CSV)
    link = tmp_path / "input-link.csv"
    link.symlink_to(source)
    process, output = cli(tmp_path, input_path=link)
    assert process.returncode != 0
    assert not output.exists()
