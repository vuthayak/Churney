from __future__ import annotations

from datetime import date, timezone
from pathlib import Path

import pytest

from churney.config import SourceConfig
from churney.emit import load_card_file
from churney.fetch import Fetcher
from churney.models import Network, RewardKind
from scrapers.amex_ca import AmexCaScraper, classify_program, money_to_minor

from test_fetch import fixture_transport

FIXTURES = Path(__file__).parent / "fixtures" / "amex_ca"


def make_source(**overrides) -> SourceConfig:
    defaults = dict(
        name="amex_ca",
        issuer_slug="amex_ca",
        display_name="American Express Canada",
        allowed=True,
        tos_reviewed_at=date.today(),
        cadence="weekly",
        fetch_mode="httpx",
        entry_urls=[f"https://www.americanexpress.com/en/ca/network/personal-credit-cards.html"],
    )
    defaults.update(overrides)
    return SourceConfig(**defaults)


def make_scraper(tmp_path: Path, **source_overrides) -> AmexCaScraper:
    fetcher = Fetcher(
        cache_dir=tmp_path / "cache",
        transport=fixture_transport(),
        min_interval=0.0,
    )
    return AmexCaScraper(fetcher, make_source(**source_overrides), tmp_path / "data")


class TestHelpers:
    def test_money_to_minor(self):
        assert money_to_minor("$1,234.56") == 123456
        assert money_to_minor("$250") == 25000
        assert money_to_minor("capped at $2,500") == 250000
        assert money_to_minor("no money here") is None

    def test_classify_program(self):
        assert classify_program("Gold Rewards Card") == "amex_mr"
        assert classify_program("Aeroplan Card") == "aeroplan"
        assert classify_program("SimplyCash Preferred Card") == "simplycash"
        assert classify_program("Mystery Card") is None


class TestParseGoldRewardsCard:
    card_file = None

    @classmethod
    def parse_once(cls, tmp_path):
        if cls.card_file is None:
            html = (FIXTURES / "gold-rewards-card.html").read_text(encoding="utf-8")
            cls.card_file = make_scraper(tmp_path).parse_card(
                html, "https://www.americanexpress.com/en-ca/credit-cards/gold-rewards-card.html"
            )
        return cls.card_file

    def test_card_identity(self, tmp_path):
        cf = self.parse_once(tmp_path)
        card = cf.card
        assert card.slug == "amex-ca-gold-rewards-card"
        assert card.name == "Gold Rewards Card"
        assert card.network == Network.AMEX
        assert card.program_slug == "amex_mr"
        assert card.card_type == "personal"

    def test_version_terms(self, tmp_path):
        cf = self.parse_once(tmp_path)
        v = cf.card_version
        assert v.annual_fee_minor == 25000
        assert v.extra_card_fee_minor == 5000
        assert v.fx_fee_pct == 2.5
        assert v.purchase_apr == 21.99
        assert v.cash_apr == 22.99
        assert v.valid_from == date.today()
        assert v.source_url.endswith("gold-rewards-card.html")

    def test_earn_rates_golden(self, tmp_path):
        cf = self.parse_once(tmp_path)
        by_cat = {r.category_slug: r for r in cf.earn_rates}
        # base inserted first
        assert cf.earn_rates[0].category_slug is None
        assert cf.earn_rates[0].rate == 1.0
        assert cf.earn_rates[0].kind == RewardKind.POINTS
        g = by_cat["grocery"]
        assert g.rate == 5.0
        assert g.cap_amount_minor == 250_000
        d = by_cat["dining"]
        assert d.rate == 2.0
        assert len(cf.earn_rates) == 3

    def test_offer_two_layer_capture(self, tmp_path):
        cf = self.parse_once(tmp_path)
        assert len(cf.offers) == 1
        o = cf.offers[0]
        assert o.reward_points == 85000
        assert o.min_spend_minor == 750_000
        assert o.deadline_days == 180
        assert o.eligibility_notes == "deadline stated as 6 months on page"
        assert o.first_year_free is True
        assert o.verified_at.tzinfo is not None
        assert o.verified_at.utcoffset() == timezone.utc.utcoffset(None)
        # limited-time variant captured separately from canonical public offer
        assert len(o.alternate_offers) == 1
        alt = o.alternate_offers[0]
        assert alt.channel == "limited_time"
        assert alt.reward_points == 10000

    def test_no_review_items_when_fully_parsed(self, tmp_path):
        cf = self.parse_once(tmp_path)
        assert cf.needs_manual_review == []


class TestParseSimplyCashPreferred:
    def test_cashback_card_golden(self, tmp_path):
        html = (FIXTURES / "simplycash-preferred-card.html").read_text(encoding="utf-8")
        cf = make_scraper(tmp_path).parse_card(
            html, "https://www.americanexpress.com/en-ca/credit-cards/simplycash-preferred-card.html"
        )
        assert cf.card.program_slug == "simplycash"
        assert cf.card_version.annual_fee_minor == 12000
        kinds = {r.kind for r in cf.earn_rates}
        assert kinds == {RewardKind.CASHBACK}
        by_cat = {r.category_slug: r for r in cf.earn_rates}
        # cashback rates follow the data-model pct/100 convention (4% -> 0.04)
        assert by_cat["grocery"].rate == 0.04
        assert by_cat["grocery"].cap_amount_minor == 8_000_000
        assert by_cat["transit_rideshare"].rate == 0.02
        assert by_cat[None].rate == 0.0125  # base cashback
        offer = cf.offers[0]
        assert offer.reward_points is None
        assert offer.reward_cashback_minor == 40000
        assert offer.deadline_days == 90
        assert offer.alternate_offers == []


class TestFullRun:
    def test_run_emits_files_and_detects_drift(self, tmp_path):
        scraper = make_scraper(tmp_path)
        outcomes = scraper.run()
        assert [o.status for o in outcomes] == ["new", "new"]
        emitted = sorted(p.name for p in (tmp_path / "data" / "cards").glob("*.json"))
        assert emitted == [
            "amex-ca-gold-rewards-card.json",
            "amex-ca-simplycash-preferred-card.json",
        ]
        # round-trip validation through the envelope schema
        cf = load_card_file(tmp_path / "data" / "cards" / "amex-ca-gold-rewards-card.json")
        assert cf.content_hash is not None
        assert cf.schema_version == "1"

        outcomes2 = scraper.run(force=False)
        assert [o.status for o in outcomes2] == ["unchanged", "unchanged"]

    def test_tos_gate_blocks_uncrawlable_source(self, tmp_path):
        scraper = make_scraper(tmp_path, tos_reviewed_at=None)
        with pytest.raises(Exception, match="ToS review"):
            scraper.run()

    def test_limit_flag(self, tmp_path):
        scraper = make_scraper(tmp_path)
        outcomes = scraper.run(limit=1)
        assert len(outcomes) == 1

    def test_semantic_drift_ignores_volatile_fields(self, tmp_path):
        # Force re-parse of identical pages: timestamps differ, data doesn't.
        scraper = make_scraper(tmp_path)
        scraper.run()
        outcomes2 = scraper.run(force=True)
        assert [o.status for o in outcomes2] == ["unchanged", "unchanged"]


class TestParseAeroplanReserveLive:
    """Golden test for the real americanexpress.com page structure (tiles +
    two-part welcome bonus + trademark artifacts)."""

    def test_live_format_golden(self, tmp_path):
        html = (FIXTURES / "aeroplan-reserve.html").read_text(encoding="utf-8")
        cf = make_scraper(tmp_path).parse_card(
            html, "https://www.americanexpress.com/en-ca/credit-cards/aeroplan-reserve/"
        )
        card = cf.card
        assert card.name == "Aeroplan Reserve Card"
        assert card.slug == "amex-ca-aeroplan-reserve"
        assert card.program_slug == "aeroplan"

        v = cf.card_version
        assert v.annual_fee_minor == 59900
        assert v.extra_card_fee_minor == 19900
        assert v.purchase_apr == 21.99
        assert v.cash_apr == 21.99

        by_cat = {r.category_slug: r for r in cf.earn_rates}
        assert cf.earn_rates[0].category_slug is None
        assert cf.earn_rates[0].rate == 1.25
        assert by_cat["travel_air"].rate == 3.0
        assert by_cat["dining"].rate == 2.0
        assert by_cat["travel_hotel"].rate == 2.0
        assert len(cf.earn_rates) == 4

        offer = cf.offers[0]
        # canonical part of the two-part welcome bonus
        assert offer.reward_points == 60000
        assert offer.min_spend_minor == 750_000
        assert offer.deadline_days == 90
        assert "Current or former Cardmembers" in (offer.eligibility_notes or "")
        # month-13 component captured as a later-spend alternate
        later = [a for a in offer.alternate_offers if a.channel == "later_spend"]
        assert len(later) == 1
        assert later[0].reward_points == 25000
        assert later[0].min_spend_minor == 250_000

        fields = {r.field for r in cf.needs_manual_review}
        assert fields == {"fx_fee_pct"}


class TestNeverGuesses:
    def test_unparseable_page_routes_to_review(self, tmp_path):
        junk = "<html><body><h1>Some Card</h1><p>No structured data here.</p></body></html>"
        cf = make_scraper(tmp_path).parse_card(junk, "https://www.americanexpress.com/en-ca/credit-cards/some-card.html")
        fields = {r.field for r in cf.needs_manual_review}
        assert "annual_fee_minor" in fields
        assert "fx_fee_pct" in fields
        assert "purchase_apr" in fields
        assert "program_slug" in fields  # falls back but flagged
        assert cf.card.program_slug == "unknown"
        assert cf.offers == []


