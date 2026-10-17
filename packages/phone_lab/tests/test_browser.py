from __future__ import annotations

import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import sync_playwright

from phone_lab.benchmark import TASKS, Benchmark
from phone_lab.dataset import audit, generate
from phone_lab.web import create_app

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


@pytest.fixture
def engine():
    if not Path(CHROME).exists():
        pytest.skip("actual local Chrome executable unavailable")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=CHROME)
        yield browser
        browser.close()


@pytest.fixture
def served(tmp_path):
    lab = Benchmark(tmp_path / "lab")
    app = create_app(lab, "operator-0123456789", "evaluator-0123456789")
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(32)
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("owned server did not start")
        time.sleep(0.01)
    yield lab, f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)
    assert not thread.is_alive()


@pytest.mark.parametrize("task", TASKS)
def test_actual_browser_contacts_and_outcomes(engine, served, task):
    lab, base = served
    s = lab.create("browser-owned", 73, 390, 700, task)
    context = engine.new_context(viewport={"width": 390, "height": 700})
    p = context.new_page()
    errors = []
    p.on("pageerror", lambda e: errors.append(str(e)))
    try:
        p.goto(f"{base}/s/{s.id}")
        if task == "drag":
            grip = p.locator(".handle").bounding_box()
            goal = p.locator(".destination").bounding_box()
            p.mouse.move(grip["x"] + grip["width"] / 2, grip["y"] + grip["height"] / 2)
            p.mouse.down()
            p.mouse.move(goal["x"] + goal["width"] / 2, goal["y"] + goal["height"] / 2, steps=6)
            p.mouse.up()
        elif task == "entry":
            p.get_by_role("textbox", name="Value").click()
            p.get_by_role("textbox", name="Value").fill(s.expected_value)
            p.get_by_role("button", name="Check", exact=True).click()
        elif task == "menu":
            p.get_by_role("button", name="Menu", exact=True).click()
            p.get_by_role("button", name="Orange", exact=True).click()
        elif task == "overlay":
            p.get_by_role("button", name="Dismiss Overlay", exact=True).click()
            p.get_by_role("button", name="Continue", exact=True).click()
        elif task == "scroll":
            p.locator(".list").hover()
            p.mouse.wheel(0, 250)
            p.get_by_role("button", name="Finish", exact=True).click()
        else:
            p.get_by_role("button", name="Continue", exact=True).click()
        p.locator("#result").filter(has_text="Complete").wait_for(timeout=5000)
        assert lab.outcome(s.id)["complete"]
        assert lab.outcome(s.id)["wrong_actions"] == 0
        assert not errors and lab.get(s.id).events
        assert all("success" not in e and "cohort" not in e for e in lab.get(s.id).events)
    finally:
        context.close()


@pytest.mark.skipif(not Path(CHROME).exists(), reason="actual Chrome unavailable")
def test_browser_rendered_labels_determinism_and_group_audit(tmp_path):
    first = generate(tmp_path / "first", [0, 1, 2], executable=CHROME)
    second = generate(tmp_path / "second", [0, 1, 2], executable=CHROME)
    assert len(first["rows"]) == 27
    assert [r["sha256"] for r in first["rows"]] == [r["sha256"] for r in second["rows"]]
    result = audit(first, tmp_path / "first")
    assert not result["errors"]
    # Near-similarity is retained as an explicit failed acceptance gate, never silently ignored.
    assert result["accepted"] == (not result["near_duplicates"])
    for row in first["rows"]:
        if row["task"] == "entry":
            assert next(label for label in row["labels"] if label["role"] == "field")["text"] == ""
        assert row["source"] == "generated-browser"
    b = first["rows"][-1]
    b["font_group"] = first["rows"][0]["font_group"]
    assert any("group crosses split" in e for e in audit(first, tmp_path / "first")["errors"])


@pytest.mark.skipif(not Path(CHROME).exists(), reason="actual Chrome unavailable")
def test_hash_mutation_and_dataset_destination_refused(tmp_path):
    m = generate(tmp_path / "dataset", [0, 1, 2], executable=CHROME)
    path = tmp_path / "dataset" / m["rows"][0]["image"]
    with path.open("ab") as f:
        f.write(b"changed")
    assert any("image hash" in e for e in audit(m, tmp_path / "dataset")["errors"])
    with pytest.raises(ValueError, match="already exists"):
        generate(tmp_path / "dataset", [0], executable=CHROME)


@pytest.mark.parametrize("task", TASKS)
def test_actual_keyboard_accessibility_paths(engine, served, task):
    lab, base = served
    s = lab.create("keyboard-generated", 73, 390, 700, task)
    context = engine.new_context(viewport={"width": 390, "height": 700})
    p = context.new_page()
    try:
        p.goto(f"{base}/s/{s.id}")
        p.keyboard.press("Tab")
        if task == "drag":
            p.keyboard.press("Enter")
            p.keyboard.press("Tab")
            p.keyboard.press("Enter")
        elif task == "entry":
            p.keyboard.insert_text(s.expected_value)
            p.keyboard.press("Tab")
            p.keyboard.press("Enter")
        elif task in {"menu", "overlay", "scroll"}:
            if task == "scroll":
                p.keyboard.press("PageDown")
            else:
                p.keyboard.press("Enter")
            p.wait_for_function("document.querySelector('#marker').dataset.frame.endsWith(':2')")
            p.keyboard.press("Tab")
            p.keyboard.press("Enter")
        else:
            p.keyboard.press("Enter")
        p.wait_for_function("document.querySelector('#result').textContent==='Complete'")
        assert lab.outcome(s.id)["complete"]
        assert lab.get(s.id).wrong_actions == 0
        assert p.locator("#error").inner_text() == ""
    finally:
        context.close()


@pytest.mark.skipif(not Path(CHROME).exists(), reason="actual Chrome unavailable")
def test_normalized_label_tampering_refused(tmp_path):
    m = generate(tmp_path / "label-audit", [0, 1, 2], executable=CHROME)
    row = m["rows"][0]
    (tmp_path / "label-audit" / row["yolo_label"]).write_text("0 0 0 1 1\n")
    assert any("YOLO label hash" in error for error in audit(m, tmp_path / "label-audit")["errors"])
