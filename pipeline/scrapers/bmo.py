"""BMO Bank of Montreal scraper.

BMO card pages are Next.js shells (~2.5 MB HTML). Many expose a schema.org
Product JSON-LD block with annual fee (`offers.price`) and purchase APR
(`offers.@graph[0].annualPercentageRate`). Cards without top-level Product
JSON-LD still embed the same fields deeper in the page JSON. Earn copy uses
BMO-specific phrasing ("5 points for every $1 you spend on ...").
"""

from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from churney.models import CardVersion, EarnRate, ReviewItem, RewardKind
from scrapers.common import (
    CASH_APR_RE,
    match_all_categories,
    money_to_minor,
)
from scrapers.generic import GenericIssuerScraper

_BMO_DOLLAR_FEE_RE = re.compile(r"\$(\d+(?:\.\d{2})?)\s+annual fee", re.I)
_BMO_EMBEDDED_PRICE_RE = re.compile(r'"price"\s*:\s*"(\d+(?:\.\d{2})?)"')
_BMO_EMBEDDED_APR_RE = re.compile(r'"annualPercentageRate"\s*:\s*"(\d+(?:\.\d+)?)"')
_BMO_POINTS_EARN_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s+(?:viporter\s+)?points?\s+for every\s+\$1\s+"
    r"(?:you\s+)?(?:spend(?:ing)?|spent)\s+(?:on|at)\s+"
    r"([^.]{3,120}?)(?=\s+\d|\s+Earn\s+\d|\s+Annual|\s+Apply|\s+Get|\s+\.|$)",
    re.I,
)
_BMO_BASE_CTX = (
    "everything else",
    "all other",
    "everywhere else",
    "all purchases",
    "everyday",
    "other eligible",
    "other purchase",
)


class BmoScraper(GenericIssuerScraper):
    issuer_slug = "bmo"
    network = None
    default_program = "bmo_rewards"
    program_tokens = (
        ("viporter", "viporter"),
        ("cashback", "cashback"),
        ("cash back", "cashback"),
        ("blue rewards", "bmo_rewards"),
        ("eclipse", "bmo_rewards"),
        ("ascend", "bmo_rewards"),
        ("preferred rate", "none"),
        ("u.s. dollar", "none"),
        ("us dollar", "none"),
        ("prepaid", "none"),
    )

    def parse_card(self, html: str, url: str):
        self._raw_html = html
        return super().parse_card(html, url)

    def _html_blob(self) -> str:
        return getattr(self, "_raw_html", "")

    def _product_ld(self, html: str) -> dict | None:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(tag.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(data, dict) and data.get("@type") == "Product":
                return data
        return None

    def _credit_card_node(self, product: dict) -> dict:
        offers = product.get("offers") or {}
        graph = offers.get("@graph") or []
        for node in graph:
            if isinstance(node, dict) and node.get("@type") == "CreditCard":
                return node
        return graph[0] if graph and isinstance(graph[0], dict) else {}

    def _extract_name(self, soup: BeautifulSoup, url: str) -> str:
        product = self._product_ld(self._html_blob())
        if product and product.get("name"):
            return str(product["name"]).strip()
        raw = soup.find("h1")
        name = re.sub(r"\s+", " ", raw.get_text(strip=True) if raw else "")
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        name = re.sub(r"[®*™‡†]+", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        if not name:
            raise ValueError(f"no card name on {url}")
        return name

    def _extract_version(self, text: str, url: str, review: list[ReviewItem]) -> CardVersion:
        html = self._html_blob()
        product = self._product_ld(html)
        annual_fee_minor = purchase_apr = cash_apr = None

        if product:
            offers = product.get("offers") or {}
            price = offers.get("price")
            if price is not None and str(price).replace(".", "", 1).isdigit():
                annual_fee_minor = money_to_minor("$" + str(price))
            cc = self._credit_card_node(product)
            apr_raw = cc.get("annualPercentageRate")
            if apr_raw:
                purchase_apr = float(apr_raw)

        if annual_fee_minor is None:
            fee_m = _BMO_DOLLAR_FEE_RE.search(text) or _BMO_DOLLAR_FEE_RE.search(html)
            if fee_m:
                annual_fee_minor = money_to_minor("$" + fee_m.group(1))
            else:
                price_m = _BMO_EMBEDDED_PRICE_RE.search(html)
                if price_m:
                    annual_fee_minor = money_to_minor("$" + price_m.group(1))

        if purchase_apr is None:
            apr_m = _BMO_EMBEDDED_APR_RE.search(html)
            if apr_m:
                purchase_apr = float(apr_m.group(1))

        if purchase_apr is None:
            from scrapers.common import PURCHASE_APR_RE

            page_apr = PURCHASE_APR_RE.search(text)
            if page_apr:
                purchase_apr = float(page_apr.group(1))

        cash_m = CASH_APR_RE.search(text)
        if cash_m:
            cash_apr = float(cash_m.group(1) or cash_m.group(2))

        if annual_fee_minor is None:
            review.append(ReviewItem(field="annual_fee_minor", reason="fee pattern not found"))
        if purchase_apr is None:
            review.append(ReviewItem(field="purchase_apr", reason="purchase APR pattern not found"))

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

        def ingest(ctx: str, rate: float, kind: RewardKind = RewardKind.POINTS) -> None:
            lowered = ctx.strip().lower()
            if any(token in lowered for token in _BMO_BASE_CTX):
                add(None, rate, kind)
                return
            if "blue rewards partners" in lowered or "participating blue rewards" in lowered:
                add("retail_online", rate, kind)
                return
            if "porter" in lowered or "viporter" in lowered:
                add("travel_air", rate, kind)
                return
            cats = match_all_categories(lowered)
            if not cats:
                reviews.append(
                    ReviewItem(
                        field="earn_rates",
                        reason=f"BMO earn context not matched: {lowered[:90]!r}",
                    )
                )
                return
            for cat in cats:
                add(cat, rate, kind)

        for source in (html, text):
            for m in _BMO_POINTS_EARN_RE.finditer(source):
                ingest(m.group(2), float(m.group(1)))

        if rates:
            if not any(r.category_slug is None for r in rates):
                reviews.append(ReviewItem(field="earn_rates", reason="no base-rate pattern found"))
            return rates, reviews

        return super()._extract_earn_rates(text, url)
