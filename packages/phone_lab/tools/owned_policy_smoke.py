"""Pixel/OCR policy against the generated owned site, with fake motor evidence only."""

from __future__ import annotations

import argparse
import json
import re
import secrets
import socket
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import uvicorn
from playwright.sync_api import sync_playwright

from phone_lab.benchmark import TASKS, Benchmark, Box, Refusal
from phone_lab.control import Calibration, FakeSerial, Frame, Intent, VirtualController
from phone_lab.web import create_app
from phone_lab.workflow import append_run, color_candidates, save_capture, website_observations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--chrome", required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    ocr = args.ocr.resolve()
    if root.exists():
        raise Refusal("new immutable workflow output required")
    root.mkdir(mode=0o700, parents=True)
    lab = Benchmark(root / "runtime")
    app = create_app(lab, secrets.token_hex(24), secrets.token_hex(24))
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(32)
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started:
        if time.monotonic() > deadline:
            raise Refusal("owned server startup timeout")
        time.sleep(0.01)
    results = []
    start = datetime.now(ZoneInfo("America/Toronto")).isoformat()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=args.chrome, headless=True)
            for task in TASKS:
                s = lab.create("generated-policy", 73, 390, 700, task)
                page = browser.new_page(viewport={"width": 390, "height": 700})
                page.goto(f"http://127.0.0.1:{sock.getsockname()[1]}/s/{s.id}")
                cal = Calibration.fit(
                    s.device,
                    (390, 700),
                    [[0, 0], [390, 0], [0, 700], [390, 700]],
                    [[0, 0], [39, 0], [0, 70], [39, 70]],
                    [[100, 200], [300, 600]],
                    [[10, 20], [30, 60]],
                    Box(0, 0, 39, 70),
                )
                controller = VirtualController(FakeSerial(), cal)
                controller.home()
                capture_index = 0
                policy_steps = 0

                def capture():
                    nonlocal capture_index
                    # The capture harness supplies visible identity only. Target DOM/labels never enter the policy.
                    marker = page.locator("#marker").inner_text()
                    frame = Frame(s.device, s.id, marker, time.monotonic(), 390, 700)
                    folder = root / "captures" / task / f"{capture_index:03d}"
                    scratch = root / f"capture-{task}-{capture_index}.png"
                    capture_index += 1
                    page.screenshot(path=str(scratch))
                    save_capture(folder, scratch, frame, permission="owned-generated-fixture")
                    process = subprocess.run(
                        [str(ocr), str(folder / "frame.png")],
                        capture_output=True,
                        text=True,
                        timeout=20,
                        check=True,
                    )
                    return frame, folder / "frame.png", json.loads(process.stdout)

                def candidate(name, image, texts):
                    matches = []
                    for box in color_candidates(image):
                        b = box["box"]
                        inside = []
                        for text in texts:
                            t = text["box"]
                            x = t["x"] + t["width"] / 2
                            y = t["y"] + t["height"] / 2
                            if (
                                b["x"] <= x <= b["x"] + b["width"]
                                and b["y"] <= y <= b["y"] + b["height"]
                            ):
                                inside.append(text)
                        joined = " ".join(
                            t["text"]
                            for t in sorted(inside, key=lambda t: (t["box"]["y"], t["box"]["x"]))
                        )
                        if (
                            joined == name
                            and inside
                            and min(t["confidence"] for t in inside) >= 0.9
                        ):
                            matches.append((b["x"] + b["width"] / 2, b["y"] + b["height"] / 2))
                    if not matches:
                        # OCR-only fallback is an explicit development candidate; evaluator decides real hit.
                        matches = [
                            (
                                t["box"]["x"] + t["box"]["width"] / 2,
                                t["box"]["y"] + t["box"]["height"] / 2,
                            )
                            for t in texts
                            if t["text"] == name and t["confidence"] >= 0.9
                        ]
                    if len(matches) != 1:
                        raise Refusal("ambiguous/missing pixel-OCR target")
                    return matches[0]

                def motor(frame, points, kind="tap"):
                    nonlocal policy_steps
                    now = time.monotonic()
                    token = secrets.token_hex(16)
                    controller.arm(frame, token, now)
                    intent = Intent(
                        kind,
                        frame.device,
                        frame.session,
                        frame.marker,
                        cal.digest,
                        tuple(points),
                        0.95,
                        now + 1,
                        token,
                    )
                    record = controller.execute(intent, frame, now)
                    record["capture_index"] = capture_index - 1
                    append_run(root / "runs.jsonl", record)
                    policy_steps += 1

                def wait_change(marker):
                    page.wait_for_function(
                        'prior=>document.querySelector("#marker").innerText!==prior',
                        arg=marker,
                        timeout=3000,
                    )

                def tap(name):
                    frame, image, texts = capture()
                    point = candidate(name, image, texts)
                    motor(frame, [point])
                    page.mouse.click(*point)
                    wait_change(frame.marker)

                failure = None
                try:
                    if task == "tap":
                        tap("Continue")
                    elif task == "menu":
                        tap("Menu")
                        tap("Orange")
                    elif task == "overlay":
                        tap("Dismiss Overlay")
                        tap("Continue")
                    elif task == "drag":
                        frame, image, texts = capture()
                        grip = candidate("Grip", image, texts)
                        goal = candidate("Goal", image, texts)
                        motor(frame, [grip, goal], "drag")
                        page.mouse.move(*grip)
                        page.mouse.down()
                        page.mouse.move(*goal, steps=6)
                        page.mouse.up()
                        wait_change(frame.marker)
                    elif task == "entry":
                        frame, image, texts = capture()
                        fields = [
                            p["box"]
                            for p in color_candidates(image)
                            if p["box"]["width"] > 300 and p["box"]["height"] < 80
                        ]
                        if len(fields) != 1:
                            raise Refusal("missing/ambiguous pixel field")
                        b = fields[0]
                        point = (b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
                        motor(frame, [point])
                        page.mouse.click(*point)
                        wait_change(frame.marker)
                        instructions = " ".join(t["text"] for t in texts)
                        digits = re.search(r"Enter (\d+) then", instructions)
                        if not digits:
                            raise Refusal("visible numeric instruction unreadable")
                        prior = page.locator("#marker").inner_text()
                        page.keyboard.insert_text(digits.group(1))
                        wait_change(prior)
                        tap("Check")
                    elif task == "scroll":
                        frame, image, texts = capture()
                        lists = [
                            p["box"]
                            for p in color_candidates(image)
                            if p["box"]["width"] > 300 and p["box"]["height"] >= 100
                        ]
                        if len(lists) != 1:
                            raise Refusal("missing/ambiguous pixel list")
                        b = lists[0]
                        point = (b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
                        motor(frame, [(point[0], point[1] + 35), (point[0], point[1] - 35)], "drag")
                        page.mouse.move(*point)
                        page.mouse.wheel(0, 250)
                        wait_change(frame.marker)
                        tap("Finish")
                except Exception as error:
                    controller.stop("policy refusal/cancel")
                    failure = {"type": type(error).__name__, "message": str(error)}
                # Independent evaluator reads ground truth only after policy actions.
                results.append(
                    {
                        "task": task,
                        "outcome": lab.outcome(s.id),
                        "policy_steps": policy_steps,
                        "failure": failure,
                        "physical_acceptance": False,
                    }
                )
                page.close()
            browser.close()
    finally:
        server.should_exit = True
        thread.join(5)
        sock.close()
    report = {
        "schema": "owned-policy-smoke/1",
        "start_Toronto": start,
        "end_Toronto": datetime.now(ZoneInfo("America/Toronto")).isoformat(),
        "results": results,
        "policy_inputs": "pixels, OCR, requested task, visible frame identity only",
        "labels_in_policy": False,
        "actual_owned_browser_observations": True,
        "motors": "fake serial only; wheel is a generated scroll stand-in",
        "real_phone_or_participant_study": False,
        "website_observations": website_observations(list(lab.sessions.values())),
    }
    (root / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "tasks": len(results),
                "completed": sum(r["outcome"]["complete"] for r in results),
                "failures": sum(r["failure"] is not None for r in results),
                "result": str(root / "result.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
