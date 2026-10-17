import copy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from phone_lab.benchmark import Refusal
from phone_lab.catalog import build_catalog, create_dataset_app, dataset_spec, load_catalog

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def test_seed_and_tag_order_is_canonical_and_bounds_refuse():
    assert dataset_spec([2, 0, 1], ["pilot", "ui"]) == dataset_spec([0, 1, 2], ["ui", "pilot"])
    for seeds, tags in (
        ([True], []),
        ([-1], []),
        ([1, 1], []),
        ([1], ["../../private"]),
        ([1], ["a"] * 17),
    ):
        with pytest.raises(Refusal):
            dataset_spec(seeds, tags)


def test_actual_chrome_exports_stable_ids_borders_tags_and_bytes(tmp_path):
    if not Path(CHROME).exists():
        pytest.skip("actual local Chrome unavailable")
    first = build_catalog(tmp_path / "first", [0, 1, 2], tags=["pilot", "ui"], executable=CHROME)
    second = build_catalog(tmp_path / "second", [2, 0, 1], tags=["ui", "pilot"], executable=CHROME)
    assert first == second
    assert len(first["samples"]) == 27
    assert {s["split"] for s in first["samples"]} == {"train", "val", "test"}
    assert len({s["id"] for s in first["samples"]}) == 27
    for sample in first["samples"]:
        assert "pilot" in sample["tags"]
        assert sample["borders"]
        for border in sample["borders"]:
            assert 0 <= border["left"] < border["right"] <= 390
            assert 0 <= border["top"] < border["bottom"] <= 700
        for key in ("image", "yolo_label", "annotation"):
            assert (tmp_path / "first" / sample[key]).read_bytes() == (
                tmp_path / "second" / sample[key]
            ).read_bytes()
    assert load_catalog(tmp_path / "first") == first
    image = tmp_path / "first" / first["samples"][0]["image"]
    image.write_bytes(b"corrupted capture")
    with pytest.raises(Refusal):
        load_catalog(tmp_path / "first")


def test_dataset_app_limits_paths_and_exposes_no_actor_dispatch(tmp_path):
    client = TestClient(create_dataset_app(tmp_path, executable=CHROME))
    assert "Synthetic data" in client.get("/").text
    assert client.get("/api/datasets").json() == []
    assert client.get("/api/datasets/unknown").status_code == 404
    assert client.post("/api/dispatch", json={}).status_code == 404
    for payload in (
        {"seeds": [True]},
        {"seeds": [0], "tags": ["../../private"]},
        {"seeds": [0], "robot_label": "hidden"},
    ):
        assert client.post("/api/datasets", json=payload).status_code == 422


def test_catalog_paths_cannot_escape_even_with_plausible_schema(tmp_path):
    if not Path(CHROME).exists():
        pytest.skip("actual local Chrome unavailable")
    catalog = build_catalog(tmp_path / "data", [0], executable=CHROME)
    import json

    bad = copy.deepcopy(catalog)
    bad["samples"][0]["image"] = "../outside.png"
    (tmp_path / "data" / "catalog.json").write_text(json.dumps(bad))
    with pytest.raises(Refusal):
        load_catalog(tmp_path / "data")


def test_actual_web_app_generates_filters_tags_and_renders_measured_borders(tmp_path):
    if not Path(CHROME).exists():
        pytest.skip("actual local Chrome unavailable")
    import socket
    import threading
    import time

    import uvicorn
    from playwright.sync_api import sync_playwright

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    server = uvicorn.Server(
        uvicorn.Config(
            create_dataset_app(tmp_path, executable=CHROME), log_level="error", access_log=False
        )
    )
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 5
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, executable_path=CHROME)
            page = browser.new_page()
            origin = f"http://127.0.0.1:{sock.getsockname()[1]}"
            page.goto(origin)
            page.locator("#seeds").fill("0")
            page.get_by_role("button", name="Generate dataset").click()
            page.wait_for_function("document.querySelectorAll('.sample').length===9", timeout=30000)
            assert page.locator(".box").count() > 0
            assert "pilot" in page.locator(".sample").first.inner_text()
            image = page.locator(".frame img").first
            image.evaluate("img=>img.decode()")
            assert image.evaluate("img=>img.naturalWidth") == 390
            page.locator("#borders").uncheck()
            assert page.locator(".box").count() == 0
            page.locator("#task").select_option("drag")
            assert page.locator(".sample").count() == 1
            dataset_id = page.locator("#datasets").input_value()
            detail = page.request.get(f"{origin}/api/datasets/{dataset_id}").json()
            assert detail["spec"]["tags"] == ["pilot", "ui"]
            assert page.request.get(f"{origin}/files/{dataset_id}/catalog.json").status == 200
            assert page.request.get(f"{origin}/files/{dataset_id}/catalog.sha256").status == 404
            page.get_by_role("button", name="Generate dataset").click()
            page.wait_for_function("!document.querySelector('button').disabled", timeout=30000)
            assert len(list(tmp_path.iterdir())) == 1
            browser.close()
    finally:
        server.should_exit = True
        thread.join(5)
        sock.close()
