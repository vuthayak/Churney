"""Brim Financial scraper.

Brim's consumer lineup (Brim Mastercard and Brim World Elite Mastercard) is
published on a single JS-enhanced listing page at brimfinancial.com/credit-cards.
There are no per-card detail URLs; we use fragment identifiers in card_urls and
parse each product tile from the shared listing HTML.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from churney.emit import card_file_path, emit, load_card_file, semantic_dict
from churney.models import Card, CardFile, CardVersion, EarnRate, Network, ReviewItem, RewardKind
from churney.report import Outcome
from scrapers.base import IssuerScraper
from scrapers.common import money_to_minor

LISTING_URL = "https://brimfinancial.com/credit-cards"

# Fragment suffixes in sources.yaml card_urls map to these variants.
CARD_VARIANTS: dict[str, dict[str, str]] = {
    "brim-mastercard": {
        "name": "Brim Mastercard",
        "heading": "Brim Standard",
        "page_url": f"{LISTING_URL}#brim-mastercard",
    },
    "brim-world-elite-mastercard": {
        "name": "Brim World Elite Mastercard",
        "heading": "Brim World Elite",
        "page_url": f"{LISTING_URL}#brim-world-elite-mastercard",
    },
}

_ANNUAL_FEE_RE = re.compile(r"\$([\d,]+)\s+Annual Fee", re.I)
_EARN_RE = re.compile(
    r"Earn\s+(\d+)\s+point(?:s)?\s+for\s+every\s+\$(\d+)\s+spent",
    re.I,
)
_FX_PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%\s*Foreign Transaction", re.I)


class BrimScraper(IssuerScraper):
    issuer_slug = "brim"
    default_program = "brim_rewards"

    def discover_card_urls(self) -> Iterable[str]:
        if self.source.card_urls:
            yield from self.source.card_urls
            return
        for variant in CARD_VARIANTS.values():
            yield variant["page_url"]

    def run(self, *, force: bool = False, limit: int | None = None) -> list[Outcome]:
        self.source.assert_crawlable()
        variants = list(self._variant_slugs())
        if limit is not None:
            variants = variants[:limit]

        listing_url = LISTING_URL
        try:
            page = self.fetcher.fetch(listing_url)
        except Exception as exc:  # noqa: BLE001
            return [
                Outcome(card_slug=slug, status="failed", detail=str(exc))
                for slug in variants
            ]

        outcomes: list[Outcome] = []
        for slug in variants:
            outcomes.append(
                self._process_variant(
                    slug,
                    page.html,
                    page.content_hash,
                    force=force,
                )
            )
        return outcomes

    def parse_card(self, html: str, url: str) -> CardFile:
        slug = self._slug_from_url(url)
        return self._build_card_file(html, slug, url)

    # -- internals -------------------------------------------------------------

    def _variant_slugs(self) -> Iterable[str]:
        if self.source.card_urls:
            for url in self.source.card_urls:
                yield self._slug_from_url(url)
            return
        yield from CARD_VARIANTS

    def _slug_from_url(self, url: str) -> str:
        fragment = urlparse(url).fragment
        if fragment in CARD_VARIANTS:
            return fragment
        tail = url.rstrip("/").split("/")[-1].removesuffix(".html")
        return tail if tail != "credit-cards" else "unknown"

    def _process_variant(
        self,
        slug: str,
        html: str,
        content_hash: str,
        *,
        force: bool,
    ) -> Outcome:
        variant = CARD_VARIANTS[slug]
        page_url = variant["page_url"]
        out_path = card_file_path(self.out_dir, slug)
        try:
            card_file = self._build_card_file(html, slug, page_url)
            card_file.content_hash = content_hash
            old = load_card_file(out_path) if out_path.exists() else None
            path = emit(card_file, self.out_dir)
        except Exception as exc:  # noqa: BLE001
            return Outcome(card_slug=slug, status="failed", detail=str(exc))

        if old is not None:
            status = (
                "unchanged"
                if semantic_dict(old) == semantic_dict(card_file)
                else "updated"
            )
        else:
            status = "new"
        detail = (
            f"{len(card_file.needs_manual_review)} review items"
            if card_file.needs_manual_review
            else ""
        )
        return Outcome(
            card_slug=card_file.card.slug,
            status=status,
            path=str(path),
            detail=detail,
        )

    def _build_card_file(self, html: str, slug: str, page_url: str) -> CardFile:
        variant = CARD_VARIANTS[slug]
        soup = BeautifulSoup(html, "lxml")
        for tag in soup.find_all(["nav", "footer"]):
            tag.decompose()

        tile = self._find_tile(soup, variant["heading"])
        if tile is None:
            raise ValueError(f"card tile not found for {variant['heading']!r}")

        review: list[ReviewItem] = []
        fee_box = tile.select_one(".annual_fee_box")
        if fee_box is None:
            raise ValueError(f"annual_fee_box missing for {variant['heading']!r}")

        fee_text = fee_box.get_text(" ", strip=True)
        fee_m = _ANNUAL_FEE_RE.search(fee_text)
        if fee_m:
            annual_fee_minor = money_to_minor("$" + fee_m.group(1))
        elif "$0" in fee_text and "annual fee" in fee_text.lower():
            annual_fee_minor = 0
        else:
            annual_fee_minor = None
            review.append(ReviewItem(field="annual_fee_minor", reason="fee pattern not found"))

        earn_m = _EARN_RE.search(fee_text)
        earn_rates: list[EarnRate] = []
        if earn_m:
            points = float(earn_m.group(1))
            dollars = float(earn_m.group(2))
            earn_rates.append(
                EarnRate(
                    category_slug=None,
                    rate=points / dollars,
                    kind=RewardKind.POINTS,
                    source_url=page_url,
                )
            )
        else:
            review.append(ReviewItem(field="earn_rates", reason="base earn pattern not found"))

        fx_m = _FX_PCT_RE.search(fee_text)
        if fx_m:
            fx_fee_pct = float(fx_m.group(1))
        else:
            page_fx = _FX_PCT_RE.search(soup.get_text(" ", strip=True))
            fx_fee_pct = float(page_fx.group(1)) if page_fx else None
        if fx_fee_pct is None:
            review.append(
                ReviewItem(
                    field="fx_fee_pct",
                    reason="per-card FX fee not stated on tile; Brim site cites 1.5% elsewhere [VERIFY]",
                )
            )

        review.append(
            ReviewItem(
                field="purchase_apr",
                reason="purchase APR not stated on brimfinancial.com credit-cards page",
            )
        )
        review.append(
            ReviewItem(
                field="cash_apr",
                reason="cash advance APR not stated on brimfinancial.com credit-cards page",
            )
        )
        review.append(
            ReviewItem(
                field="offers",
                reason="no public welcome-bonus offer on brimfinancial.com page at scrape time",
            )
        )

        card = Card(
            slug=slug,
            issuer_slug=self.issuer_slug,
            name=variant["name"],
            network=Network.MASTERCARD,
            program_slug=self.default_program,
            card_type="personal",
            status="live",
            page_url=page_url,
        )
        version = CardVersion(
            valid_from=date.today(),
            annual_fee_minor=annual_fee_minor,
            extra_card_fee_minor=None,
            fx_fee_pct=fx_fee_pct,
            purchase_apr=None,
            cash_apr=None,
            source_url=page_url,
        )
        return CardFile(
            card=card,
            card_version=version,
            earn_rates=earn_rates,
            offers=[],
            needs_manual_review=review,
        )

    def _find_tile(self, soup: BeautifulSoup, heading: str) -> Tag | None:
        for h4 in soup.find_all("h4"):
            if h4.get_text(strip=True) == heading:
                parent = h4.find_parent(class_="cars_holder_main")
                if parent is not None:
                    return parent
        return None
