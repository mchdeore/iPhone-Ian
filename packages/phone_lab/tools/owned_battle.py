"""Run bounded matched-layout battles against the frozen owned vision policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from phone_lab.battle import battle_status, combine_round, dashboard_html
from phone_lab.benchmark import Refusal
from phone_lab.workflow import append_run, read_runs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--detector", type=Path, required=True)
    parser.add_argument("--detector-sha256", required=True)
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--chrome", required=True)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if not 1 <= args.rounds <= 20 or not 30 <= args.timeout <= 300:
        raise Refusal("battle round/timeout bounds")
    if not args.detector.is_file() or args.detector.stat().st_size > 64 * 1024 * 1024:
        raise Refusal("bounded frozen detector required")
    if hashlib.sha256(args.detector.read_bytes()).hexdigest() != args.detector_sha256:
        raise Refusal("detector hash mismatch")
    root = args.output.resolve()
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    frozen = {
        "schema": "owned-battle-design/1",
        "detector_sha256": args.detector_sha256,
        "profiles": ["fixed", "varied"],
        "rules": "declared-contact-patterns/1",
        "rounds": args.rounds,
        "layout_pairing": "same seed offset per fixed/varied pair",
        "physical_gantry_verified": False,
        "human_validation": "pending consented controls",
        "started_Toronto": datetime.now(ZoneInfo("America/Toronto")).isoformat(),
    }
    sources = [Path(__file__), Path(__file__).with_name("owned_policy_smoke.py")]
    sources += list((Path(__file__).parents[1] / "src/phone_lab").glob("*.py"))
    frozen["source_sha256"] = {
        str(p.relative_to(Path(__file__).parents[1])): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(sources)
    }
    (root / "design.json").write_text(json.dumps(frozen, indent=2) + "\n")
    worker = Path(__file__).with_name("owned_policy_smoke.py")
    for number in range(1, args.rounds + 1):
        profile = "fixed" if number % 2 else "varied"
        offset = ((number - 1) // 2) * 1000
        round_root = root / "rounds" / f"{number:02d}-{profile}"
        command = [
            sys.executable,
            str(worker),
            str(round_root),
            "--detector",
            str(args.detector),
            "--detector-sha256",
            args.detector_sha256,
            "--ocr",
            str(args.ocr),
            "--chrome",
            args.chrome,
            "--motion-profile",
            profile,
            "--seed-offset",
            str(offset),
        ]
        try:
            with (root / f"round-{number:02d}.log").open("xb") as log:
                result = subprocess.run(
                    command, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout, check=False
                )
            if result.returncode:
                raise Refusal("worker failed; partial evidence retained")
            red = json.loads((round_root / "result.json").read_text())
            packets = read_runs(round_root / "blue_inputs.jsonl")
            combined = combine_round(red, packets, round_number=number)
            combined["run_id"] = f"round-{number}"
            append_run(root / "battle_runs.jsonl", combined)
            (root / "dashboard.html").write_text(dashboard_html(battle_status(root)))
            print(
                json.dumps(
                    {
                        "round": number,
                        "profile": profile,
                        "red": combined["red"],
                        "blue": combined["blue"],
                        "completed_Toronto": datetime.now(ZoneInfo("America/Toronto")).isoformat(),
                    }
                ),
                flush=True,
            )
        except subprocess.TimeoutExpired:
            raise Refusal("worker timed out; partial evidence retained") from None
    frozen["finished_Toronto"] = datetime.now(ZoneInfo("America/Toronto")).isoformat()
    (root / "completion.json").write_text(json.dumps(frozen, indent=2) + "\n")
    # Worker framework caches remain under its owned output; no external platform actions.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
