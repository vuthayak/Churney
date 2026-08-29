"""Golden tests for Brim Financial scraper."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from churney.config import SourceConfig
from churney.models import Network, RewardKind
from scrapers import BrimScraper

FIXTURES = Path(__file__).parent / "fixtures" / "brim"
CARD_URLS = [
    "https://brimfinancial.com/credit-cards#brim-mastercard",
    "https://brimfinancial.com/credit-cards#brim-world-elite-mastercard",
]


def make_source(**overrides) -> SourceConfig:
    defaults = dict(
        name="brim",
        issuer_slug="brim",
        display_name="Brim Financial",
        allowed=True,
        tos_reviewed_at=date.today(),
        cadence="monthly",
        fetch_mode="httpx",
        entry_urls=[],
        card_urls=CARD_URLS,
    )
    defaults.update(overrides)
    return SourceConfig(**defaults)


def make_scraper() -> BrimScraper:
    return BrimScraper(None, make_source(), Path("."))


class TestDiscoverCardUrls:
    def test_uses_explicit_card_urls(self):
        scraper = make_scraper()
        urls = list(scraper.discover_card_urls())
        assert len(urls) == 2
        assert all("brimfinancial.com/credit-cards#" in u for u in urls)


class TestParseBrimMastercard:
    URL = "https://brimfinancial.com/credit-cards#brim-mastercard"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "live-listing.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_card_identity(self):
        cf = self.parse_once()
        assert cf.card.slug == "brim-mastercard"
        assert cf.card.name == "Brim Mastercard"
        assert cf.card.network == Network.MASTERCARD
        assert cf.card.program_slug == "brim_rewards"

    def test_fees_and_earn(self):
        cf = self.parse_once()
        assert cf.card_version.annual_fee_minor == 0
        assert cf.card_version.fx_fee_pct == 1.5
        assert len(cf.earn_rates) == 1
        assert cf.earn_rates[0].rate == 0.5
        assert cf.earn_rates[0].kind == RewardKind.POINTS


class TestParseBrimWorldElite:
    URL = "https://brimfinancial.com/credit-cards#brim-world-elite-mastercard"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "live-listing.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_card_identity(self):
        cf = self.parse_once()
        assert cf.card.slug == "brim-world-elite-mastercard"
        assert cf.card.name == "Brim World Elite Mastercard"
        assert cf.card.network == Network.MASTERCARD

    def test_fees_and_earn(self):
        cf = self.parse_once()
        assert cf.card_version.annual_fee_minor == 8900
        assert cf.card_version.fx_fee_pct == 1.5
        assert cf.earn_rates[0].rate == 1.0
        assert cf.earn_rates[0].kind == RewardKind.POINTS
