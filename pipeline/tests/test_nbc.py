"""Golden tests for National Bank of Canada (nbc.ca) scraper."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from churney.config import SourceConfig
from churney.models import Network, RewardKind
from scrapers import NbcScraper

FIXTURES = Path(__file__).parent / "fixtures" / "nbc"
CARD_URLS = [
    "https://www.nbc.ca/personal/mastercard-credit-cards/world-elite.html",
    "https://www.nbc.ca/personal/mastercard-credit-cards/echo.html",
    "https://www.nbc.ca/personal/mastercard-credit-cards/platinum.html",
    "https://www.nbc.ca/personal/mastercard-credit-cards/syncro.html",
]


def make_source(**overrides) -> SourceConfig:
    defaults = dict(
        name="nbc",
        issuer_slug="nbc",
        display_name="National Bank of Canada",
        allowed=True,
        tos_reviewed_at=date.today(),
        cadence="weekly",
        fetch_mode="httpx",
        entry_urls=[],
        card_urls=CARD_URLS,
    )
    defaults.update(overrides)
    return SourceConfig(**defaults)


def make_scraper() -> NbcScraper:
    return NbcScraper(None, make_source(), Path("."))


class TestDiscoverCardUrls:
    def test_uses_explicit_card_urls(self):
        scraper = make_scraper()
        urls = list(scraper.discover_card_urls())
        assert len(urls) == 4
        assert all("nbc.ca/personal/mastercard-credit-cards/" in u for u in urls)


class TestParseWorldElite:
    URL = "https://www.nbc.ca/personal/mastercard-credit-cards/world-elite.html"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "world-elite.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_card_identity(self):
        cf = self.parse_once()
        assert cf.card.slug == "nbc-world-elite"
        assert cf.card.name == "World Elite Mastercard"
        assert cf.card.network == Network.MASTERCARD
        assert cf.card.program_slug == "nbc_rewards"

    def test_fees_and_apr_from_product_map(self):
        cf = self.parse_once()
        assert cf.card_version.annual_fee_minor == 15000
        assert cf.card_version.extra_card_fee_minor == 5000
        assert cf.card_version.purchase_apr == 20.99
        assert cf.card_version.cash_apr == 22.49

    def test_earn_from_legal_copy(self):
        cf = self.parse_once()
        by_cat = {r.category_slug: r for r in cf.earn_rates}
        assert by_cat["gas"].rate == 2.0
        assert by_cat["recurring_bills"].rate == 2.0
        assert by_cat[None].rate == 1.0
        assert all(r.kind == RewardKind.POINTS for r in cf.earn_rates)


class TestParseEcho:
    URL = "https://www.nbc.ca/personal/mastercard-credit-cards/echo.html"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "echo.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_cashback_card(self):
        cf = self.parse_once()
        assert cf.card.program_slug == "cashback"
        assert cf.card_version.annual_fee_minor == 3000
        assert any(r.kind == RewardKind.CASHBACK for r in cf.earn_rates)


class TestParseSyncro:
    URL = "https://www.nbc.ca/personal/mastercard-credit-cards/syncro.html"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "syncro.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_low_rate_card(self):
        cf = self.parse_once()
        assert cf.card_version.purchase_apr == 8.9
        assert cf.card_version.annual_fee_minor == 3500
