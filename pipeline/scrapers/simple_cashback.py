"""Cashback-first issuers (Tangerine, Simplii): sentence-style earn copy,
percentage welcome promos. Extends the generic parser with a % cash-back WB
pattern that can't be valued in minor units without a spend basis."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from churney.models import Offer, ReviewItem
from scrapers.generic import GenericIssuerScraper

WB_CASH_PCT_RE = re.compile(
    r"[Ee]arn\s+(?:up to\s+)?(\d+(?:\.\d+)?)\s*%\s*cash ?back"
    r"(?:[^.]{0,60}?(?:for|during|in)\s+(?:the first\s+)?(\d+)\s*months?)?",
    re.I,
)


class SimpleCashbackScraper(GenericIssuerScraper):
    default_program = "cashback"

    def _extract_offer(self, text: str, url: str) -> tuple[Offer | None, list[ReviewItem]]:
        offer, reviews = super()._extract_offer(text, url)
        if offer is not None:
            return offer, reviews

        # Percentage-based cash-back promo ("Earn 10% cash back for 2 months").
        m = WB_CASH_PCT_RE.search(text)
        if m:
            pct = m.group(1)
            months = m.group(2)
            review = ReviewItem(
                field="offers",
                reason=f"percent-based bonus ({pct}% cash back"
                + (f" for {months} months" if months else "")
                + "); value depends on spend basis - manual valuation needed",
            )
            offer = Offer(
                headline=f"Earn {pct}% cash back" + (f" for {months} months" if months else ""),
                min_spend_minor=None,
                deadline_days=int(months) * 30 if months else None,
                reward_cashback_minor=None,
                eligibility_notes="percent-based welcome promo",
                alternate_offers=[],
                source_url=url,
                verified_at=datetime.now(timezone.utc),
            )
            return offer, [review]
        return None, reviews
