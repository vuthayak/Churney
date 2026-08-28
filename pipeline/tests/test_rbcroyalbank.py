"""Golden tests for RBC Royal Bank scraper."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from churney.config import SourceConfig
from churney.models import Network, RewardKind
from scrapers import RbcScraper

FIXTURES = Path(__file__).parent / "fixtures" / "rbcroyalbank"
LINK_PATTERN = (
    r"^/credit-cards/(travel|rewards|cash-back|low-interest|no-fee|student)/"
    r"([a-z0-9_-]+)\.html$"
)
ENTRY_URLS = [
    "https://www.rbcroyalbank.com/credit-cards/index.html",
    "https://www.rbcroyalbank.com/credit-cards/travel.html",
    "https://www.rbcroyalbank.com/credit-cards/rewards.html",
    "https://www.rbcroyalbank.com/credit-cards/cash-back.html",
    "https://www.rbcroyalbank.com/credit-cards/low-interest.html",
    "https://www.rbcroyalbank.com/credit-cards/no-fee.html",
    "https://www.rbcroyalbank.com/credit-cards/student.html",
]


def make_source(**overrides) -> SourceConfig:
    defaults = dict(
        name="rbcroyalbank",
        issuer_slug="rbcroyalbank",
        display_name="RBC Royal Bank",
        allowed=True,
        tos_reviewed_at=date.today(),
        cadence="weekly",
        fetch_mode="httpx",
        link_pattern=LINK_PATTERN,
        entry_urls=ENTRY_URLS,
    )
    defaults.update(overrides)
    return SourceConfig(**defaults)


def make_scraper() -> RbcScraper:
    return RbcScraper(None, make_source(), Path("."))


class TestDiscoverFromListingFixture:
    def test_finds_fifteen_consumer_cards(self):
        html = (FIXTURES / "live-listing.html").read_text(encoding="utf-8")
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
        assert len(seen) == 15
        assert "/credit-cards/travel/rbc-avion-visa-infinite.html" in seen
        assert "/credit-cards/travel/avion-rbc-credit-cards.html" not in seen


class TestParseAvionVisaInfinite:
  URL = "https://www.rbcroyalbank.com/credit-cards/travel/rbc-avion-visa-infinite.html"

  @classmethod
  def parse_once(cls):
      if not hasattr(cls, "_cf"):
          html = (FIXTURES / "rbc-avion-visa-infinite.html").read_text(encoding="utf-8")
          cls._cf = make_scraper().parse_card(html, cls.URL)
      return cls._cf

  def test_card_identity(self):
      cf = self.parse_once()
      assert cf.card.slug == "rbcroyalbank-rbc-avion-visa-infinite"
      assert cf.card.name == "RBC Avion Visa Infinite"
      assert cf.card.program_slug == "avion"
      assert cf.card.network == Network.VISA

  def test_version_terms(self):
      cf = self.parse_once()
      v = cf.card_version
      assert v.annual_fee_minor == 12000
      assert v.extra_card_fee_minor == 5000
      assert v.purchase_apr == 20.99
      assert v.cash_apr == 22.99

  def test_earn_rates(self):
      cf = self.parse_once()
      rates = {(r.category_slug, r.rate, r.kind) for r in cf.earn_rates}
      assert (None, 1.0, RewardKind.POINTS) in rates
      assert ("travel_other", 1.25, RewardKind.POINTS) in rates

  def test_welcome_bonus(self):
      cf = self.parse_once()
      assert len(cf.offers) == 1
      assert cf.offers[0].reward_points == 70000


class TestParseIonVisa:
  URL = "https://www.rbcroyalbank.com/credit-cards/rewards/rbc-ion-visa.html"

  def test_no_fee_and_earn_structure(self):
      html = (FIXTURES / "rbc-ion-visa.html").read_text(encoding="utf-8")
      cf = make_scraper().parse_card(html, self.URL)
      assert cf.card_version.annual_fee_minor == 0
      rates = {(r.category_slug, r.rate) for r in cf.earn_rates}
      assert (None, 1.0) in rates
      assert ("grocery", 1.5) in rates


class TestParseCashbackMastercard:
  URL = "https://www.rbcroyalbank.com/credit-cards/cash-back/rbc-cashback-mastercard.html"

  def test_cashback_rates(self):
      html = (FIXTURES / "rbc-cashback-mastercard.html").read_text(encoding="utf-8")
      cf = make_scraper().parse_card(html, self.URL)
      assert cf.card.program_slug == "cashback"
      rates = {(r.category_slug, r.rate) for r in cf.earn_rates}
      assert ("grocery", 0.02) in rates
      assert (None, 0.01) in rates


class TestParseWestJetWorldElite:
    URL = (
        "https://www.rbcroyalbank.com/credit-cards/travel/"
        "westjet-rbc-world-elite-mastercard.html"
    )

    def test_westjet_earn_structure(self):
        html = (FIXTURES / "westjet-rbc-world-elite-mastercard.html").read_text(encoding="utf-8")
        cf = make_scraper().parse_card(html, self.URL)
        assert cf.card.program_slug == "westjet"
        rates = {(r.category_slug, r.rate) for r in cf.earn_rates}
        assert ("travel_air", 2.0) in rates
        assert ("grocery", 2.0) in rates
        assert (None, 1.5) in rates
        assert cf.offers[0].reward_points == 70000
