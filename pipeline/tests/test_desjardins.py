"""Golden tests for Desjardins (desjardins.com) scraper."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from churney.config import SourceConfig
from churney.models import Network, RewardKind
from scrapers.desjardins import DesjardinsScraper

FIXTURES = Path(__file__).parent / "fixtures" / "desjardins"
LINK_PATTERN = r"^/en/credit-cards/([a-z0-9-]+)\.html$"
ENTRY_URLS = ["https://www.desjardins.com/en/credit-cards.html"]


def make_source(**overrides) -> SourceConfig:
    defaults = dict(
        name="desjardins",
        issuer_slug="desjardins",
        display_name="Desjardins",
        allowed=True,
        tos_reviewed_at=date.today(),
        cadence="weekly",
        fetch_mode="httpx",
        link_pattern=LINK_PATTERN,
        entry_urls=ENTRY_URLS,
    )
    defaults.update(overrides)
    return SourceConfig(**defaults)


def make_scraper() -> DesjardinsScraper:
    return DesjardinsScraper(None, make_source(), Path("."))


class TestDiscoverFromListingFixture:
    def test_finds_eight_consumer_cards(self):
        html = (FIXTURES / "listing.html").read_text(encoding="utf-8")
        scraper = make_scraper()
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse

        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            path = a["href"].split("?")[0].split("#")[0]
            if path.startswith("http"):
                path = urlparse(path).path
            if scraper._keep_link(path):
                seen.add(path)
        assert len(seen) == 8
        assert "/en/credit-cards/cash-back-visa.html" in seen
        assert "/en/credit-cards/compare-cards.html" not in seen


class TestParseCashBackVisa:
    URL = "https://www.desjardins.com/en/credit-cards/cash-back-visa.html"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "cash-back-visa.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_card_identity(self):
        cf = self.parse_once()
        assert cf.card.slug == "desjardins-cash-back-visa"
        assert cf.card.name == "Cash Back Visa Credit Card"
        assert cf.card.network == Network.VISA
        assert cf.card.program_slug == "cashback"

    def test_fees_and_apr_from_json_ld(self):
        cf = self.parse_once()
        assert cf.card_version.annual_fee_minor == 0
        assert cf.card_version.purchase_apr == 20.9
        assert cf.card_version.cash_apr == 21.9

    def test_category_earn_rates(self):
        cf = self.parse_once()
        by_cat = {r.category_slug: r for r in cf.earn_rates}
        assert by_cat["entertainment"].rate == 0.02
        assert by_cat["transit_rideshare"].rate == 0.02
        assert by_cat[None].rate == 0.005
        assert all(r.kind == RewardKind.CASHBACK for r in cf.earn_rates)


class TestParseOdysseyWorldElite:
    URL = "https://www.desjardins.com/en/credit-cards/odyssey-world-elite-mastercard.html"

    @classmethod
    def parse_once(cls):
        if not hasattr(cls, "_cf"):
            html = (FIXTURES / "odyssey-world-elite-mastercard.html").read_text(encoding="utf-8")
            cls._cf = make_scraper().parse_card(html, cls.URL)
        return cls._cf

    def test_bonusdollars_program(self):
        cf = self.parse_once()
        assert cf.card.program_slug == "bonusdollars"
        assert cf.card.network == Network.MASTERCARD
        assert cf.card_version.annual_fee_minor == 13000

    def test_bonusdollars_earn_kind(self):
        cf = self.parse_once()
        by_cat = {r.category_slug: r for r in cf.earn_rates}
        assert by_cat["grocery"].rate == 0.03
        assert by_cat[None].rate == 0.01
        assert all(r.kind == RewardKind.BONUS_DOLLARS for r in cf.earn_rates)

    def test_signup_bonus(self):
        cf = self.parse_once()
        assert len(cf.offers) == 1
        assert "130" in cf.offers[0].headline
        assert cf.offers[0].reward_cashback_minor == 13000

    def test_annual_earn_caps(self):
        cf = self.parse_once()
        by_cat = {r.category_slug: r for r in cf.earn_rates}
        assert by_cat["grocery"].cap_amount_minor == 1_000_000
        assert by_cat["grocery"].cap_period == "annual"
        assert by_cat["dining"].cap_amount_minor == 600_000
        assert by_cat["dining"].cap_period == "annual"
        assert by_cat["travel_other"].cap_amount_minor == 2_000_000


class TestParseFlexi:
    URL = "https://www.desjardins.com/en/credit-cards/flexi-visa.html"

    def test_no_rewards(self):
        html = (FIXTURES / "flexi-visa.html").read_text(encoding="utf-8")
        cf = make_scraper().parse_card(html, self.URL)
        assert cf.card.program_slug == "none"
        assert cf.card_version.purchase_apr == 10.9
        assert cf.earn_rates == []
