"""Playwright-backed fetcher: renders JavaScript with headless Chromium, then
hands the rendered DOM to the shared Fetcher pipeline (robots, throttle,
cache, drift). Used for JS-rendered issuer sites (docs/04 §9.1 fetch decision).
"""

from __future__ import annotations

from pathlib import Path

from churney.fetch import Fetcher


class PlaywrightFetcher(Fetcher):
    def __init__(
        self,
        cache_dir: Path,
        *,
        wait_after_load_ms: int = 3000,
        goto_timeout_ms: int = 45_000,
        **kwargs,
    ) -> None:
        super().__init__(cache_dir, **kwargs)
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        context = self._browser.new_context(
            user_agent=self.client.headers["User-Agent"],
            locale="en-CA",
            viewport={"width": 1440, "height": 2400},
            timezone_id="America/Toronto",
        )
        self._context = context
        self._page = context.new_page()
        self._wait_after_load_ms = wait_after_load_ms
        self._goto_timeout_ms = goto_timeout_ms

    def _get(self, url: str) -> tuple[int, str]:
        resp = self._page.goto(url, wait_until="domcontentloaded", timeout=self._goto_timeout_ms)
        try:
            self._page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:  # noqa: BLE001 - networkidle is best-effort
            pass
        self._page.wait_for_timeout(self._wait_after_load_ms)
        status = resp.status if resp else 0
        return status, self._page.content()

    def close(self) -> None:
        try:
            self._context.close()
            self._browser.close()
            self._pw.stop()
        finally:
            self.client.close()
