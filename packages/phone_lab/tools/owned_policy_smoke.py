"""Pixel/OCR policy against the generated owned site, with fake motor evidence only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import uvicorn
from PIL import Image
from playwright.sync_api import sync_playwright

from phone_lab.battle import motion_settings
from phone_lab.benchmark import TASKS, Benchmark, Box, Refusal
from phone_lab.blue import make_blue_packet
from phone_lab.control import Calibration, FakeSerial, Frame, Intent, VirtualController
from phone_lab.metrics import latency
from phone_lab.perception import ROLES, choose_target, unletterbox_box
from phone_lab.web import create_app
from phone_lab.workflow import append_run, color_candidates, save_capture, website_observations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--chrome", required=True)
    parser.add_argument("--detector", type=Path)
    parser.add_argument("--detector-sha256")
    parser.add_argument("--motion-profile", choices=("fixed", "varied"), default="fixed")
    parser.add_argument("--seed-offset", type=int, default=0)
    args = parser.parse_args()
    motion_settings(args.motion_profile, args.seed_offset)
    detector_hash = None
    if args.detector and not args.detector_sha256:
        raise Refusal("--detector requires --detector-sha256")
    if args.detector_sha256 and not args.detector:
        raise Refusal("--detector-sha256 requires --detector")
    if args.detector:
        if not re.fullmatch(r"[0-9a-f]{64}", args.detector_sha256):
            raise Refusal("invalid detector checkpoint hash")
        if not args.detector.is_file() or args.detector.stat().st_size > 64 * 1024 * 1024:
            raise Refusal("bounded local detector checkpoint required")
        detector_hash = hashlib.sha256(args.detector.read_bytes()).hexdigest()
        if detector_hash != args.detector_sha256:
            raise Refusal("detector checkpoint hash mismatch")
    root = args.output.resolve()
    ocr = args.ocr.resolve()
    if root.exists():
        raise Refusal("new immutable workflow output required")
    root.mkdir(mode=0o700, parents=True)
    start = datetime.now(ZoneInfo("America/Toronto")).isoformat()
    warmup_image = root / "generated-warmup.png"
    Image.new("RGB", (390, 700), "white").save(warmup_image)
    warmup = {
        "input": "generated blank PNG",
        "before_frame_capture": True,
        "OCR_binary_sha256": hashlib.sha256(ocr.read_bytes()).hexdigest(),
    }
    t0 = time.perf_counter()
    subprocess.run([str(ocr), str(warmup_image)], capture_output=True, check=True, timeout=20)
    warmup["OCR_ms"] = (time.perf_counter() - t0) * 1000
    model = None
    detector = None
    if args.detector:
        for key, name in (
            ("YOLO_CONFIG_DIR", "yolo-config"),
            ("TORCH_HOME", "torch-cache"),
            ("MPLCONFIGDIR", "matplotlib-cache"),
        ):
            path = root / name
            path.mkdir(mode=0o700)
            os.environ[key] = str(path)
        t0 = time.perf_counter()
        import cv2
        import torch
        import ultralytics
        from ultralytics import YOLO
        from ultralytics.data.augment import LetterBox

        torch.set_num_threads(2)
        model = YOLO(str(args.detector.resolve()))
        if set(model.names.values()) != ROLES or len(model.names) != len(ROLES):
            raise Refusal("trained detector role mapping mismatch")
        square = LetterBox((640, 640), auto=False)(image=cv2.imread(str(warmup_image)))
        model.predict(square, device="cpu", imgsz=640, max_det=32, verbose=False)
        # The backend resets Torch's pool during initialization; bound the action pool afterward.
        torch.set_num_threads(2)
        warmup["detector_load_and_first_inference_ms"] = (time.perf_counter() - t0) * 1000
        detector = {
            "sha256": detector_hash,
            "device": "cpu",
            "FP32": True,
            "torch": torch.__version__,
            "ultralytics": ultralytics.__version__,
            "roles": model.names,
            "minimum_candidate_score": 0.9,
            "input_size": [640, 640],
            "preprocess": "explicit fixed-square LetterBox; exact rounded padding restored",
        }
        backend = model.predictor.model
        if backend.onnx:
            dtype = backend.session.get_inputs()[0].type
            if dtype != "tensor(float)":
                raise Refusal("FP32 ONNX input required")
            detector["dtype"] = dtype
            detector["runtime"] = "onnxruntime"
            detector["runtime_intra_op_threads"] = (
                backend.session.get_session_options().intra_op_num_threads
            )
        else:
            dtype = next(model.model.parameters()).dtype
            if dtype != torch.float32:
                raise Refusal("FP32 PyTorch checkpoint required")
            detector["dtype"] = str(dtype)
            detector["runtime"] = "pytorch"
            detector["runtime_intra_op_threads"] = torch.get_num_threads()
    (root / "startup.json").write_text(
        json.dumps(
            {
                "start_Toronto": start,
                "warmup": warmup,
                "detector": detector,
            },
            indent=2,
        )
        + "\n"
    )
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
    perception_timings = []
    browser_version = None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                executable_path=args.chrome, headless=True, args=["--disable-gpu"]
            )
            browser_version = browser.version
            for task_index, task in enumerate(TASKS):
                s = lab.create("generated-policy", 73 + args.seed_offset, 390, 700, task)
                motion = motion_settings(args.motion_profile, args.seed_offset + task_index)
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
                    page.evaluate("document.fonts.ready")
                    page.evaluate(
                        "new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))"
                    )
                    marker = page.locator("#marker").inner_text()
                    frame = Frame(s.device, s.id, marker, time.monotonic(), 390, 700)
                    folder = root / "captures" / task / f"{capture_index:03d}"
                    scratch = root / f"capture-{task}-{capture_index}.png"
                    attempts = root / "capture-attempts" / task / f"{capture_index:03d}"
                    attempts.mkdir(mode=0o700, parents=True)
                    capture_index += 1
                    previous = None
                    for attempt in range(4):
                        current = page.screenshot()
                        (attempts / f"{attempt}.png").write_bytes(current)
                        if current == previous:
                            scratch.write_bytes(current)
                            break
                        previous = current
                    else:
                        raise Refusal("unstable capture; PNG attempts preserved")
                    if page.locator("#marker").inner_text() != marker:
                        raise Refusal("frame changed during capture")
                    save_capture(folder, scratch, frame, permission="owned-generated-fixture")
                    t0 = time.perf_counter()
                    process = subprocess.run(
                        [str(ocr), str(folder / "frame.png")],
                        capture_output=True,
                        text=True,
                        timeout=20,
                        check=True,
                    )
                    ocr_ms = (time.perf_counter() - t0) * 1000
                    texts = json.loads(process.stdout)
                    predictions = None
                    detector_ms = None
                    if model is not None:
                        t0 = time.perf_counter()
                        square = LetterBox((640, 640), auto=False)(
                            image=cv2.imread(str(folder / "frame.png"))
                        )
                        output = model.predict(
                            square,
                            device="cpu",
                            imgsz=640,
                            conf=0.1,
                            max_det=32,
                            verbose=False,
                        )[0]
                        detector_ms = (time.perf_counter() - t0) * 1000
                        predictions = []
                        for box in output.boxes:
                            predictions.append(
                                {
                                    "role": model.names[int(box.cls[0])],
                                    "confidence": float(box.conf[0]),
                                    "box": unletterbox_box(
                                        [float(v) for v in box.xyxy[0]], viewport=(390, 700)
                                    ),
                                }
                            )
                    timing = {
                        "task": task,
                        "capture_index": capture_index - 1,
                        "OCR_ms": ocr_ms,
                        "detector_ms": detector_ms,
                        "frame_age_after_perception_ms": (time.monotonic() - frame.captured_at)
                        * 1000,
                    }
                    perception_timings.append(timing)
                    with (folder / "perception.json").open("x") as evidence:
                        json.dump(
                            {
                                "frame": marker,
                                "OCR": texts,
                                "detections": predictions,
                                "timing": timing,
                            },
                            evidence,
                        )
                    return frame, folder / "frame.png", texts, predictions

                def candidate(name, image, texts, predictions, role="button"):
                    if predictions is not None:
                        return choose_target(
                            predictions,
                            texts,
                            role=role,
                            name=name if role == "button" else None,
                            viewport=(390, 700),
                        )
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
                            matches.append(
                                {
                                    "point": (b["x"] + b["width"] / 2, b["y"] + b["height"] / 2),
                                    "confidence": min(t["confidence"] for t in inside),
                                }
                            )
                    if not matches:
                        # OCR-only fallback is an explicit development candidate; evaluator decides real hit.
                        matches = [
                            {
                                "point": (
                                    t["box"]["x"] + t["box"]["width"] / 2,
                                    t["box"]["y"] + t["box"]["height"] / 2,
                                ),
                                "confidence": t["confidence"],
                            }
                            for t in texts
                            if t["text"] == name and t["confidence"] >= 0.9
                        ]
                    if len(matches) != 1:
                        raise Refusal("ambiguous/missing pixel-OCR target")
                    return matches[0]

                def motor(frame, points, kind="tap", confidence=0.95):
                    nonlocal policy_steps
                    if page.locator("#marker").inner_text() != frame.marker:
                        raise Refusal("visible frame changed before action")
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
                        confidence,
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
                    frame, image, texts, predictions = capture()
                    selected = candidate(name, image, texts, predictions)
                    point = selected["point"]
                    motor(frame, [point], confidence=selected["confidence"])
                    page.mouse.click(*point, delay=motion["tap_delay_ms"])
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
                        frame, image, texts, predictions = capture()
                        grip_target = candidate("Grip", image, texts, predictions, "handle")
                        goal_target = candidate("Goal", image, texts, predictions, "destination")
                        grip, goal = grip_target["point"], goal_target["point"]
                        motor(
                            frame,
                            [grip, goal],
                            "drag",
                            min(grip_target["confidence"], goal_target["confidence"]),
                        )
                        page.mouse.move(*grip)
                        page.mouse.down()
                        for step in range(1, motion["drag_steps"] + 1):
                            ratio = step / motion["drag_steps"]
                            page.mouse.move(
                                grip[0] + (goal[0] - grip[0]) * ratio,
                                grip[1] + (goal[1] - grip[1]) * ratio,
                            )
                            if motion["drag_duration_ms"]:
                                page.wait_for_timeout(
                                    motion["drag_duration_ms"] / motion["drag_steps"]
                                )
                        page.mouse.up()
                        wait_change(frame.marker)
                    elif task == "entry":
                        frame, image, texts, predictions = capture()
                        fields = [
                            p["box"]
                            for p in color_candidates(image)
                            if p["box"]["width"] > 300 and p["box"]["height"] < 80
                        ]
                        score = 0.95
                        if predictions is not None:
                            selected = candidate(None, image, texts, predictions, "field")
                            point, score = selected["point"], selected["confidence"]
                        else:
                            if len(fields) != 1:
                                raise Refusal("missing/ambiguous pixel field")
                            b = fields[0]
                            point = (b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
                        motor(frame, [point], confidence=score)
                        page.mouse.click(*point, delay=motion["tap_delay_ms"])
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
                        frame, image, texts, predictions = capture()
                        lists = [
                            p["box"]
                            for p in color_candidates(image)
                            if p["box"]["width"] > 300 and p["box"]["height"] >= 100
                        ]
                        score = 0.95
                        if predictions is not None:
                            selected = candidate(None, image, texts, predictions, "list")
                            point, score = selected["point"], selected["confidence"]
                        else:
                            if len(lists) != 1:
                                raise Refusal("missing/ambiguous pixel list")
                            b = lists[0]
                            point = (b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
                        motor(
                            frame,
                            [(point[0], point[1] + 35), (point[0], point[1] - 35)],
                            "drag",
                            score,
                        )
                        page.mouse.move(*point)
                        page.mouse.wheel(0, 250)
                        wait_change(frame.marker)
                        tap("Finish")
                except Exception as error:
                    controller.stop("policy refusal/cancel")
                    failure = {"type": type(error).__name__, "message": str(error)}
                observed = lab.get(s.id)
                append_run(
                    root / "blue_inputs.jsonl",
                    make_blue_packet(s.id, (s.width, s.height), observed.events),
                )
                # Independent evaluator reads ground truth only after provider export.
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
        "schema": "owned-policy-smoke/2",
        "start_Toronto": start,
        "end_Toronto": datetime.now(ZoneInfo("America/Toronto")).isoformat(),
        "results": results,
        "motion_profile": args.motion_profile,
        "seed_offset": args.seed_offset,
        "motion_scope": "declared generated browser contacts; fake motor endpoints only",
        "blue_inputs_sha256": hashlib.sha256((root / "blue_inputs.jsonl").read_bytes()).hexdigest(),
        "policy_inputs": "pixels, OCR, requested task, visible frame identity only",
        "labels_in_policy": False,
        "warmup": warmup,
        "detector": detector,
        "final_Torch_threads": torch.get_num_threads() if model is not None else None,
        "capture_recipe": 3,
        "Python": sys.version.split()[0],
        "Chrome": browser_version,
        "perception_timings": perception_timings,
        "perception_latency": {
            "OCR": latency([t["OCR_ms"] for t in perception_timings]),
            "detector": latency(
                [t["detector_ms"] for t in perception_timings if t["detector_ms"] is not None]
            ),
            "frame_age": latency([t["frame_age_after_perception_ms"] for t in perception_timings]),
        },
        "actual_owned_browser_observations": True,
        "motors": "fake serial only; numeric keyboard insertion and wheel are generated stand-ins",
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
