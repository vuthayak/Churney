"""Golden tests for the config-driven generic scraper against CIBC fixtures.

CIBC exercises code paths Amex doesn't:
- grouped point lines ("2 points for every $1 spent on eligible travel ...")
- multi-category earn contexts ("gas stations, ... grocery stores and drug stores")
- DOM-split numbers ("35 ,000 Aventura Points")
- statement-period MSR deadlines ("first 4 monthly statement periods")
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from churney.config import SourceConfig
from churney.models import Network, RewardKind
from scrapers import CibcScraper

FIXTURES = Path(__file__).parent / "fixtures" / "cibc"
CARD_URL = (
    "https://www.cibc.com/en/personal-banking/credit-cards/"
    "all-credit-cards/aventura-visa-infinite-card.html"
)


def make_source(**overrides) -> SourceConfig:
    defaults = dict(
        name="cibc",
        issuer_slug="cibc",
        display_name="CIBC",
        allowed=True,
        tos_reviewed_at=date.today(),
        cadence="weekly",
        fetch_mode="httpx",
        entry_urls=[],
    )
    defaults.update(overrides)
    return SourceConfig(**defaults)


def make_scraper() -> CibcScraper:
    # parse_card() needs no fetcher; discovery is tested elsewhere.
    return CibcScraper(None, make_source(), Path("."))


def parse_aventura():
    html = (FIXTURES / "aventura-visa-infinite-card.html").read_text(encoding="utf-8")
    return make_scraper().parse_card(html, CARD_URL)


class TestParseAventuraVisaInfinite:
    def test_card_identity(self):
        cf = parse_aventura()
        assert cf.card.name == "CIBC Aventura Visa Infinite Card"
        assert cf.card.program_slug == "aventura"
        assert cf.card.network == Network.VISA
        assert cf.card.card_type == "personal"

    def test_earn_rates_golden(self):
        """CIBC copy: '1.5 points for every $1 spent at eligible gas stations,
        electric vehicle charging stations, grocery stores and drug stores'."""
        cf = parse_aventura()
        rates = {(r.category_slug, r.rate): r for r in cf.earn_rates}
        assert rates[("grocery", 1.5)].kind == RewardKind.POINTS
        assert rates[("gas", 1.5)]
        assert rates[("drugstore", 1.5)]  # 'drug stores' hint variant
        assert rates[(None, 1.0)]  # '1 point for every $1 ... all other purchases'
        assert rates[("travel_other", 2.0)]  # CIBC Rewards Centre travel

    def test_offer_statement_period_msr(self):
        """'Get a total of up to 35,000 Aventura Points' + '$3,000 ... in the
        first 4 monthly statement periods' -> 35k pts / $3,000 / 120 days."""
        cf = parse_aventura()
        assert len(cf.offers) == 1
        offer = cf.offers[0]
        assert offer.reward_points == 35000
        assert offer.min_spend_minor == 300000
        assert offer.deadline_days == 120

    def test_no_unmatched_context_reviews(self):
        cf = parse_aventura()
        ppd_reviews = [
            r for r in cf.needs_manual_review if "points-per-dollar" in r.reason
        ]
        assert ppd_reviews == []

    def test_fx_fee_still_flagged_for_review(self):
        """Never-guess rule: missing FX fee must surface as a review item."""
        cf = parse_aventura()
        assert any(r.field == "fx_fee_pct" for r in cf.needs_manual_review)


class TestParseDividendVisaInfinite:
    def test_cashback_card_still_golden(self):
        """Regression guard: the % cash-back path that already worked."""
        html = (FIXTURES / "live-detail.html").read_text(encoding="utf-8")
        url = (
            "https://www.cibc.com/en/personal-banking/credit-cards/"
            "all-credit-cards/dividend-visa-infinite-card.html"
        )
        cf = make_scraper().parse_card(html, url)
        rates = {(r.category_slug, r.rate) for r in cf.earn_rates}
        assert ("gas", 0.04) in rates
        assert ("grocery", 0.04) in rates
        assert (None, 0.01) in rates  # '1% cash back on everything else'
        assert cf.card.program_slug == "cashback"


class TestDiscoverAbsoluteUrls:
    def test_absolute_href_matches_link_pattern(self):
        """Listing pages sometimes use full https:// hrefs instead of relative paths."""
        from urllib.parse import urlparse

        from bs4 import BeautifulSoup

        from scrapers import ScotiabankScraper

        html = (
            '<a href="https://www.scotiabank.com/ca/en/personal/credit-cards/'
            'visa/momentum-infinite-card.html">Momentum</a>'
        )
        scraper = ScotiabankScraper(
            None,
            make_source(issuer_slug="scotiabank", name="scotiabank", link_pattern=(
                "^/ca/en/personal/credit-cards/(visa|american-express)/([a-z0-9-]+)\\.html$"
            )),
            Path("."),
        )
        soup = BeautifulSoup(html, "lxml")
        paths = []
        for a in soup.find_all("a", href=True):
            path = a["href"].split("?")[0].split("#")[0]
            if path.startswith("http"):
                path = urlparse(path).path
            if scraper._keep_link(path):
                paths.append(path)
        assert paths == ["/ca/en/personal/credit-cards/visa/momentum-infinite-card.html"]


class TestNumberNormalization:
    def test_split_number_rejoined(self):
        """DOM-split '35 ,000' must become '35,000' before regex extraction."""
        import re

        from scrapers.generic import GenericIssuerScraper

        soup_text = re.sub(r"\s+", " ", "Get a total of up to 35 ,000 Points")
        normalized = re.sub(r"(\d)\s*,\s*(\d)", r"\1,\2", soup_text)
        assert normalized == "Get a total of up to 35,000 Points"
        # and the WB pattern now matches it
        from scrapers.common import WB_POINTS_RE

        m = WB_POINTS_RE.search(normalized)
        assert m and m.group(1) == "35,000"
