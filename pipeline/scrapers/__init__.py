"""Scraper registry: source name -> IssuerScraper implementation.

Thin per-issuer subclasses of GenericIssuerScraper carry only what differs:
program tokens, network default, and site quirks.
"""

from __future__ import annotations

from scrapers.amex_ca import AmexCaScraper
from scrapers.generic import GenericIssuerScraper
from scrapers.nbc import NbcScraper
from scrapers.rbcroyalbank import RbcRoyalBankScraper
from scrapers.simple_cashback import SimpleCashbackScraper


class TdScraper(GenericIssuerScraper):
    issuer_slug = "td"
    network = None  # inferred from name (Visa products)
    program_tokens = (
        ("aeroplan", "aeroplan"),
        ("first class travel", "td_rewards"),
        ("cash back", "cashback"),
    )


class CibcScraper(GenericIssuerScraper):
    issuer_slug = "cibc"
    program_tokens = (
        ("aeroplan", "aeroplan"),
        ("aventura", "aventura"),
        ("dividend", "cashback"),
        ("costco", "costco"),
        ("select", "cashback"),
    )


class ScotiabankScraper(GenericIssuerScraper):
    issuer_slug = "scotiabank"
    default_program = "scene_plus"  # all Scotia consumer cards earn Scene+
    program_tokens = (
        ("momentum", "cashback"),
        ("scene+", "scene_plus"),
        ("scene plus", "scene_plus"),
        ("scene", "scene_plus"),
    )
    excluded_families = {"manage-your-credit-card", "compare-cards"}


class TangerineScraper(SimpleCashbackScraper):
    issuer_slug = "tangerine"
    # 2026 lineup change: the former cash-back World Elite now earns Scene+
    # points (verified against tangerine.ca card page). Money-Back cards remain
    # cashback.
    default_program = "cashback"
    program_tokens = (
        ("rewards world elite", "scene_plus"),
        ("world elite", "scene_plus"),
        ("money-back", "cashback"),
        ("money back", "cashback"),
    )


class SimpliiScraper(SimpleCashbackScraper):
    issuer_slug = "simplii"


class RbcScraper(RbcRoyalBankScraper):
    """Registered alias; logic lives in scrapers/rbcroyalbank.py."""


SCRAPER_REGISTRY = {
    "amex_ca": AmexCaScraper,
    "td": TdScraper,
    "cibc": CibcScraper,
    "scotiabank": ScotiabankScraper,
    "tangerine": TangerineScraper,
    "simplii": SimpliiScraper,
    "rbcroyalbank": RbcScraper,
    "nbc": NbcScraper,
}
