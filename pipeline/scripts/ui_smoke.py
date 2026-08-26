"""Headless smoke test for the static UI (file:// load, filter, detail render)."""

from pathlib import Path

from playwright.sync_api import sync_playwright

ui = Path("ui/index.html").resolve()
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    page = b.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"file:///{ui.as_posix()}")
    page.wait_for_timeout(800)

    n_items = page.locator(".card-item").count()
    title = page.locator("#detail h1").first.inner_text() if n_items else "(none)"
    print(f"list items: {n_items}")
    print(f"preselected detail: {title}")

    # search filter
    page.fill("#search", "cobalt")
    page.wait_for_timeout(300)
    print("after search 'cobalt':", page.locator(".card-item").count())

    # issuer filter
    page.fill("#search", "")
    page.select_option("#issuer", "td")
    page.wait_for_timeout(300)
    print("after issuer=td:", page.locator(".card-item").count())

    # detail content sanity on first visible card
    page.select_option("#issuer", "")
    page.wait_for_timeout(200)
    page.locator(".card-item").first.click()
    page.wait_for_timeout(200)
    boxes = page.locator("#detail .box").count()
    review = page.locator("#detail .review-list li").count()
    print(f"detail boxes: {boxes}, review items shown: {review}")

    print("JS errors:", errors or "none")
    b.close()
