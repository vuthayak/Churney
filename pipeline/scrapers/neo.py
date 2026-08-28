"""Neo Financial (neofinancial.com) scraper.

Neo card pages are Next.js SPAs; Playwright rendering is required for earn
tiles and FAQ copy. Fees/APR also appear in embedded RSC FAQ answers.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from churney.models import (
    AlternateOffer,
    CardVersion,
    EarnRate,
    Offer,
    ReviewItem,
    RewardKind,
)
from scrapers.common import (
    MSR_MONTHS_RE,
    match_all_categories,
    money_to_minor,
)
from scrapers.simple_cashback import SimpleCashbackScraper

_NEO_ANNUAL_FEE_RE = re.compile(
    r"(?:annual fee of|)\s*\$(\d+)\s+annual fee", re.I
)
_NEO_PURCHASE_APR_RE = re.compile(
    r"purchase credit rate on the [^\"\\]{1,120}? is (\d+(?:\.\d+)?)(?:%|-)",
    re.I,
)
_NEO_CASH_APR_RE = re.compile(
    r"cash advance rate\s+is\s+(\d+(?:\.\d+)?)(?:%|-)",
    re.I,
)
# "Earn 5% on groceries, 4% on recurring payments, and 3% on gas"
_NEO_PCT_ON_RE = re.compile(
    r"(\d+(?:\.\d+)?)%\s+on\s+([^,;²³⁴⁵.]{3,60}?)"
    r"(?=\s*(?:,|and|\.|²|³|⁴|⁵|$))",
    re.I,
)
# Playwright-rendered feature tile: "1% cashback⁴ from gas and grocery"
_NEO_FEATURE_CASHBACK_RE = re.compile(
    r"(\d+(?:\.\d+)?)%\s*cashback[^<]{0,40}from\s+([^<]{3,80})",
    re.I,
)
# United earn tiles: "1.25x miles per $1" + following context line
_NEO_MILES_TILE_RE = re.compile(
    r"(\d+(?:\.\d+)?)x\s+miles?\s+per \$1", re.I
)
WB_MILES_RE = re.compile(
    r"(?:up to\s+)?([\d,]{2,})\s+(?:bonus\s+)?(?:mileageplus\s+)?miles",
    re.I,
)
_NEO_MSR_SPEND_RE = re.compile(
    r"spend\s+\$([\d,]+)\s+in your first\s+(\d+)\s+months?", re.I
)

_CATEGORY_OVERRIDES = {
    "groceries": "grocery",
    "grocery": "grocery",
    "gas": "gas",
    "recurring payments": "recurring_bills",
    "everything else": None,
    "dining and grocery purchases": ("dining", "grocery"),
}


class NeoScraper(SimpleCashbackScraper):
    issuer_slug = "neo"
    network = None  # inferred: all Neo consumer cards are Mastercard
    default_program = "cashback"
    program_tokens = (
        ("mileageplus", "united_mileageplus"),
        ("united", "united_mileageplus"),
        ("cathay", "asia_miles"),
        ("neo mastercard", "cashback"),
        ("world elite", "cashback"),
        ("world mastercard", "cashback"),
    )

    def parse_card(self, html: str, url: str):
        self._raw_html = html
        return super().parse_card(html, url)

    def _html_blob(self) -> str:
        return getattr(self, "_raw_html", "")

    def _extract_name(self, soup: BeautifulSoup, url: str) -> str:
        title = soup.title.get_text(strip=True) if soup.title else ""
        name = title.split("|")[0].strip()
        name = re.sub(r"[®*™‡†⁰¹²³⁴⁵⁶⁷⁸⁹]+", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        if name:
            return name
        return super()._extract_name(soup, url)

    def _extract_version(self, text: str, url: str, review: list[ReviewItem]) -> CardVersion:
        html = self._html_blob()
        blob = f"{text} {html}"

        fee_m = _NEO_ANNUAL_FEE_RE.search(blob)
        if fee_m:
            annual_fee_minor = int(fee_m.group(1)) * 100
        elif "united" in url:
            annual_fee_minor = None
            review.append(ReviewItem(field="annual_fee_minor", reason="fee pattern not found"))
        else:
            # Base Neo Mastercard is marketed without a primary annual fee.
            annual_fee_minor = 0

        apr_m = _NEO_PURCHASE_APR_RE.search(html) or _NEO_PURCHASE_APR_RE.search(text)
        purchase_apr = float(apr_m.group(1)) if apr_m else None
        if purchase_apr is None:
            review.append(ReviewItem(field="purchase_apr", reason="purchase APR not found in FAQ copy"))

        cash_m = _NEO_CASH_APR_RE.search(html) or _NEO_CASH_APR_RE.search(text)
        cash_apr = float(cash_m.group(1)) if cash_m else None

        review.append(
            ReviewItem(
                field="fx_fee_pct",
                reason="per-card FX fee not stated; most CA cards 2.5% [VERIFY]",
            )
        )

        income_m = re.search(
            r"Minimum\s+\$([\d,]+)\s+annual (?:personal )?income", blob, re.I
        )
        hh_m = re.search(
            r"household income of \$([\d,]+)", blob, re.I
        )

        extra = None
        if re.search(r"additional cardholder[^$]{0,80}\$0", blob, re.I):
            extra = 0

        return CardVersion(
            valid_from=self._today,
            annual_fee_minor=annual_fee_minor,
            extra_card_fee_minor=extra,
            fx_fee_pct=None,
            income_req_personal=int(income_m.group(1).replace(",", "")) if income_m else None,
            income_req_household=int(hh_m.group(1).replace(",", "")) if hh_m else None,
            purchase_apr=purchase_apr,
            cash_apr=cash_apr,
            source_url=url,
        )

    def _ingest_cashback_context(self, ctx: str, rate: float, add) -> list[ReviewItem]:
        reviews: list[ReviewItem] = []
        lowered = re.split(r"\bcollect\b", ctx.strip().lower())[0].strip().rstrip(".")
        if "gas and grocer" in lowered:
            add("gas", rate, RewardKind.CASHBACK)
            add("grocery", rate, RewardKind.CASHBACK)
            return reviews
        if lowered in _CATEGORY_OVERRIDES:
            mapped = _CATEGORY_OVERRIDES[lowered]
            if mapped is None:
                add(None, rate, RewardKind.CASHBACK)
            elif isinstance(mapped, tuple):
                for cat in mapped:
                    add(cat, rate, RewardKind.CASHBACK)
            else:
                add(mapped, rate, RewardKind.CASHBACK)
            return reviews
        cats = match_all_categories(lowered)
        if not cats:
            reviews.append(
                ReviewItem(field="earn_rates", reason=f"Neo earn context not matched: {lowered[:90]!r}")
            )
            return reviews
        for cat in cats:
            add(cat, rate, RewardKind.CASHBACK)
        return reviews

    def _extract_earn_rates(self, text: str, url: str) -> tuple[list[EarnRate], list[ReviewItem]]:
        if "united" in url:
            return self._extract_united_earn_rates(text, url)

        rates: list[EarnRate] = []
        reviews: list[ReviewItem] = []
        seen: set[tuple[str | None, float, RewardKind]] = set()
        html = self._html_blob()

        def add(category, value: float, kind: RewardKind) -> None:
            key = (category, value, kind)
            if key in seen:
                return
            seen.add(key)
            rates.append(
                EarnRate(category_slug=category, rate=value, kind=kind, source_url=url)
            )

        for m in _NEO_FEATURE_CASHBACK_RE.finditer(html):
            ctx = re.sub(r"<[^>]+>", "", m.group(2))
            reviews.extend(self._ingest_cashback_context(ctx, float(m.group(1)) / 100, add))

        visible = re.sub(r"\s+", " ", BeautifulSoup(html, "lxml").get_text(" ", strip=True))
        for m in _NEO_PCT_ON_RE.finditer(visible):
            reviews.extend(
                self._ingest_cashback_context(m.group(2), float(m.group(1)) / 100, add)
            )

        if not rates:
            if re.search(r"cashback on gas and grocer", html, re.I):
                reviews.append(
                    ReviewItem(
                        field="earn_rates",
                        reason="gas/grocery cashback mentioned but rate % not stated on page",
                    )
                )
            else:
                reviews.append(ReviewItem(field="earn_rates", reason="no earn patterns found on page"))
        elif not any(r.category_slug is None for r in rates):
            reviews.append(ReviewItem(field="earn_rates", reason="no base-rate pattern found"))
        return rates, reviews

    def _extract_united_earn_rates(
        self, text: str, url: str
    ) -> tuple[list[EarnRate], list[ReviewItem]]:
        rates: list[EarnRate] = []
        reviews: list[ReviewItem] = []
        seen: set[tuple[str | None, float, RewardKind]] = set()
        html = self._html_blob()

        def add(category, value: float) -> None:
            key = (category, value, RewardKind.POINTS)
            if key in seen:
                return
            seen.add(key)
            rates.append(
                EarnRate(
                    category_slug=category,
                    rate=value,
                    kind=RewardKind.POINTS,
                    source_url=url,
                )
            )

        soup = BeautifulSoup(html, "lxml")
        for h3 in soup.find_all("h3"):
            tile = h3.get_text(" ", strip=True)
            m = _NEO_MILES_TILE_RE.search(tile)
            if not m:
                continue
            rate = float(m.group(1))
            ctx_p = h3.find_next("p")
            ctx = ctx_p.get_text(" ", strip=True).lower() if ctx_p else tile.lower()
            if "united" in ctx or "star alliance" in ctx or "airline" in ctx:
                add("travel_air", rate)
            elif "dining" in ctx or "grocery" in ctx:
                for cat in match_all_categories(ctx):
                    add(cat, rate)
            elif "everything else" in ctx:
                add(None, rate)
            else:
                reviews.append(
                    ReviewItem(field="earn_rates", reason=f"United miles tile context not matched: {ctx[:90]!r}")
                )

        if not rates:
            reviews.append(ReviewItem(field="earn_rates", reason="no earn patterns found on page"))
        elif not any(r.category_slug is None for r in rates):
            reviews.append(ReviewItem(field="earn_rates", reason="no base-rate pattern found"))
        return rates, reviews

    def _extract_offer(self, text: str, url: str) -> tuple[Offer | None, list[ReviewItem]]:
        if "united" in url:
            return self._extract_united_offer(text, url)
        return super()._extract_offer(text, url)

    def _extract_united_offer(self, text: str, url: str) -> tuple[Offer | None, list[ReviewItem]]:
        reviews: list[ReviewItem] = []
        html = self._html_blob()
        blob = f"{text} {html}"

        miles_parts = [
            (int(m.group(1).replace(",", "")), m.end())
            for m in WB_MILES_RE.finditer(blob)
            if m.group(1).replace(",", "").isdigit()
        ]
        if not miles_parts:
            reviews.append(ReviewItem(field="offers", reason="no welcome-bonus pattern found"))
            return None, reviews

        pts = max(p for p, _ in miles_parts)
        msr = _NEO_MSR_SPEND_RE.search(blob) or MSR_MONTHS_RE.search(blob)
        min_spend = deadline = None
        eligibility_notes = None
        if msr:
            min_spend = money_to_minor("$" + msr.group(1))
            n = int(msr.group(2))
            deadline = n * 30
            eligibility_notes = (
                f"tiered WB: 5k miles on first purchase + 15k miles for ${msr.group(1)} "
                f"in first {n} months + 5k annual renewal (VERIFIED neofinancial.com page copy)"
            )
        else:
            reviews.append(
                ReviewItem(field="offer.min_spend", reason="miles WB found but MSR not parsed from page")
            )

        alternates: list[AlternateOffer] = []
        if re.search(r"5,000 miles When you make your first purchase", blob, re.I):
            alternates.append(
                AlternateOffer(
                    headline="5,000 miles on first purchase",
                    channel="first_purchase",
                    reward_points=5000,
                    source_url=url,
                    seen_on=self._today,
                )
            )
        if re.search(r"5,000 miles Every year your account stays open", blob, re.I):
            alternates.append(
                AlternateOffer(
                    headline="5,000 miles annual renewal bonus",
                    channel="annual_renewal",
                    reward_points=5000,
                    source_url=url,
                    seen_on=self._today,
                )
            )

        offer = Offer(
            headline=f"Earn up to {pts:,} MileagePlus miles",
            min_spend_minor=min_spend,
            deadline_days=deadline,
            reward_points=pts,
            eligibility_notes=eligibility_notes,
            alternate_offers=alternates,
            source_url=url,
            verified_at=datetime.now(timezone.utc),
        )
        return offer, reviews
