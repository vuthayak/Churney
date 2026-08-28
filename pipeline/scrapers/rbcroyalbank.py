"""RBC Royal Bank scraper.

RBC card pages are server-rendered with stable copy, but earn tiles use a
site-specific pattern ("1.25X Earn 1.25 Avion points on travel ...") and fees
use "Annual Fee $120" / "Purchase Rate 20.99%" labels instead of the generic
patterns other issuers share.
"""

from __future__ import annotations

import re

from churney.models import CardVersion, EarnRate, ReviewItem, RewardKind
from scrapers.common import (
    match_all_categories,
    money_to_minor,
)
from scrapers.generic import GenericIssuerScraper

# "1.25X Earn 1.25 Avion points on travel related purchases"
# "1.5X Earn 1.5X Avion points for every $1 spent on groceries, gas ..."
RBC_EARN_BLOCK_RE = re.compile(
    r"(\d+(?:\.\d+)?)X\s+Earn\s+(\d+(?:\.\d+)?)(?:X)?\s+(?:Avion\s+)?points?\s+"
    r"(?:for every \$1 spent on|on)\s+([^.]{3,120}?)"
    r"(?=\s+\d+(?:\.\d+)?X\s+Earn|\s+\d{1,3},\d{3}\s+Avion|\s+Annual Fee|\s+Apply by|\s+Features|\s+How to|$)",
    re.I,
)
RBC_BASE_CTX = (
    "all other",
    "everyday",
    "everything else",
    "qualifying purchases",
    "other eligible",
)

RBC_FEE_RE = re.compile(r"Annual Fee\s*\$([\d,]+(?:\.\d{2})?)", re.I)
RBC_SUPP_FEE_RE = re.compile(r"Additional Card\s*\$([\d,]+(?:\.\d{2})?)", re.I)
RBC_PURCHASE_APR_RE = re.compile(r"Purchase Rate\s*(\d+(?:\.\d+)?)\s*%", re.I)
RBC_CASH_APR_RE = re.compile(r"Cash Advance Rate\s*(\d+(?:\.\d+)?)\s*%", re.I)
RBC_NO_FEE_RE = re.compile(r"Annual Fee\s*\$0\b", re.I)
RBC_BASE_CASHBACK_RE = re.compile(
    r"(?:up to\s+)?(\d+(?:\.\d+)?)\s*%\s*cash ?back\s+on\s+"
    r"(?:all your other|all other|your everyday|all purchases|other qualifying)",
    re.I,
)
RBC_CATEGORY_CASHBACK_RE = re.compile(
    r"(?<![\d.])(\d+(?:\.\d+)?)\s*%\s*cash ?back\s+on\s+([^.;]{3,80}?)"
    r"(?=\s+\d|\s+and\s+up\s+to|\s+apply|\s+annual|\s+for\s+the|\s+unlock|$)",
    re.I,
)


class RbcRoyalBankScraper(GenericIssuerScraper):
    issuer_slug = "rbcroyalbank"
    program_tokens = (
        ("british airways", "british_airways"),
        ("westjet", "westjet"),
        ("avion", "avion"),
        ("ion plus", "avion"),
        ("ion", "avion"),
        ("more rewards", "rbc_rewards"),
        ("moi", "rbc_rewards"),
        ("cash back", "cashback"),
        ("cashback", "cashback"),
        ("low rate", "cashback"),
    )
    excluded_families = {
        "avion-rbc-credit-cards",
        "westjet_rbc_credit-cards",
    }

    def _extract_version(self, text: str, url: str, review: list[ReviewItem]) -> CardVersion:
        fee_m = RBC_FEE_RE.search(text)
        if fee_m:
            annual_fee_minor = money_to_minor("$" + fee_m.group(1))
        elif RBC_NO_FEE_RE.search(text):
            annual_fee_minor = 0
        else:
            annual_fee_minor = None
            review.append(ReviewItem(field="annual_fee_minor", reason="fee pattern not found"))

        supp = RBC_SUPP_FEE_RE.search(text)
        extra = money_to_minor("$" + supp.group(1)) if supp else None

        apr_m = RBC_PURCHASE_APR_RE.search(text)
        purchase_apr = float(apr_m.group(1)) if apr_m else None
        cash_m = RBC_CASH_APR_RE.search(text)
        cash_apr = float(cash_m.group(1)) if cash_m else None
        if purchase_apr is None:
            review.append(ReviewItem(field="purchase_apr", reason="purchase APR pattern not found"))

        fx_fee_pct = None
        review.append(
            ReviewItem(
                field="fx_fee_pct",
                reason="per-card FX fee not stated; most CA cards 2.5% [VERIFY]",
            )
        )

        return CardVersion(
            valid_from=self._today,
            annual_fee_minor=annual_fee_minor,
            extra_card_fee_minor=extra,
            fx_fee_pct=fx_fee_pct,
            purchase_apr=purchase_apr,
            cash_apr=cash_apr,
            source_url=url,
        )

    def _extract_earn_rates(self, text: str, url: str) -> tuple[list[EarnRate], list[ReviewItem]]:
        rates: list[EarnRate] = []
        reviews: list[ReviewItem] = []
        seen: set[tuple[str | None, float]] = set()

        def add(category, value: float, kind: RewardKind) -> None:
            key = (category, value)
            if key in seen:
                return
            seen.add(key)
            rates.append(
                EarnRate(category_slug=category, rate=value, kind=kind, source_url=url)
            )

        for m in RBC_EARN_BLOCK_RE.finditer(text):
            rate = float(m.group(2))
            ctx = m.group(3).strip().lower()
            if any(token in ctx for token in RBC_BASE_CTX):
                add(None, rate, RewardKind.POINTS)
                continue
            cats = match_all_categories(ctx)
            if not cats:
                reviews.append(
                    ReviewItem(
                        field="earn_rates",
                        reason=f"RBC earn context not matched: {ctx[:90]!r}",
                    )
                )
                continue
            for cat in cats:
                add(cat, rate, RewardKind.POINTS)

        if rates:
            if not any(r.category_slug is None for r in rates):
                reviews.append(ReviewItem(field="earn_rates", reason="no base-rate pattern found"))
            return rates, reviews

        if "cash back" in text.lower() or "cashback" in text.lower():
            return self._extract_cashback_rates(text, url)

        return super()._extract_earn_rates(text, url)

    def _extract_cashback_rates(
        self, text: str, url: str
    ) -> tuple[list[EarnRate], list[ReviewItem]]:
        rates: list[EarnRate] = []
        reviews: list[ReviewItem] = []
        seen: set[tuple[str | None, float]] = set()

        def add(category, value: float) -> None:
            if value > 0.10:
                return
            key = (category, value)
            if key in seen:
                return
            seen.add(key)
            rates.append(
                EarnRate(
                    category_slug=category,
                    rate=value,
                    kind=RewardKind.CASHBACK,
                    source_url=url,
                )
            )

        base_m = RBC_BASE_CASHBACK_RE.search(text)
        if base_m:
            add(None, float(base_m.group(1)) / 100)

        for m in RBC_CATEGORY_CASHBACK_RE.finditer(text):
            ctx = m.group(2).lower()
            if any(
                token in ctx
                for token in ("all other", "everyday", "everything else", "other qualifying")
            ):
                continue
            cats = match_all_categories(ctx)
            if not cats:
                continue
            value = float(m.group(1)) / 100
            for cat in cats:
                add(cat, value)

        if not rates:
            reviews.append(ReviewItem(field="earn_rates", reason="no earn patterns found on page"))
        elif not any(r.category_slug is None for r in rates):
            reviews.append(ReviewItem(field="earn_rates", reason="no base-rate pattern found"))
        return rates, reviews
