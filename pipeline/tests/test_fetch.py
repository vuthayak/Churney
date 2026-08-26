from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pytest

from churney.config import SourceConfig, load_sources
from churney.fetch import Fetcher, RobotsDisallowed

FIXTURES = Path(__file__).parent / "fixtures" / "amex_ca"
HOST = "www.americanexpress.com"


def fixture_transport(robots_body: str | None = "standard"):
    """httpx.MockTransport serving fixture files by URL path."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = urlparse(str(request.url)).path
        if path == "/robots.txt":
            if robots_body is None:
                return httpx.Response(404)
            body = (
                "User-agent: *\nDisallow: /private/\n"
                if robots_body == "standard"
                else robots_body
            )
            return httpx.Response(200, text=body)
        # entry/listing pages
        if path.endswith(("personal-credit-cards.html", "business-credit-cards.html")):
            return httpx.Response(
                200, text=(FIXTURES / "listing.html").read_text(encoding="utf-8")
            )
        name = path.rstrip("/").split("/")[-1]
        file = FIXTURES / (name if name.endswith(".html") else f"{name}.html")
        if not file.exists():
            return httpx.Response(404)
        return httpx.Response(200, text=file.read_text(encoding="utf-8"))

    return httpx.MockTransport(handler)


def make_fetcher(tmp_path: Path, **kwargs) -> Fetcher:
    kwargs.setdefault("transport", fixture_transport())
    kwargs.setdefault("min_interval", 0.0)  # no real sleeping in tests
    return Fetcher(cache_dir=tmp_path / "cache", **kwargs)


class TestFetcher:
    def test_drift_detection_new_then_unchanged(self, tmp_path):
        f = make_fetcher(tmp_path)
        url = f"https://{HOST}/en-ca/credit-cards/gold-rewards-card.html"
        first = f.fetch(url)
        assert first.status == "new"
        second = f.fetch(url)
        assert second.status == "unchanged"
        assert first.content_hash == second.content_hash
        # cached body exists and index tracks the hash
        assert Path(json.loads((tmp_path / "cache" / "index.json").read_text())[url]["body"]).exists()

    def test_robots_disallowed(self, tmp_path):
        f = make_fetcher(tmp_path)
        with pytest.raises(RobotsDisallowed):
            f.fetch(f"https://{HOST}/private/internal-tools/")

    def test_robots_missing_means_unrestricted(self, tmp_path):
        f = make_fetcher(tmp_path, transport=fixture_transport(robots_body=None))
        result = f.fetch(f"https://{HOST}/en-ca/credit-cards/gold-rewards-card.html")
        assert result.status == "new"

    def test_rate_limit_enforced_per_host(self, tmp_path):
        ticks = iter(range(10**9))

        def fake_clock() -> float:
            return next(ticks)

        f = make_fetcher(tmp_path, min_interval=5.0, clock=fake_clock)
        url = f"https://{HOST}/en-ca/credit-cards/gold-rewards-card.html"
        f._last_hit[HOST] = 100.0  # pretend we just hit the host at t=100
        # advance fake clock so next() returns 101 -> wait = 5 - (101-100) = 4s > 0
        # time.sleep is called; patch it out and verify it was called with >0
        slept = {}
        import time as _time

        orig_sleep = _time.sleep
        _time.sleep = lambda s: slept.update(s=s)
        try:
            f.fetch(url)
        finally:
            _time.sleep = orig_sleep
        assert slept.get("s", 0) > 0


class TestSourcesConfig:
    def test_uncrawlable_without_tos_review(self, tmp_path):
        cfg = SourceConfig(
            name="amex_ca",
            issuer_slug="amex_ca",
            display_name="Amex",
            allowed=True,
            tos_reviewed_at=None,
            cadence="weekly",
            fetch_mode="httpx",
            entry_urls=[],
        )
        with pytest.raises(Exception, match="ToS review not recorded"):
            cfg.assert_crawlable()

    def test_load_sources_yaml(self):
        sources = load_sources(Path(__file__).parents[1] / "sources.yaml")
        assert "amex_ca" in sources
        assert sources["amex_ca"].issuer_slug == "amex_ca"

