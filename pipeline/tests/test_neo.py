"""Golden tests for Neo Financial (neofinancial.com) scraper."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from churney.config import SourceConfig
from churney.models import Network, RewardKind
from scrapers import NeoScraper

FIXTURES = Path(__file__).parent / "fixtures" / "neo"
CARD_URLS = [
    "https://www.neofinancial.com/credit-cards/neo-mastercard",
    "https://www.neofinancial.com/credit-cards/neo-world-elite-mastercard",
    "https://www.neofinancial.com/credit-cards/neo-united-mastercard",
]


def make_source(**overrides) -> SourceConfig:
    defaults = dict(
        name="neo",
        issuer_slug="neo",
        display_name="Neo Financial",
        allowed=True,
        tos_reviewed_at=date.today(),
        cadence="weekly",
        fetch_mode="playwright",
        entry_urls=[],
        card_urls=CARD_URLS,
    )
    defaults.update(overrides)
    return SourceConfig(**defaults)


def make_scraper() -> NeoScraper:
    return NeoScraper(None, make_source(), Path("."))


class TestDiscoverCardUrls:
    def test_uses_explicit_card_urls(self):
        scraper = make_scraper()
        urls = list(scraper.discover_card_urls())
        assert len(urls) == 3
        assert all("neofinancial.com/credit-cards/neo-" in u for u in urls)


class TestParseNeoMastercard:
    URL = "https://www.neofinancial.com/credit-cards/neo-mastercard"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "neo-mastercard.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_card_identity(self):
        cf = self.parse_once()
        assert cf.card.slug == "neo-neo-mastercard"
        assert cf.card.name == "Neo Mastercard"
        assert cf.card.network == Network.MASTERCARD
        assert cf.card.program_slug == "cashback"

    def test_fees_and_apr_from_faq(self):
        cf = self.parse_once()
        assert cf.card_version.annual_fee_minor == 0
        assert cf.card_version.purchase_apr == 19.99
        assert cf.card_version.cash_apr == 22.99

    def test_earn_rate_not_in_current_page_copy(self):
        cf = self.parse_once()
        assert cf.earn_rates == []
        assert any(r.field == "earn_rates" for r in cf.needs_manual_review)


class TestParseNeoMastercardFeatureTile:
    """Older rendered snapshot still carries explicit 1% gas/grocery tile."""

    URL = "https://www.neofinancial.com/credit-cards/neo-mastercard"

    def test_feature_tile_cashback(self):
        html = (FIXTURES / "live-detail.html").read_text(encoding="utf-8")
        cf = make_scraper().parse_card(html, self.URL)
        by_cat = {r.category_slug: r for r in cf.earn_rates}
        assert by_cat["gas"].rate == 0.01
        assert by_cat["grocery"].rate == 0.01
        assert all(r.kind == RewardKind.CASHBACK for r in cf.earn_rates)


class TestParseWorldElite:
    URL = "https://www.neofinancial.com/credit-cards/neo-world-elite-mastercard"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "neo-world-elite-mastercard.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_card_identity(self):
        cf = self.parse_once()
        assert cf.card.slug == "neo-neo-world-elite-mastercard"
        assert cf.card.name == "Neo World Elite Mastercard"
        assert cf.card.program_slug == "cashback"

    def test_fees_and_apr(self):
        cf = self.parse_once()
        assert cf.card_version.annual_fee_minor == 14900
        assert cf.card_version.purchase_apr == 19.99
        assert cf.card_version.income_req_personal == 80000
        assert cf.card_version.income_req_household == 150000

    def test_tiered_cashback(self):
        cf = self.parse_once()
        by_cat = {r.category_slug: r for r in cf.earn_rates}
        assert by_cat["grocery"].rate == 0.05
        assert by_cat["recurring_bills"].rate == 0.04
        assert by_cat["gas"].rate == 0.03
        assert by_cat[None].rate == 0.01
        assert all(r.kind == RewardKind.CASHBACK for r in cf.earn_rates)


class TestParseUnited:
    URL = "https://www.neofinancial.com/credit-cards/neo-united-mastercard"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "neo-united-mastercard.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_card_identity(self):
        cf = self.parse_once()
        assert cf.card.slug == "neo-neo-united-mastercard"
        assert "United" in cf.card.name
        assert cf.card.program_slug == "united_mileageplus"

    def test_fees(self):
        cf = self.parse_once()
        assert cf.card_version.annual_fee_minor == 8900
        assert cf.card_version.income_req_personal == 80000

    def test_miles_earn_structure(self):
        cf = self.parse_once()
        by_cat = {r.category_slug: r for r in cf.earn_rates}
        assert by_cat["travel_air"].rate == 1.25
        assert by_cat["dining"].rate == 1.0
        assert by_cat["grocery"].rate == 1.0
        assert by_cat[None].rate == 0.75
        assert all(r.kind == RewardKind.POINTS for r in cf.earn_rates)

    def test_welcome_offer(self):
        cf = self.parse_once()
        assert len(cf.offers) == 1
        offer = cf.offers[0]
        assert offer.reward_points == 25000
        assert offer.min_spend_minor == 300000
        assert offer.deadline_days == 90
        assert len(offer.alternate_offers) >= 2
