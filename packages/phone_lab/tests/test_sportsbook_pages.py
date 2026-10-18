from pathlib import Path

import pytest

from phone_lab.benchmark import Refusal
from phone_lab.sportsbook.fixtures import provider_snapshot
from phone_lab.sportsbook.pages import provider_page

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def test_actual_iphone_provider_pages_show_prices_status_and_measured_field_borders():
    if not Path(CHROME).exists():
        pytest.skip("actual local Chrome unavailable")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=CHROME, args=["--disable-gpu"])
        page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        for provider in ("provider-a", "provider-b", "provider-c"):
            for phase in range(3):
                snapshot = provider_snapshot(17, phase, provider=provider)
                html = provider_page(snapshot)
                assert html == provider_page(snapshot)
                page.set_content(html)
                page.evaluate("document.fonts.ready")
                assert page.locator('[data-role="provider"]').inner_text() == provider.replace("-", " ").title()
                assert page.locator('[data-role="selection"]').count() == 4
                assert page.locator('[data-role="odds"]').count() == 4
                assert page.get_by_text("Sports", exact=True).count() == 1
                assert page.locator('[data-role="odds"]').first.inner_text() == snapshot["quotes"][0]["odds"]
                assert page.locator('[data-role="status"]').nth(1).inner_text() == ("Suspended" if phase == 2 else "Open")
                for box in page.locator('[data-label]').evaluate_all("els=>els.map(e=>{const b=e.getBoundingClientRect();return [b.x,b.y,b.width,b.height]})"):
                    x, y, width, height = box
                    assert 0 <= x < x + width <= 390
                    assert 0 <= y < y + height <= 844
                assert page.locator("body").evaluate("e=>e.scrollWidth") == 390
        browser.close()


def test_bad_snapshot_and_inconsistent_shared_metadata_refuse_before_render():
    snapshot = provider_snapshot(0, 0)
    snapshot["quotes"][1]["quote_time"] = "2026-01-01T18:00:30Z"
    with pytest.raises(Refusal):
        provider_page(snapshot)
