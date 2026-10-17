"""Matched red trials, blind blue scoring and a read-only local scoreboard."""

from __future__ import annotations

import json
import random
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .benchmark import TASKS, Refusal, finite, identifier
from .blue import score_contacts
from .workflow import read_runs


def motion_settings(profile, seed):
    if not isinstance(profile, str) or profile not in {"fixed", "varied"}:
        raise Refusal("declared motion profile required")
    if type(seed) is not int or not 0 <= seed <= 1_000_000:
        raise Refusal("motion seed bounds")
    if profile == "fixed":
        return {"tap_delay_ms": 0, "drag_steps": 6, "drag_duration_ms": 0}
    rng = random.Random(seed)
    return {
        "tap_delay_ms": rng.randint(60, 160),
        "drag_steps": rng.randint(6, 16),
        "drag_duration_ms": rng.randint(160, 400),
    }


def combine_round(red, packets, *, round_number):
    """Finish all blind scores before reading any independent red outcome."""
    if type(round_number) is not int or not 1 <= round_number <= 20:
        raise Refusal("round bounds")
    if not isinstance(packets, list) or len(packets) != len(TASKS):
        raise Refusal("one provider packet per task required")
    blue = {}
    for packet in packets:
        score = score_contacts(packet)
        sid = score["run_id"]
        if sid in blue:
            raise Refusal("duplicate provider session")
        blue[sid] = score
    if not isinstance(red, dict):
        raise Refusal("red result required")
    profile, seed = red.get("motion_profile"), red.get("seed_offset")
    motion_settings(profile, seed)
    results = red.get("results")
    if not isinstance(results, list) or len(results) != len(TASKS):
        raise Refusal("one outcome per task required")
    sessions, tasks, seen = [], set(), set()
    for result in results:
        if not isinstance(result, dict) or result.get("task") not in TASKS:
            raise Refusal("task identity")
        task = result["task"]
        outcome = result.get("outcome")
        if not isinstance(outcome, dict):
            raise Refusal("independent outcome required")
        sid = identifier(outcome.get("session"))
        if task in tasks or sid in seen or sid not in blue:
            raise Refusal("outcome/provider identity mismatch")
        tasks.add(task)
        seen.add(sid)
        complete, wrong = outcome.get("complete"), outcome.get("wrong_actions")
        if type(complete) is not bool or type(wrong) is not int or not 0 <= wrong <= 5000:
            raise Refusal("outcome bounds")
        sessions.append(
            {
                "task": task,
                "session": sid,
                "complete": complete,
                "wrong_actions": wrong,
                "refused": result.get("failure") is not None,
                "blue": blue[sid],
                "status": ("completed_flagged" if blue[sid]["flags"] else "completed_unflagged")
                if complete
                else "incomplete",
            }
        )
    if seen != set(blue):
        raise Refusal("unmatched provider packet")
    return {
        "schema": "owned-battle-round/1",
        "run_id": f"round-{round_number}",
        "round": round_number,
        "motion_profile": profile,
        "seed_offset": seed,
        "red": {
            "completed": sum(s["complete"] for s in sessions),
            "tasks": len(TASKS),
            "wrong_actions": sum(s["wrong_actions"] for s in sessions),
            "refused": sum(s["refused"] for s in sessions),
        },
        "blue": {
            "flagged_sessions": sum(bool(s["blue"]["flags"]) for s in sessions),
            "human_validation": "pending consented controls",
            "sanctions": False,
        },
        "sessions": sessions,
        "physical_gantry_verified": False,
        "contacts": "generated owned-browser stand-ins",
    }


def dashboard_html(status=None):
    bootstrap = json.dumps(status or {"state": "waiting", "rounds": []}, allow_nan=False).replace(
        "<", "\\u003c"
    )
    return (
        """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gantry red / blue lab</title><style>
:root{color-scheme:dark;font:16px system-ui;background:#10151e;color:#e8edf5}
body{max-width:1100px;margin:auto;padding:32px}h1{font-size:32px}a{color:#a5c9ff}
.teams{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{padding:24px;border:1px solid #455065;border-radius:16px}
.red{border-top:4px solid #f28b96}.blue{border-top:4px solid #7fb8fb}.count{font-size:36px;font-weight:700}
table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:12px;border-bottom:1px solid #384252}
.muted{color:#b7c1d0}#state{padding:10px 0} @media(max-width:600px){body{padding:16px}.teams{grid-template-columns:1fr}}
</style><h1>Gantry red / blue lab</h1><p class="muted">Owned mobile tasks · frozen vision model · independent contact scoring</p>
<div class="teams"><section class="card red"><h2>Red team</h2><div class="count" id="red">0 / 0</div><p>Tasks completed</p></section>
<section class="card blue"><h2>Blue team</h2><div class="count" id="blue">0</div><p>Sessions with declared contact patterns</p></section></div>
<p id="state"></p><p class="muted">Generated browser contacts. Physical gantry and consented human controls pending. Patterns are hypotheses; no sanctions.</p>
<table><thead><tr><th>Round / profile</th><th>Task</th><th>Outcome</th><th>Blue patterns</th></tr></thead><tbody id="rows"></tbody></table>
<script id="bootstrap" type="application/json">"""
        + bootstrap
        + """</script><script>
function show(s){let completed=0,total=0,flagged=0;const rows=document.getElementById('rows');rows.replaceChildren();
for(const r of s.rounds||[]){completed+=r.red.completed;total+=r.red.tasks;flagged+=r.blue.flagged_sessions;
for(const t of r.sessions){const row=document.createElement('tr');for(const value of [r.round+' / '+r.motion_profile,t.task,t.status,t.blue.flags.join(', ')||'none']){
const cell=document.createElement('td');cell.textContent=value;row.append(cell)}rows.append(row)}}
document.getElementById('red').textContent=completed+' / '+total;document.getElementById('blue').textContent=flagged;
document.getElementById('state').textContent=s.state||'waiting';}
show(JSON.parse(document.getElementById('bootstrap').textContent));
if(location.protocol!=='file:')setInterval(async()=>{try{const r=await fetch('/api/status');if(r.ok)show(await r.json());else document.getElementById('state').textContent='Evidence unavailable; retained for inspection'}catch{}},1000);
</script></html>"""
    )


def battle_status(root):
    path = Path(root) / "battle_runs.jsonl"
    if not path.exists():
        return {"state": "waiting", "rounds": []}
    if path.is_symlink() or path.stat().st_size > 20_000_000:
        raise Refusal("battle evidence budget")
    rounds = read_runs(path)
    if len(rounds) > 20 or any(
        not isinstance(r, dict) or r.get("schema") != "owned-battle-round/1" for r in rounds
    ):
        raise Refusal("battle evidence schema")
    # Reconstruct from the explicitly narrow saved result, refusing arbitrary fields.
    checked = []
    for row in rounds:
        sessions = row.get("sessions")
        if not isinstance(sessions, list) or len(sessions) != len(TASKS):
            raise Refusal("battle sessions")
        # The writer stores scores, never raw provider inputs or evaluator labels.
        if set(row) != {
            "schema",
            "run_id",
            "round",
            "motion_profile",
            "seed_offset",
            "red",
            "blue",
            "sessions",
            "physical_gantry_verified",
            "contacts",
        }:
            raise Refusal("unexpected battle evidence")
        _saved_round(row)
        if any(prior["round"] == row["round"] for prior in checked):
            raise Refusal("duplicate saved round")
        checked.append(row)
    return {"state": "recorded rounds (hardware and human validation pending)", "rounds": checked}


def _keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected.split()):
        raise Refusal("unexpected saved fields")


def _saved_round(row):
    number = row["round"]
    if type(number) is not int or not 1 <= number <= 20 or row["run_id"] != f"round-{number}":
        raise Refusal("saved round identity")
    motion_settings(row["motion_profile"], row["seed_offset"])
    if (
        row["physical_gantry_verified"] is not False
        or row["contacts"] != "generated owned-browser stand-ins"
    ):
        raise Refusal("saved evidence scope")
    tasks, ids = set(), set()
    for session in row["sessions"]:
        _keys(session, "task session complete wrong_actions refused blue status")
        sid = identifier(session["session"])
        task = session["task"]
        if not isinstance(task, str) or task not in TASKS or task in tasks or sid in ids:
            raise Refusal("saved task/session identity")
        tasks.add(task)
        ids.add(sid)
        if (
            type(session["complete"]) is not bool
            or type(session["refused"]) is not bool
            or type(session["wrong_actions"]) is not int
        ):
            raise Refusal("saved outcome types")
        finite(session["wrong_actions"], 0, 5000, "wrong actions")
        score = session["blue"]
        _keys(
            score,
            "schema run_id features flags robot_probability human_validation sanctions rule_version",
        )
        if (
            score["schema"] != "blue-contact-score/1"
            or score["run_id"] != sid
            or score["rule_version"] != "declared-contact-patterns/1"
        ):
            raise Refusal("saved blue identity")
        if (
            score["robot_probability"] is not None
            or score["sanctions"] is not False
            or score["human_validation"] != "pending consented controls"
        ):
            raise Refusal("saved validation scope")
        flags = score["flags"]
        if (
            not isinstance(flags, list)
            or len(flags) > 3
            or any(
                not isinstance(f, str)
                or f
                not in {"short_contact_dwell", "regular_contact_dwell", "straight_contact_path"}
                for f in flags
            )
        ):
            raise Refusal("saved flags")
        features = score["features"]
        _keys(features, "contacts dwell_ms contact_paths cancelled_contacts incomplete_contacts")
        for key in ("contacts", "cancelled_contacts", "incomplete_contacts"):
            if type(features[key]) is not int or not 0 <= features[key] <= 5000:
                raise Refusal("saved contact counts")
        stats = features["dwell_ms"]
        _keys(stats, "count p50_ms p95_ms")
        if type(stats["count"]) is not int or stats["count"] != features["contacts"]:
            raise Refusal("saved dwell count")
        for key in ("p50_ms", "p95_ms"):
            if stats["count"]:
                finite(stats[key], 0, 1e15, "dwell")
            elif stats[key] is not None:
                raise Refusal("empty dwell statistics")
        paths = features["contact_paths"]
        if not isinstance(paths, list) or len(paths) != features["contacts"]:
            raise Refusal("saved contact paths")
        for path in paths:
            _keys(path, "length_px linearity moves")
            finite(path["length_px"], 0, 30_000_000, "contact length")
            finite(path["linearity"], 0, 1.000000001, "linearity")
            if type(path["moves"]) is not int or not 0 <= path["moves"] <= 5000:
                raise Refusal("saved moves")
        expected = (
            ("completed_flagged" if flags else "completed_unflagged")
            if session["complete"]
            else "incomplete"
        )
        if session["status"] != expected:
            raise Refusal("saved outcome status")
    expected_red = {
        "completed": sum(s["complete"] for s in row["sessions"]),
        "tasks": len(TASKS),
        "wrong_actions": sum(s["wrong_actions"] for s in row["sessions"]),
        "refused": sum(s["refused"] for s in row["sessions"]),
    }
    expected_blue = {
        "flagged_sessions": sum(bool(s["blue"]["flags"]) for s in row["sessions"]),
        "human_validation": "pending consented controls",
        "sanctions": False,
    }
    if row["red"] != expected_red or row["blue"] != expected_blue:
        raise Refusal("saved score totals")


def create_dashboard(root):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/", response_class=HTMLResponse)
    def home():
        return dashboard_html()

    @app.get("/api/status")
    def status():
        try:
            return battle_status(root)
        except (Refusal, OSError, TypeError, KeyError):
            raise HTTPException(503, "Battle evidence unavailable; original retained") from None

    return app
