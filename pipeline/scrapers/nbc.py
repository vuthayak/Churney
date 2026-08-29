"""National Bank of Canada (nbc.ca) scraper.

NBC card pages are Angular/SPA shells, but each detail page embeds a
`Websites.Product.Core.setProductMap(JSON.parse(...))` blob with fees, APRs,
and product metadata. Earn breakdowns also appear in static legal/accordion HTML
(`Gas and electric vehicle charging: <b>2</b> points per dollar ...`).
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from churney.models import CardVersion, EarnRate, ReviewItem, RewardKind
from scrapers.common import (
    MSR_DAYS_RE,
    MSR_MONTHS_RE,
    WB_POINTS_RE,
    match_all_categories,
    money_to_minor,
)
from scrapers.generic import GenericIssuerScraper

# Escaped JSON delimiter used inside setProductMap (three backslashes + x22).
_NBC_Q = r"\\\\\\x22"
_NBC_SEP = _NBC_Q + ":" + _NBC_Q

# Fields read from the embedded product map (parallel arrays per page).
_PRODUCT_FIELDS = (
    "nomProduit.en",
    "urlPage.en",
    "productPricing.AF_CRD.productPricingValue.en",
    "productPricing.AF_CRD_SUP.productPricingValue.en",
    "productPricing.TX_INT.productPricingValue.en",
    "productPricing.TX_TRF.productPricingValue.en",
    "accroche.en",
    "categoriePrincipale.en",
)

# Legal accordion: "Gas and electric vehicle charging: <b>2</b> points per dollar ..."
_NBC_LEGAL_POINTS_RE = re.compile(
    r"([^:<>]{3,90}?):\s*<b>\s*(\d+(?:\.\d+)?)\s*</b>\s*points?\s+per\s+dollar",
    re.I,
)
_NBC_LEGAL_POINTS_PER_AMOUNT_RE = re.compile(
    r"([^:<>]{3,90}?):\s*<b>\s*(\d+(?:\.\d+)?)\s*</b>\s*points?\s+per\s*<b>\s*\$(\d+(?:\.\d+)?)\s*</b>",
    re.I,
)
# Marketing tiles: "up to 5 points per dollar spent"
_NBC_POINTS_PPD_RE = re.compile(
    r"(?:up to\s+)?(\d+(?:\.\d+)?)\s+points?\s+per\s+dollar",
    re.I,
)
_NBC_CASHBACK_PCT_RE = re.compile(
    r"(?:up to\s+)?(\d+(?:\.\d+)?)\s*%\s*cash\s*back",
    re.I,
)
_NBC_CASHBACK_CATEGORY_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*%\s*cash\s*back\s+on\s+([^.;]{3,80}?)"
    r"(?=\s+\d|\s+and\s+|\s+apply|\s+annual|\s+for\s+the|$)",
    re.I,
)

_NBC_BASE_CTX = (
    "other purchase",
    "all other",
    "everyday",
    "everything else",
    "everywhere else",
    "all purchase",
    "other eligible",
)


class NbcScraper(GenericIssuerScraper):
    issuer_slug = "nbc"
    network = None  # inferred: all NBC consumer cards are Mastercard
    default_program = "nbc_rewards"
    program_tokens = (
        ("echo", "cashback"),
        ("cashback", "cashback"),
        ("mycredit", "cashback"),
        ("my-credit", "cashback"),
        ("syncro", "nbc_rewards"),
        ("allure", "nbc_rewards"),
        ("mc1", "nbc_rewards"),
        ("world elite", "nbc_rewards"),
        ("world", "nbc_rewards"),
        ("platinum", "nbc_rewards"),
    )

    def parse_card(self, html: str, url: str):
        self._raw_html = html
        return super().parse_card(html, url)

    def _html_blob(self) -> str:
        return getattr(self, "_raw_html", "")

    def _decode_nbc_val(self, raw: str) -> str:
        s = raw.replace("\\/", "/")
        try:
            return s.encode("utf-8").decode("unicode_escape")
        except UnicodeDecodeError:
            return s

    def _extract_product_map(self, html: str) -> dict[str, list[str]]:
        fields: dict[str, list[str]] = {}
        for key in _PRODUCT_FIELDS:
            pat = re.compile(
                rf"{re.escape(key)}{_NBC_SEP}(?P<val>(?:[^\\]|\\.)+?){_NBC_Q}"
            )
            fields[key] = [self._decode_nbc_val(m.group("val")) for m in pat.finditer(html)]
        return fields

    def _product_index(self, fields: dict[str, list[str]], url: str) -> int | None:
        slug = urlparse(url).path.rstrip("/").split("/")[-1].removesuffix(".html")
        urls = fields.get("urlPage.en", [])
        for i, page_url in enumerate(urls):
            if slug in page_url:
                return i
        return None

    def _field_at(self, fields: dict[str, list[str]], key: str, idx: int | None) -> str | None:
        if idx is None:
            return None
        vals = fields.get(key, [])
        return vals[idx] if idx < len(vals) else None

    def _extract_name(self, soup: BeautifulSoup, url: str) -> str:
        fields = self._extract_product_map(self._html_blob())
        idx = self._product_index(fields, url)
        mapped = self._field_at(fields, "nomProduit.en", idx)
        if mapped:
            return mapped
        return super()._extract_name(soup, url)

    def _extract_version(self, text: str, url: str, review: list[ReviewItem]) -> CardVersion:
        fields = self._extract_product_map(self._html_blob())
        idx = self._product_index(fields, url)

        annual_raw = self._field_at(fields, "productPricing.AF_CRD.productPricingValue.en", idx)
        if annual_raw is not None and annual_raw.isdigit():
            annual_fee_minor = int(annual_raw) * 100
        else:
            annual_fee_minor = None
            review.append(ReviewItem(field="annual_fee_minor", reason="fee not found in product map"))

        supp_raw = self._field_at(fields, "productPricing.AF_CRD_SUP.productPricingValue.en", idx)
        extra = int(supp_raw) * 100 if supp_raw and supp_raw.isdigit() else None

        apr_raw = self._field_at(fields, "productPricing.TX_INT.productPricingValue.en", idx)
        purchase_apr = float(apr_raw) if apr_raw else None
        if purchase_apr is None:
            review.append(ReviewItem(field="purchase_apr", reason="purchase APR not found in product map"))

        cash_raw = self._field_at(fields, "productPricing.TX_TRF.productPricingValue.en", idx)
        cash_apr = float(cash_raw) if cash_raw else None

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
            fx_fee_pct=None,
            purchase_apr=purchase_apr,
            cash_apr=cash_apr,
            source_url=url,
        )

    def _ingest_points_context(self, ctx: str, rate: float, add) -> list[ReviewItem]:
        reviews: list[ReviewItem] = []
        lowered = ctx.strip().lower()
        if any(token in lowered for token in _NBC_BASE_CTX):
            add(None, rate, RewardKind.POINTS)
            return reviews
        if "recurring bill" in lowered or "pre-authorized" in lowered or "preauthorized" in lowered:
            add("recurring_bills", rate, RewardKind.POINTS)
            return reviews
        if "à la carte travel" in lowered or "a la carte travel" in lowered:
            add("travel_air", rate, RewardKind.POINTS)
            return reviews
        if "restaurant" in lowered or "dining" in lowered:
            add("dining", rate, RewardKind.POINTS)
            return reviews
        if "online" in lowered:
            add("retail_online", rate, RewardKind.POINTS)
            return reviews
        cats = match_all_categories(lowered)
        if not cats:
            reviews.append(
                ReviewItem(field="earn_rates", reason=f"NBC earn context not matched: {lowered[:90]!r}")
            )
            return reviews
        for cat in cats:
            add(cat, rate, RewardKind.POINTS)
        return reviews

    def _extract_earn_rates(self, text: str, url: str) -> tuple[list[EarnRate], list[ReviewItem]]:
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

        is_cashback = any(tok in url.lower() for tok in ("echo", "my-credit", "cashback"))

        for m in _NBC_LEGAL_POINTS_RE.finditer(html):
            ctx, rate_s = m.group(1), m.group(2)
            ctx = re.sub(r"<[^>]+>", "", ctx)
            reviews.extend(self._ingest_points_context(ctx, float(rate_s), add))

        for m in _NBC_LEGAL_POINTS_PER_AMOUNT_RE.finditer(html):
            ctx, points_s, dollars_s = m.group(1), m.group(2), m.group(3)
            ctx = re.sub(r"<[^>]+>", "", ctx)
            rate = float(points_s) / float(dollars_s)
            reviews.extend(self._ingest_points_context(ctx, rate, add))

        if not rates:
            ppd = _NBC_POINTS_PPD_RE.search(html) or _NBC_POINTS_PPD_RE.search(text)
            if ppd and not is_cashback:
                add(None, float(ppd.group(1)), RewardKind.POINTS)

        if is_cashback or "cashback" in html.lower()[:8000]:
            base_m = _NBC_CASHBACK_PCT_RE.search(html) or _NBC_CASHBACK_PCT_RE.search(text)
            if base_m:
                add(None, float(base_m.group(1)) / 100, RewardKind.CASHBACK)
            for m in _NBC_CASHBACK_CATEGORY_RE.finditer(html):
                ctx = m.group(2).lower()
                if any(token in ctx for token in _NBC_BASE_CTX):
                    continue
                cats = match_all_categories(ctx)
                value = float(m.group(1)) / 100
                if not cats:
                    continue
                for cat in cats:
                    add(cat, value, RewardKind.CASHBACK)

        if not rates:
            reviews.append(ReviewItem(field="earn_rates", reason="no earn patterns found on page"))
        elif not any(r.category_slug is None for r in rates):
            reviews.append(ReviewItem(field="earn_rates", reason="no base-rate pattern found"))
        return rates, reviews

    def _extract_offer(self, text: str, url: str):
        offer, reviews = super()._extract_offer(text, url)
        if offer:
            return offer, reviews

        points_parts = [
            (int(m.group(1).replace(",", "")), m.end())
            for m in WB_POINTS_RE.finditer(text)
        ]
        if not points_parts:
            return None, reviews

        canonical = max(points_parts, key=lambda p: p[0])
        pts, first_end = canonical
        msr = (
            MSR_DAYS_RE.search(text, first_end)
            or MSR_MONTHS_RE.search(text, first_end)
        )
        min_spend = deadline = None
        eligibility_notes = None
        if msr:
            min_spend = money_to_minor("$" + msr.group(1))
            n = int(msr.group(2))
            unit_days = 1 if MSR_DAYS_RE.match(msr.group(0), 0) else 30
            deadline = n * unit_days
            eligibility_notes = (
                f"deadline stated as {n} {'days' if unit_days == 1 else 'months'} in legal copy"
            )
        else:
            reviews.append(
                ReviewItem(field="offer.min_spend", reason="WB points found but MSR not parsed from page")
            )

        from datetime import datetime, timezone

        from churney.models import Offer

        return (
            Offer(
                headline=f"Earn up to {pts:,} reward points",
                min_spend_minor=min_spend,
                deadline_days=deadline,
                reward_points=pts,
                eligibility_notes=eligibility_notes,
                source_url=url,
                verified_at=datetime.now(timezone.utc),
            ),
            reviews,
        )
