"""Golden tests for BMO (bmo.com) scraper."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from churney.config import SourceConfig
from churney.models import Network, RewardKind
from scrapers import BmoScraper

FIXTURES = Path(__file__).parent / "fixtures" / "bmo"
CARD_URLS = [
    "https://www.bmo.com/main/personal/credit-cards/bmo-eclipse-visa-infinite/",
    "https://www.bmo.com/main/personal/credit-cards/bmo-cashback-mastercard/",
    "https://www.bmo.com/en-ca/main/personal/credit-cards/bmo-viporter-mastercard/",
    "https://www.bmo.com/en-ca/main/personal/credit-cards/preferred-rate-mastercard/",
    "https://www.bmo.com/en-ca/main/business/credit-cards/bmo-blue-rewards-business-mastercard/",
]


def make_source(**overrides) -> SourceConfig:
    defaults = dict(
        name="bmo",
        issuer_slug="bmo",
        display_name="BMO",
        allowed=True,
        tos_reviewed_at=date.today(),
        cadence="weekly",
        fetch_mode="httpx",
        entry_urls=[],
        card_urls=CARD_URLS,
    )
    defaults.update(overrides)
    return SourceConfig(**defaults)


def make_scraper() -> BmoScraper:
    return BmoScraper(None, make_source(), Path("."))


class TestDiscoverCardUrls:
    def test_uses_explicit_card_urls(self):
        scraper = make_scraper()
        urls = list(scraper.discover_card_urls())
        assert len(urls) == 5
        assert all("bmo.com" in u for u in urls)


class TestParseEclipseVisaInfinite:
    URL = "https://www.bmo.com/main/personal/credit-cards/bmo-eclipse-visa-infinite/"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "bmo-eclipse-visa-infinite.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_card_identity(self):
        cf = self.parse_once()
        assert cf.card.slug == "bmo-eclipse-visa-infinite"
        assert cf.card.name == "BMO eclipse Visa Infinite Card"
        assert cf.card.network == Network.VISA
        assert cf.card.program_slug == "bmo_rewards"

    def test_fees_and_apr_from_json_ld(self):
        cf = self.parse_once()
        assert cf.card_version.annual_fee_minor == 12000
        assert cf.card_version.purchase_apr == 20.99


class TestParseCashbackMastercard:
    URL = "https://www.bmo.com/main/personal/credit-cards/bmo-cashback-mastercard/"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "bmo-cashback-mastercard.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_cashback_rates(self):
        cf = self.parse_once()
        assert cf.card.program_slug == "cashback"
        by_cat = {r.category_slug: r for r in cf.earn_rates}
        assert by_cat["grocery"].rate == 0.03
        assert by_cat[None].rate == 0.005
        assert all(r.kind == RewardKind.CASHBACK for r in cf.earn_rates)


class TestParseViporterMastercard:
    URL = "https://www.bmo.com/en-ca/main/personal/credit-cards/bmo-viporter-mastercard/"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "bmo-viporter-mastercard.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_viporter_program(self):
        cf = self.parse_once()
        assert cf.card.program_slug == "viporter"
        assert cf.card_version.annual_fee_minor == 0


class TestParsePreferredRate:
    URL = "https://www.bmo.com/en-ca/main/personal/credit-cards/preferred-rate-mastercard/"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "preferred-rate-mastercard.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_low_rate_card(self):
        cf = self.parse_once()
        assert cf.card.program_slug == "none"
        assert cf.card_version.annual_fee_minor == 2900
        assert cf.card_version.purchase_apr == 13.99


class TestParseBlueRewardsBusiness:
    URL = "https://www.bmo.com/en-ca/main/business/credit-cards/bmo-blue-rewards-business-mastercard/"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "bmo-blue-rewards-business-mastercard.html").read_text(
                encoding="utf-8"
            )
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_business_card(self):
        cf = self.parse_once()
        assert cf.card.card_type == "business"
        assert cf.card_version.annual_fee_minor == 0
        assert cf.card_version.purchase_apr == 23.99
        assert cf.offers and cf.offers[0].reward_points == 30000
