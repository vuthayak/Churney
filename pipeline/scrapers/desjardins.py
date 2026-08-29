"""Desjardins (desjardins.com) scraper.

English consumer card pages are server-rendered with schema.org JSON-LD
(`FinancialProduct`) for fees/APR and AEM `<li>Category: X%</li>` rows for earn
breakdowns. BONUSDOLLARS cards earn `RewardKind.BONUS_DOLLARS` (1 BD = $1 redeem).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from churney.models import CardVersion, EarnRate, Offer, ReviewItem, RewardKind
from scrapers.common import match_all_categories, money_to_minor
from scrapers.generic import GenericIssuerScraper

_DSJ_CAT_RATE_RE = re.compile(
    r"<li>(?P<ctx>[^<:]+?):\s*(?:up to\s+)?(?P<rate>\d+(?:\.\d+)?)\s*%",
    re.I,
)
_DSJ_LI_FNOTE_RE = re.compile(
    r"<li>(?P<ctx>[^<:]+?):\s*(?:up to\s+)?(?P<rate>\d+(?:\.\d+)?)\s*%"
    r"\$\{fnote:(?:[^}]+\/)+(?P<fnote>[^}|]+)",
    re.I,
)
_DSJ_CAP_FNOTE_RE = re.compile(
    r'id="(?P<fnote>[^"]+)"[^>]*>The (?P<rate>\d+(?:\.\d+)?)% (?:Cash Back|BONUSDOLLARS) '
    r"rate will be applied to the first \$(?P<cap>[\d,]+)",
    re.I,
)
_DSJ_FNOTE_RE = re.compile(r"\$\{fnote:[^}]+\}")
_DSJ_TOKEN_RE = re.compile(
    r'data-token="pr1\.(?P<field>annualFee|interestFee|interestFeeCashAdvance)"[^>]*>'
    r"(?P<val>[^<]+)",
    re.I,
)
_SIGNUP_BONUS_RE = re.compile(r'"signupBonus"\s*:\s*"([^"]*)"')
_BD_SIGNUP_RE = re.compile(r"(\d+)\s*BONUSDOLLARS", re.I)
_CASH_SIGNUP_RE = re.compile(r"\$([\d,]+(?:\.\d+)?)\s*cash\s*back", re.I)

_DSJ_BASE_CTX = (
    "other purchase",
    "all other",
    "everyday",
    "everything else",
)

_DSJ_EXCLUDED_TAILS = {
    "bonusdollars-rewards-program",
    "cards-no-longer-available",
    "cash-advance",
    "compare-cards",
    "desjardins-odyssey-lounges",
    "disputing-credit-card-charge",
    "faq",
    "mobile-payment",
    "overdraft-transfers",
    "pay-installments",
    "statement-explained",
    "us-visa",
}


class DesjardinsScraper(GenericIssuerScraper):
    issuer_slug = "desjardins"
    network = None
    default_program = "cashback"
    program_tokens = (
        ("odyssey", "bonusdollars"),
        ("bonus visa", "bonusdollars"),
        ("bonus", "bonusdollars"),
        ("cash back", "cashback"),
        ("cash-back", "cashback"),
        ("flexi", "none"),
    )

    def parse_card(self, html: str, url: str):
        self._raw_html = html
        return super().parse_card(html, url)

    def _keep_link(self, path: str) -> bool:
        if not super()._keep_link(path):
            return False
        tail = path.rstrip("/").split("/")[-1].removesuffix(".html")
        return tail not in _DSJ_EXCLUDED_TAILS and "-application" not in tail

    def _html_blob(self) -> str:
        return getattr(self, "_raw_html", "")

    def _json_ld_product(self, html: str) -> dict | None:
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try:
                data = json.loads(m.group(1))
            except json.JSONDecodeError:
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") == "FinancialProduct":
                    return item
        return None

    def _token_value(self, field: str) -> str | None:
        for m in _DSJ_TOKEN_RE.finditer(self._html_blob()):
            if m.group("field").lower() == field.lower():
                return m.group("val").strip()
        return None

    def _parse_fee_minor(self, raw: str | None) -> int | None:
        if raw is None:
            return None
        cleaned = _DSJ_FNOTE_RE.sub("", raw).strip()
        if not cleaned or cleaned.lower() in ("none", "n/a", "no annual fee"):
            return 0
        if cleaned.isdigit():
            return int(cleaned) * 100
        return money_to_minor("$" + cleaned.replace(",", ""))

    def _extract_name(self, soup: BeautifulSoup, url: str) -> str:
        product = self._json_ld_product(self._html_blob())
        if product and product.get("name"):
            return str(product["name"]).strip()
        return super()._extract_name(soup, url)

    def _reward_kind_for(self, program_slug: str) -> RewardKind:
        if program_slug == "bonusdollars":
            return RewardKind.BONUS_DOLLARS
        return RewardKind.CASHBACK

    def _ingest_category(self, ctx: str, rate_pct: float, kind: RewardKind, add) -> list[ReviewItem]:
        reviews: list[ReviewItem] = []
        lowered = _DSJ_FNOTE_RE.sub("", ctx).strip().lower()
        value = round(rate_pct / 100, 6)
        if any(token in lowered for token in _DSJ_BASE_CTX):
            add(None, value, kind)
            return reviews
        if "alternative transportation" in lowered:
            add("transit_rideshare", value, kind)
            return reviews
        if "pre-authorized" in lowered or "preauthorized" in lowered:
            add("recurring_bills", value, kind)
            return reviews
        cats = match_all_categories(lowered)
        if not cats:
            reviews.append(
                ReviewItem(
                    field="earn_rates",
                    reason=f"Desjardins earn context not matched: {lowered[:90]!r}",
                )
            )
            return reviews
        for cat in cats:
            add(cat, value, kind)
        return reviews

    def _extract_version(self, text: str, url: str, review: list[ReviewItem]) -> CardVersion:
        product = self._json_ld_product(self._html_blob())
        annual_fee_minor = None
        purchase_apr = None
        cash_apr = None

        if product:
            price = (product.get("offers") or {}).get("price")
            annual_fee_minor = self._parse_fee_minor(str(price) if price is not None else None)
            apr_raw = product.get("interestRate") or product.get("annualPercentageRate")
            if apr_raw:
                m = re.search(r"(\d+(?:\.\d+)?)", str(apr_raw))
                purchase_apr = float(m.group(1)) if m else None
            for prop in product.get("additionalProperty") or []:
                if prop.get("name") == "Cash Advances" and prop.get("value"):
                    m = re.search(r"(\d+(?:\.\d+)?)\s*%", str(prop["value"]))
                    if m:
                        cash_apr = float(m.group(1))

        if annual_fee_minor is None:
            annual_fee_minor = self._parse_fee_minor(self._token_value("annualFee"))
        if purchase_apr is None:
            tok = self._token_value("interestFee")
            if tok:
                m = re.search(r"(\d+(?:\.\d+)?)", tok)
                purchase_apr = float(m.group(1)) if m else None
        if cash_apr is None:
            tok = self._token_value("interestFeeCashAdvance")
            if tok:
                m = re.search(r"(\d+(?:\.\d+)?)", tok)
                cash_apr = float(m.group(1)) if m else None

        if annual_fee_minor is None:
            review.append(ReviewItem(field="annual_fee_minor", reason="fee not found in JSON-LD or tokens"))
        if purchase_apr is None:
            review.append(ReviewItem(field="purchase_apr", reason="purchase APR not found in JSON-LD or tokens"))

        review.append(
            ReviewItem(
                field="fx_fee_pct",
                reason="per-card FX fee not stated; most CA cards 2.5% [VERIFY]",
            )
        )

        return CardVersion(
            valid_from=self._today,
            annual_fee_minor=annual_fee_minor,
            extra_card_fee_minor=None,
            fx_fee_pct=None,
            purchase_apr=purchase_apr,
            cash_apr=cash_apr,
            source_url=url,
        )

    def _extract_earn_rates(self, text: str, url: str) -> tuple[list[EarnRate], list[ReviewItem]]:
        if "flexi" in url:
            return [], [ReviewItem(field="earn_rates", reason="no rewards on Flexi low-rate card")]

        program_slug = self._classify_program(self._extract_name(BeautifulSoup(self._html_blob(), "lxml"), url))
        if program_slug is None:
            program_slug = self.default_program
        kind = self._reward_kind_for(program_slug)

        rates: list[EarnRate] = []
        reviews: list[ReviewItem] = []
        seen: set[tuple[str | None, float, RewardKind]] = set()
        html = self._html_blob()

        def add(category, value: float, reward_kind: RewardKind) -> None:
            key = (category, value, reward_kind)
            if key in seen:
                return
            seen.add(key)
            rates.append(
                EarnRate(category_slug=category, rate=value, kind=reward_kind, source_url=url)
            )

        for m in _DSJ_CAT_RATE_RE.finditer(html):
            ctx = m.group("ctx")
            if any(skip in ctx.lower() for skip in ("fuel purchase", "rental rate", "off ")):
                continue
            reviews.extend(self._ingest_category(ctx, float(m.group("rate")), kind, add))

        if not rates:
            reviews.append(ReviewItem(field="earn_rates", reason="no category-rate list found on page"))
        elif not any(r.category_slug is None for r in rates):
            reviews.append(ReviewItem(field="earn_rates", reason="no base-rate pattern found"))
        self._apply_annual_caps(html, rates)
        return rates, reviews

    def _footnote_caps(self, html: str) -> dict[str, int]:
        caps: dict[str, int] = {}
        for m in _DSJ_CAP_FNOTE_RE.finditer(html):
            minor = money_to_minor("$" + m.group("cap"))
            if minor is not None:
                caps[m.group("fnote").lower()] = minor
        return caps

    def _apply_annual_caps(self, html: str, rates: list[EarnRate]) -> None:
        """Attach annual spend caps from linked legal footnotes to boosted earn rows."""
        fnote_caps = self._footnote_caps(html)
        if not fnote_caps:
            return
        for m in _DSJ_LI_FNOTE_RE.finditer(html):
            fnote_id = m.group("fnote").lower()
            cap_minor = fnote_caps.get(fnote_id)
            if cap_minor is None:
                continue
            ctx = _DSJ_FNOTE_RE.sub("", m.group("ctx")).strip().lower()
            rate_val = round(float(m.group("rate")) / 100, 6)
            cats = match_all_categories(ctx)
            if not cats:
                continue
            for earn in rates:
                if earn.category_slug in cats and earn.rate == rate_val:
                    earn.cap_amount_minor = cap_minor
                    earn.cap_period = "annual"

    def _extract_offer(self, text: str, url: str) -> tuple[Offer | None, list[ReviewItem]]:
        reviews: list[ReviewItem] = []
        raw = self._html_blob()
        signup_m = _SIGNUP_BONUS_RE.search(raw)
        if not signup_m:
            return None, reviews

        signup = signup_m.group(1).strip()
        if not signup:
            return None, reviews

        bd_m = _BD_SIGNUP_RE.search(signup)
        if bd_m:
            amount = int(bd_m.group(1))
            msr_note = self._signup_msr_review(text)
            if msr_note:
                reviews.append(msr_note)
            return (
                Offer(
                    headline=f"Earn {amount:,} BONUSDOLLARS",
                    reward_cashback_minor=amount * 100,
                    eligibility_notes="1 BONUSDOLLAR = $1 redeem per desjardins.com program rules",
                    source_url=url,
                    verified_at=datetime.now(timezone.utc),
                ),
                reviews,
            )

        cash_m = _CASH_SIGNUP_RE.search(signup)
        if cash_m:
            amount_minor = money_to_minor("$" + cash_m.group(1))
            msr_note = self._signup_msr_review(text)
            if msr_note:
                reviews.append(msr_note)
            return (
                Offer(
                    headline=signup,
                    reward_cashback_minor=amount_minor,
                    source_url=url,
                    verified_at=datetime.now(timezone.utc),
                ),
                reviews,
            )

        reviews.append(
            ReviewItem(field="offers", reason=f"unparsed signupBonus metadata: {signup!r}")
        )
        return None, reviews

    def _signup_msr_review(self, text: str) -> ReviewItem | None:
        """Return a review item when signup metadata lacks a parseable MSR on-page."""
        from scrapers.common import MSR_DAYS_RE, MSR_MONTHS_RE, MSR_STATEMENT_RE

        if (
            MSR_DAYS_RE.search(text)
            or MSR_MONTHS_RE.search(text)
            or MSR_STATEMENT_RE.search(text)
        ):
            return ReviewItem(
                field="offer.min_spend",
                reason="signup MSR pattern found on page but not yet parsed from Desjardins legal copy",
            )
        return ReviewItem(
            field="offer.min_spend",
            reason=(
                "signup bonus amount from page metadata; no minimum spend stated on "
                "desjardins.com card page - VERIFIED"
            ),
        )
