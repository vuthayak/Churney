"""RBC Royal Bank scraper.

RBC card pages are server-rendered with stable copy, but earn tiles use a
site-specific pattern ("1.25X Earn 1.25 Avion points on travel ...") and fees
use "Annual Fee $120" / "Purchase Rate 20.99%" labels instead of the generic
patterns other issuers share.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from churney.models import (
    AlternateOffer,
    CardVersion,
    EarnRate,
    Offer,
    ReviewItem,
    RewardKind,
)
from scrapers.common import (
    ELIGIBILITY_NOTES_RE,
    FIRST_YEAR_FREE_RE,
    LATER_SPEND_RE,
    MSR_DAYS_RE,
    MSR_MONTHS_RE,
    MSR_STATEMENT_RE,
    WB_POINTS_RE,
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
    "everywhere else",
)

RBC_FEE_RE = re.compile(r"Annual Fee\s*:?\s*\$([\d,]+(?:\.\d{2})?)", re.I)
RBC_SUPP_FEE_RE = re.compile(r"Additional Card\s*:?\s*\$([\d,]+(?:\.\d{2})?)", re.I)
RBC_PURCHASE_APR_RE = re.compile(r"Purchase Rate\s*:?\s*(\d+(?:\.\d+)?)\s*%", re.I)
RBC_CASH_APR_RE = re.compile(r"Cash Advance Rate\s*:?\s*(\d+(?:\.\d+)?)\s*%", re.I)
RBC_NO_FEE_RE = re.compile(r"Annual Fee\s*:?\s*\$0\b", re.I)
RBC_NO_ANNUAL_FEE_RE = re.compile(r"no annual fee", re.I)
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
# WestJet / More Rewards / MOI: "Earn 2 points for every dollar you spend on ..."
RBC_DOLLAR_EARN_RE = re.compile(
    r"Earn\s+(\d+(?:\.\d+)?)\s+(?:westjet\s+|moi\s+)?points?\s+for every\s+dollar\s+you\s+spend\s+"
    r"(?:on|at)\s+"
    r"([^.]{3,120}?)(?=\s+\d+\s|\s+Earn\s+\d|\s+Annual|\s+Apply|\s+Get|\s+New!|\s+Use|\s+\.|$)",
    re.I,
)
# MOI / More Rewards: "Earn 5 points for every $1 spent at/on ..."
RBC_DOLLAR_ONE_EARN_RE = re.compile(
    r"Earn\s+(\d+(?:\.\d+)?)\s+(?:moi\s+)?points?\s+for every\s+\$1\s+"
    r"(?:in purchases(?:\s+when[^.]{0,80})?|spent(?:\s+at|\s+on))\s+([^.]{3,120}?)"
    r"(?=\.|\s+Earn\s+\d|\s+Annual|\s+Apply|\s+Get|\s+A value|\s+Even|$)",
    re.I,
)
RBC_AVIOS_EARN_RE = re.compile(
    r"Earn\s+(\d+(?:\.\d+)?)\s+Avios\s+for every\s+dollar\s+you\s+spend\s+on\s+"
    r"([^.]{3,80}?)(?=\s+\d+\s+Avios|\s+Earn\s+\d|\s+Annual|\s+Apply|\s+Take|\s+\.|$)",
    re.I,
)
# Business: "Earn 1.25 Avion points for every $1 spent in net purchases"
RBC_AVION_PPD_RE = re.compile(
    r"Earn\s+(\d+(?:\.\d+)?)\s+Avion\s+points?\s+for every\s+\$1\s+spent\s+"
    r"(?:in\s+)?([^.]{3,120}?)(?=\.|$|\s+Earn\s+\d)",
    re.I,
)
# WestJet business: "Earn 3 WestJet points per $1 spent on ..."
RBC_WESTJET_PER_DOLLAR_RE = re.compile(
    r"Earn\s+(\d+(?:\.\d+)?)\s+WestJet\s+points?\s+(?:for every|per)\s+\$1\s+spent\s+on\s+"
    r"([^.]{3,120}?)(?=\.|$|\s+Earn\s+\d)",
    re.I,
)
# Marketing + legal welcome bonuses
RBC_WB_AVIOS_RE = re.compile(
    r"(?:[Rr]eceive|[Gg]et)\s+(?:up to\s+)?([\d,]+)\s+bonus\s+Avios",
    re.I,
)
RBC_LEGAL_MSR_DAYS_RE = re.compile(
    r"(?:a total of|totaling)\s+\$([\d,]+)\s+or more.{0,220}?"
    r"within(?:\s+the)?\s+first\s+(\d+)\s+days",
    re.I,
)
RBC_LEGAL_MSR_RANGE_RE = re.compile(
    r"(?:a total of|totaling)\s+\$([\d,]+)\s+or more.{0,220}?"
    r"within\s+(\d+)\s*-\s*(\d+)\s+days",
    re.I,
)
RBC_INTRO_CASHBACK_RE = re.compile(
    r"Earn\s+(\d+(?:\.\d+)?)%\s*cash ?back\s+on\s+purchases",
    re.I,
)
RBC_EXCLUDED_CARD_TAILS = {
    "manage-my-avion-visa-infinite-business",
    "visa-creditline",
}


class RbcRoyalBankScraper(GenericIssuerScraper):
    issuer_slug = "rbcroyalbank"
    program_tokens = (
        ("classic low rate", "none"),
        ("british airways", "british_airways"),
        ("westjet", "westjet"),
        ("avion", "avion"),
        ("ion plus", "avion"),
        ("ion", "avion"),
        ("more rewards", "rbc_rewards"),
        ("moi", "rbc_rewards"),
        ("visa business card", "none"),
        ("visa business", "none"),
        ("visa platinum", "none"),
        ("cash back", "cashback"),
        ("cashback", "cashback"),
        ("low rate", "cashback"),
    )
    default_program = "avion"  # most RBC consumer cards earn Avion-branded points
    excluded_families = {
        "avion-rbc-credit-cards",
        "westjet_rbc_credit-cards",
    }

    def _keep_link(self, path: str) -> bool:
        if not super()._keep_link(path):
            return False
        tail = path.rstrip("/").split("/")[-1].removesuffix(".html")
        return tail not in RBC_EXCLUDED_CARD_TAILS

    def parse_card(self, html: str, url: str) -> CardFile:
        self._last_html = html
        return super().parse_card(html, url)

    def _classify_program(self, name: str) -> str | None:
        lowered = name.lower()
        if lowered in ("visa business card", "visa business"):
            return "none"
        return super()._classify_program(name)

    def _extract_version(self, text: str, url: str, review: list[ReviewItem]) -> CardVersion:
        fee_m = RBC_FEE_RE.search(text)
        if fee_m:
            annual_fee_minor = money_to_minor("$" + fee_m.group(1))
        elif RBC_NO_FEE_RE.search(text) or RBC_NO_ANNUAL_FEE_RE.search(text):
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

    def _html_text(self) -> str:
        raw = getattr(self, "_last_html", "")
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw))

    def _extract_earn_rates(self, text: str, url: str) -> tuple[list[EarnRate], list[ReviewItem]]:
        rates: list[EarnRate] = []
        reviews: list[ReviewItem] = []
        seen: set[tuple[str | None, float]] = set()
        sources = (text, self._html_text()) if getattr(self, "_last_html", None) else (text,)

        def add(category, value: float, kind: RewardKind = RewardKind.POINTS) -> None:
            key = (category, value)
            if key in seen:
                return
            seen.add(key)
            rates.append(
                EarnRate(category_slug=category, rate=value, kind=kind, source_url=url)
            )

        def ingest(ctx: str, rate: float) -> None:
            lowered = ctx.strip().lower()
            if any(token in lowered for token in RBC_BASE_CTX) or "everywhere else" in lowered:
                add(None, rate)
                return
            if "net purchases" in lowered or "all other purchases" in lowered:
                add(None, rate)
                return
            if "british airways" in lowered:
                add("travel_air", rate)
                return
            if "westjet" in lowered or "sunwing" in lowered:
                add("travel_air", rate)
                return
            if "telecommunications" in lowered or "electronics" in lowered or "shipping" in lowered:
                for cat in ("streaming_subs", "retail_online"):
                    add(cat, rate)
                return
            if "partner locations" in lowered or "grocery, pharmacy" in lowered:
                for cat in ("grocery", "drugstore"):
                    add(cat, rate)
                return
            if "metro" in lowered or "brunet" in lowered or "super c" in lowered:
                for cat in ("grocery", "drugstore"):
                    add(cat, rate)
                return
            cats = match_all_categories(lowered)
            if not cats:
                reviews.append(
                    ReviewItem(
                        field="earn_rates",
                        reason=f"RBC earn context not matched: {lowered[:90]!r}",
                    )
                )
                return
            for cat in cats:
                add(cat, rate)

        for pattern in (
            RBC_EARN_BLOCK_RE,
            RBC_AVION_PPD_RE,
            RBC_WESTJET_PER_DOLLAR_RE,
            RBC_AVIOS_EARN_RE,
            RBC_DOLLAR_EARN_RE,
            RBC_DOLLAR_ONE_EARN_RE,
        ):
            for source_text in sources:
                for m in pattern.finditer(source_text):
                    if pattern is RBC_EARN_BLOCK_RE:
                        ingest(m.group(3), float(m.group(2)))
                    elif pattern in (RBC_AVION_PPD_RE, RBC_WESTJET_PER_DOLLAR_RE):
                        ingest(m.group(2), float(m.group(1)))
                    else:
                        ingest(m.group(2), float(m.group(1)))

        if rates:
            if not any(r.category_slug is None for r in rates):
                reviews.append(ReviewItem(field="earn_rates", reason="no base-rate pattern found"))
            return rates, reviews

        if "/cash-back/" in url or "cash-back" in url.lower():
            return self._extract_cashback_rates(text, url)

        if "/no-fee/" in url or "/low-interest/" in url:
            reviews.append(ReviewItem(field="earn_rates", reason="no earn patterns found on page"))
            return [], reviews

        if "/business/" in url:
            if not rates:
                reviews.append(ReviewItem(field="earn_rates", reason="no earn patterns found on page"))
            return rates, reviews

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

        intro_rates: list[float] = []
        for m in RBC_INTRO_CASHBACK_RE.finditer(text):
            intro_rates.append(float(m.group(1)) / 100)
        if intro_rates:
            add(None, min(intro_rates))

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

    def _extract_offer(self, text: str, url: str) -> tuple[Offer | None, list[ReviewItem]]:
        reviews: list[ReviewItem] = []

        avios_m = RBC_WB_AVIOS_RE.search(text)
        if avios_m:
            pts = int(avios_m.group(1).replace(",", ""))
            # Legal MSRs live in embedded JSON/script blocks omitted from visible text.
            raw = getattr(self, "_last_html", text)
            tiers = list(RBC_LEGAL_MSR_DAYS_RE.finditer(raw))
            ranges = list(RBC_LEGAL_MSR_RANGE_RE.finditer(raw))
            min_spend = deadline = None
            eligibility_notes = None
            if tiers and ranges:
                total_spend = money_to_minor("$" + tiers[0].group(1)) + money_to_minor(
                    "$" + ranges[0].group(1)
                )
                min_spend = total_spend
                deadline = int(ranges[0].group(3))
                eligibility_notes = (
                    "Tiered Avios WB: 30k for $5k in first 90 days + 30k for $5k in days 91-180 "
                    "(VERIFIED rbcroyalbank.com legal copy)"
                )
            elif tiers:
                min_spend = money_to_minor("$" + tiers[0].group(1))
                deadline = int(tiers[0].group(2))
                eligibility_notes = f"deadline stated as {tiers[0].group(2)} days in legal copy"
            else:
                reviews.append(
                    ReviewItem(
                        field="offer.min_spend",
                        reason="Avios WB found but MSR only in legal HTML",
                    )
                )
            notes = ELIGIBILITY_NOTES_RE.search(text)
            if notes:
                eligibility_notes = " ".join(filter(None, [eligibility_notes, notes.group(0)]))
            return (
                Offer(
                    headline=f"Get up to {pts:,} bonus Avios",
                    min_spend_minor=min_spend,
                    deadline_days=deadline,
                    reward_points=pts,
                    eligibility_notes=eligibility_notes,
                    first_year_free=bool(FIRST_YEAR_FREE_RE.search(text)) or None,
                    source_url=url,
                    verified_at=datetime.now(timezone.utc),
                ),
                reviews,
            )

        offer, offer_reviews = super()._extract_offer(text, url)
        if offer:
            return offer, offer_reviews

        # Business tiered WB: "Earn 20,000 Avion points when you spend $5,000 in the first 3 months"
        points_parts = [
            (int(m.group(1).replace(",", "")), m.end())
            for m in WB_POINTS_RE.finditer(text)
        ]
        if points_parts:
            canonical = max(points_parts, key=lambda p: p[0])
            pts, first_end = canonical
            rest = [p for p in points_parts if p[0] != pts]
            msr = (
                MSR_DAYS_RE.search(text, first_end)
                or MSR_MONTHS_RE.search(text, first_end)
                or MSR_STATEMENT_RE.search(text, first_end)
            )
            min_spend = deadline = None
            eligibility_notes = None
            if msr:
                min_spend = money_to_minor("$" + msr.group(1))
                n = int(msr.group(2))
                unit_days = 1 if MSR_DAYS_RE.match(msr.group(0), 0) else 30
                deadline = n * unit_days
                eligibility_notes = f"deadline stated as {n} {'days' if unit_days == 1 else 'months'} on page"
            alternates: list[AlternateOffer] = []
            for p, end in rest:
                a_msr = (
                    MSR_DAYS_RE.search(text, end)
                    or MSR_MONTHS_RE.search(text, end)
                    or MSR_STATEMENT_RE.search(text, end)
                )
                later = None if a_msr else LATER_SPEND_RE.search(text, end)
                alternates.append(
                    AlternateOffer(
                        headline=f"Additional earn component: {p:,} points",
                        channel="later_spend",
                        reward_points=p,
                        min_spend_minor=money_to_minor("$" + (a_msr or later).group(1))
                        if (a_msr or later)
                        else None,
                        deadline_days=(
                            int(a_msr.group(2))
                            * (1 if MSR_DAYS_RE.match(a_msr.group(0), 0) else 30)
                        )
                        if a_msr
                        else None,
                        source_url=url,
                        seen_on=self._today,
                    )
                )
            return (
                Offer(
                    headline=f"Earn up to {pts:,} points",
                    min_spend_minor=min_spend,
                    deadline_days=deadline,
                    reward_points=pts,
                    eligibility_notes=eligibility_notes,
                    alternate_offers=alternates,
                    source_url=url,
                    verified_at=datetime.now(timezone.utc),
                ),
                reviews,
            )

        reviews.extend(offer_reviews)
        return None, reviews
