"""American Express Canada scraper (build order: docs/04 Â§9.3 phase 2a).

Amex CA pages are largely server-rendered around stable copy patterns ("Annual fee",
"Earn X Points for every $1 ... at grocery stores"), which this parser keys on.

Honesty rules (Â§9.2): anything not confidently found becomes null plus a
`needs_manual_review` entry â€” never guessed values.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, datetime, timezone
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from churney.config import SourceConfig
from churney.fetch import Fetcher
from churney.models import (
    AlternateOffer,
    Card,
    CardFile,
    CardVersion,
    EarnRate,
    Network,
    Offer,
    ReviewItem,
    RewardKind,
)
from scrapers.base import IssuerScraper

# Card detail pages are single-segment slugs under credit-cards/ or charge-cards/.
# Excludes the all-cards listing sections themselves.
CARD_LINK_RE = re.compile(r"^/en-ca/(?:credit-cards|charge-cards)/([a-z0-9-]+)/?$")
EXCLUDED_SLUGS = {"all-cards"}

FEE_RE = re.compile(r"annual (?:card )?fee[:\s]*\$([\d,]+(?:\.\d{2})?)", re.I)
SUPP_FEE_RE = re.compile(
    r"(?:supplementary|additional)\s+card[^.]*?\$\s?([\d,]+(?:\.\d{2})?)", re.I
)
# Monthly-billed cards: "Card Fee $15.99/month (Equals $191.88 annually)"
MONTHLY_FEE_RE = re.compile(
    r"card fee[:\s]*\$([\d,]+(?:\.\d{2})?)\s*/\s*month(?:[^.]*?=\s*\$([\d,]+(?:\.\d{2})?)\s*annually)?",
    re.I,
)
FX_FEE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*%\s*(?:service charge|fee)[^.]*(?:foreign|outside canada)", re.I
)
INCOME_RE = re.compile(r"minimum\s+income[^.\d$]{0,30}\$([\d,]+)", re.I)
HOUSEHOLD_INCOME_RE = re.compile(r"household\s+income[^.\d$]{0,30}\$([\d,]+)", re.I)
PURCHASE_APR_RE = re.compile(
    r"(?:purchases?|standard rate)[^.]{0,40}?(\d+(?:\.\d+)?)\s*%", re.I
)
CASH_APR_RE = re.compile(
    r"(?:(?:cash|funds)\s+advances?[^.]{0,60}?(\d+(?:\.\d+)?)\s*%)"
    r"|(?: (\d+(?:\.\d+)?)\s*%\s*on\s+(?:cash|funds)\s+advances)",    re.I,
)

# "Earn 60,000 Aeroplan Â® * points ..." â€” program words may sit between amount and
# the word "points" (footnote markers Â® * interleaved).
WB_POINTS_RE = re.compile(
    r"[Ee]arn\s+(?:up to\s+)?([\d,]{3,})(?:[^\d]{0,40}?)?\s+[Pp]oints\b"
)
WB_CASH_RE = re.compile(
    r"[Ee]arn\s+(?:up to\s+)?(?:\$|(\d+)\s*)([\d,]+(?:\.\d{2})?)\s*(?:cash back|dollars)",
    re.I,
)
MSR_RE = re.compile(
    r"(?:spending|spend)[^.]{0,20}?\$([\d,]+)[^.]{0,80}?(?:first\s+)?(\d+)\s*months?\b",
    re.I,
)
ELIGIBILITY_NOTES_RE = re.compile(
    r"Current or former Cardmembers[^.]{0,160}\.", re.I
)
# "when you spend $2,500 in month 13" — a later-spend component, not a deadline.
LATER_SPEND_RE = re.compile(
    r"(?:spending|spend)\s+\$([\d,]+)[^.]{0,60}?\bmonth\s+(\d{1,2})\b", re.I
)
FIRST_YEAR_FREE_RE = re.compile(r"first year free", re.I)

# Earn-rate tiles flattened from the rendered UI: "3X AEROPLAN POINTS On Air Canada
# 3X AEROPLAN POINTS On Air Canada For eligible ... purchases 6 2X ..."
EARN_TILE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*[xX]\s+(?:[A-Z][A-Za-zÂ®*'&.\s]*?\s+)?(?:POINTS|points|cash back)"
    r"\s+[Oo]n\s+",
)
# "Earn 5 points for every $1 ..." / "Earn 4x points ..." / "Earn 1.25% cash back ..."
EARN_LINE_RE = re.compile(
    r"[Ee]arn\s+(\d+(?:\.\d+)?)\s*(points|point|x(?!\s*the\b)|%)"
)
EARN_CATEGORY_HINTS = {
    "grocery": ["grocery", "supermarket"],
    "gas": ["gas station", "fuel"],
    "dining": ["restaurant", "dining", "food delivery", "eats & drinks", "eats"],
    "travel_air": ["airline", "air canada", "flight"],
    "travel_hotel": ["hotel", "motel", "hyatt", "marriott", "hilton", "bonvoy"],
    "travel_other": ["car rental", "travel"],
    "transit_rideshare": ["transit", "rideshare", "uber"],
    "streaming_subs": ["streaming", "subscription"],
    "drugstore": ["drugstore", "pharmacy"],
}

PROGRAM_BY_TOKEN = (
    ("aeroplan", "aeroplan"),
    ("cobalt", "amex_mr"),
    ("gold rewards", "amex_mr"),
    ("green", "amex_mr"),
    ("platinum", "amex_mr"),
    ("business gold", "amex_mr"),
    ("essential", "amex_mr"),
    ("marriott", "marriott_bonvoy"),
    ("bonvoy", "marriott_bonvoy"),
    ("simplycash", "simplycash"),
)

from scrapers.common import (
    PCT_BACK_RE,
    is_base_context,
    is_no_annual_fee_primary,
    match_all_categories,
)

NO_ANNUAL_FEE_RE = re.compile(r"no annual fee", re.I)
# "Additional Cards No annual fee" / supplementary-card context — describes extra
# cards, not the primary annual fee.
SUPP_NO_FEE_CONTEXT = re.compile(
    r"(?:additional|supplementary|extra)\s+(?:\w+\s+){0,3}cards?[^.]{0,40}$",
    re.I,
)


def money_to_minor(text: str) -> int | None:
    """'$1,234.56' -> 123456; '$250' -> 25000."""
    m = re.search(r"([\d,]+)(?:\.(\d{1,2}))?", text)
    if not m:
        return None
    dollars = int(m.group(1).replace(",", ""))
    cents = m.group(2)
    if cents is None:
        return dollars * 100
    return dollars * 100 + int(cents.ljust(2, "0"))


def classify_program(name: str) -> str | None:
    lowered = name.lower()
    for token, slug in PROGRAM_BY_TOKEN:
        if token in lowered:
            return slug
    return None


class AmexCaScraper(IssuerScraper):
    issuer_slug = "amex_ca"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._today = date.today()

    # -- discovery -----------------------------------------------------------

    def discover_card_urls(self) -> Iterable[str]:
        seen: set[str] = set()
        for entry in self.source.entry_urls:
            page = self.fetcher.fetch(entry)
            soup = BeautifulSoup(page.html, "lxml")
            for a in soup.find_all("a", href=True):
                path = a["href"].split("?")[0].rstrip("/")
                m = CARD_LINK_RE.match(path)
                if not m or m.group(1) in EXCLUDED_SLUGS:
                    continue
                url = f"https://{urlparse(entry).netloc}{path}/"
                if url not in seen:
                    seen.add(url)
                    yield url

    # -- parsing ---------------------------------------------------------------

    def parse_card(self, html: str, url: str) -> CardFile:
        soup = BeautifulSoup(html, "lxml")
        # Strip nav/footer before text extraction: nav filter menus contain
        # copy like "No Annual Fee Cards" that otherwise false-positives the
        # fee regexes (parity with GenericIssuerScraper.parse_card).
        for tag in soup.find_all(["nav", "footer"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        # Rejoin numbers split across inline DOM nodes ("35 ,000" -> "35,000").
        text = re.sub(r"(\d)\s*,\s*(\d)", r"\1,\2", text)

        review: list[ReviewItem] = []

        name_el = soup.find("h1")
        raw_name = name_el.get_text(strip=True) if name_el else ""
        if not raw_name:
            raise ValueError(f"no <h1> card name found on {url}")
        name = re.sub(r"\s+", " ", raw_name)
        # Normalize trademark artifacts: "American Express® Aeroplan®* Reserve Card"
        # -> "Aeroplan Reserve Card". Handles glued names ("Express®Cobalt") too.
        name = re.sub(r"[®*™]+", " ", name)
        name = re.sub(r"^American\s+Express[\s]*", "", name, flags=re.I)
        name = re.sub(r"\s+", " ", name).strip()

        program_slug = classify_program(name)
        if program_slug is None:
            review.append(
                ReviewItem(field="program_slug", reason=f"could not infer from name {name!r}")
            )
            program_slug = "unknown"

        # Business classification uses the raw page signals, before any name cleanup.
        is_business = (
            "business" in raw_name.lower()
            or "small business" in name.lower()
            or "/business" in urlparse(url).path
            or "-business-" in url
        )

        # --- fees / terms ---
        monthly_fee = MONTHLY_FEE_RE.search(text)
        fee_match = FEE_RE.search(text)
        if monthly_fee:
            annual_txt = monthly_fee.group(2) or str(
                float(monthly_fee.group(1).replace(",", "")) * 12
            )
            annual_fee_minor = money_to_minor("$" + annual_txt)
            review.append(
                ReviewItem(
                    field="annual_fee_minor",
                    reason=f"monthly-billed card (${monthly_fee.group(1)}/month); "
                    f"stored annualized as {annual_fee_minor} minor units",
                )
            )
        elif fee_match:
            annual_fee_minor = money_to_minor("$" + fee_match.group(1))
        elif is_no_annual_fee_primary(text):
            annual_fee_minor = 0
        else:
            annual_fee_minor = None
            review.append(ReviewItem(field="annual_fee_minor", reason="fee pattern not found"))

        supp_match = SUPP_FEE_RE.search(text)
        extra_card_fee_minor = money_to_minor(supp_match.group(0)) if supp_match else None

        fx_match = FX_FEE_RE.search(text)
        fx_fee_pct = float(fx_match.group(1)) if fx_match else None
        if fx_fee_pct is None:
            review.append(
                ReviewItem(
                    field="fx_fee_pct",
                    reason="per-card FX fee not stated; verify standard 2.5% [VERIFY]",
                )
            )

        personal_income_match = INCOME_RE.search(text)
        household_income_match = HOUSEHOLD_INCOME_RE.search(text)
        income_personal = (
            int(personal_income_match.group(1).replace(",", ""))
            if personal_income_match
            else None
        )
        income_household = (
            int(household_income_match.group(1).replace(",", ""))
            if household_income_match
            else None
        )

        apr_match = PURCHASE_APR_RE.search(text)
        purchase_apr = float(apr_match.group(1)) if apr_match else None
        cash_apr_match = CASH_APR_RE.search(text)
        cash_apr = (
            float(cash_apr_match.group(1) or cash_apr_match.group(2))
            if cash_apr_match
            else None
        )
        if purchase_apr is None:
            review.append(ReviewItem(field="purchase_apr", reason="APR pattern not found"))

        version = CardVersion(
            valid_from=self._today,
            annual_fee_minor=annual_fee_minor,
            extra_card_fee_minor=extra_card_fee_minor,
            fx_fee_pct=fx_fee_pct,
            income_req_personal=income_personal,
            income_req_household=income_household,
            purchase_apr=purchase_apr,
            cash_apr=cash_apr,
            source_url=url,
        )

        # --- earn rates ---
        earn_rates, earn_reviews = self._extract_earn_rates(text, url)
        review.extend(earn_reviews)

        # --- welcome offers (two-layer capture) ---
        offer, offer_reviews = self._extract_offer(text, url)
        review.extend(offer_reviews)

        card = Card(
            slug="amex-ca-"
            + urlparse(url).path.rstrip("/").split("/")[-1].removesuffix(".html"),
            issuer_slug=self.issuer_slug,
            name=name,
            network=Network.AMEX,
            program_slug=program_slug,
            card_type="business" if is_business else "personal",
            status="live",
            page_url=url,
        )
        return CardFile(
            card=card,
            card_version=version,
            earn_rates=earn_rates,
            offers=[offer] if offer else [],
            needs_manual_review=review,
        )

    # -- helpers -----------------------------------------------------------------

    def _extract_earn_rates(self, text: str, url: str) -> tuple[list[EarnRate], list[ReviewItem]]:
        rates: list[EarnRate] = []
        reviews: list[ReviewItem] = []
        seen: set[tuple[str | None, float]] = set()
        review = reviews

        def add(category: str | None, value: float, kind: RewardKind, cap=None) -> None:
            key = (category, value)
            if key in seen:
                return
            seen.add(key)
            rates.append(
                EarnRate(
                    category_slug=category,
                    rate=value,
                    kind=kind,
                    cap_amount_minor=cap,
                    source_url=url,
                )
            )

        # --- tile structure ("3X AEROPLAN POINTS On Air Canada ... 2X ... On dining") ---
        tiles = list(EARN_TILE_RE.finditer(text))
        for i, m in enumerate(tiles):
            start = m.end()
            end = tiles[i + 1].start() if i + 1 < len(tiles) else min(len(text), start + 200)
            chunk = text[start:end]
            title = re.split(r"\b(?:For eligible|From|on your|when you)\b", chunk, maxsplit=1)[0]
            title = re.sub(r"\s+", " ", re.sub(r"\d+$", "", title)).strip(" .,-")
            category = self._tile_category(title)
            if category == "__base__":
                category = None
            elif category == "__unknown__":
                review.append(
                    ReviewItem(
                        field="earn_rates",
                        reason=f"unmapped earn-tile title skipped (never-guess): {title!r}",
                    )
                )
                continue
            add(category, float(m.group(1)), RewardKind.POINTS)

        # --- sentence patterns ("Earn 5 points for every $1...", "Earn 4% cash back...") ---
        seen_categories = {r.category_slug for r in rates if r.category_slug}
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            m = EARN_LINE_RE.search(sentence)
            if not m:
                continue
            value = float(m.group(1))
            marker = m.group(2)
            kind = (
                RewardKind.POINTS
                if marker in ("points", "point", "x")
                else RewardKind.CASHBACK
            )
            if marker == "%":
                value /= 100  # data-model convention: cashback rate = pct/100
            lowered = sentence.lower()
            category = None
            for slug, hints in EARN_CATEGORY_HINTS.items():
                if slug in seen_categories:
                    continue
                if any(h in lowered for h in hints):
                    category = slug
                    break
            if category is None and not is_base_context(lowered):
                # Uncategorizable earn line (e.g. marketing headline "Earn 3X
                # the points ..." whose category was already captured) — adding
                # it as base would be a guess. Skip.
                continue
            cap_match = re.search(r"(?:up to|cap(?:ped)? (?:at)?)\s*\$([\d,]+)", lowered)
            add(
                category,
                value,
                kind,
                money_to_minor(cap_match.group(0)) if cap_match else None,
            )
            if category:
                seen_categories.add(category)

        # --- percent-cash-back tiles ("4% CASH BACK On gas For eligible ...") ---
        # Multi-category aware; mirrors GenericIssuerScraper's PCT_BACK pass.
        seen_cats_pct = {r.category_slug for r in rates if r.category_slug}
        pct = list(PCT_BACK_RE.finditer(text))
        for i, m in enumerate(pct):
            # Skip welcome-bonus copy ("earn a bonus 10% cash back on all
            # purchases") — the offer extractor owns those numbers.
            lead = text[max(0, m.start() - 70) : m.start()].lower()
            if re.search(r"bonus|welcome|offer", lead):
                continue
            ctx = (m.group(2) or "").lower()
            is_base = any(
                k in ctx for k in ("everything else", "all purchases", "all other", "everywhere else", "everyday purchases")
            )
            cats = (
                [c for c in match_all_categories(ctx) if c not in seen_cats_pct]
                if ctx
                else []
            )
            if not ctx or (not cats and not is_base):
                continue  # unmatched context would be a guess
            cap = re.search(r"(?:up to|first)\s*\$([\d,]+)", m.group(0), re.I)
            value = float(m.group(1)) / 100  # convention: cashback rate = pct/100
            cap_minor = money_to_minor("$" + cap.group(1)) if cap else None
            if is_base:
                add(None, value, RewardKind.CASHBACK, cap_minor)
            else:
                for cat in cats:
                    add(cat, value, RewardKind.CASHBACK, cap_minor)
                seen_cats_pct.update(cats)

        # Stable sort: base rate (category_slug=None) first, then boosted categories.
        rates.sort(key=lambda r: r.category_slug is not None)

        if not rates:
            reviews.append(
                ReviewItem(field="earn_rates", reason="no earn patterns found on page")
            )
        elif not any(r.category_slug is None for r in rates):
            reviews.append(
                ReviewItem(field="earn_rates", reason="no base-rate pattern found")
            )
        return rates, reviews

    def _tile_category(self, title: str) -> str:
        """Map an earn-tile title like 'Air Canada' or 'everything else' to a taxonomy slug.
        Returns '__base__' for base-rate titles and '__unknown__' when the tile's
        category cannot be determined (caller must skip it - never-guess rule)."""
        lowered = title.lower().strip()
        if (
            not lowered
            or "everything else" in lowered
            or "everyday purchases" in lowered
            or lowered.startswith("all other")
        ):
            return "__base__"
        for slug, hints in EARN_CATEGORY_HINTS.items():
            if any(h in lowered for h in hints):
                return slug
        return "__unknown__"

    def _extract_offer(self, text: str, url: str) -> tuple[Offer | None, list[ReviewItem]]:
        reviews: list[ReviewItem] = []

        points_parts = [
            (int(m.group(1).replace(",", "")), m.end()) for m in WB_POINTS_RE.finditer(text)
        ]
        cash_match = WB_CASH_RE.search(text)

        if points_parts:
            # Hero headline + body copy often repeat the same bonus; drop duplicates.
            canonical = points_parts[0]
            rest = [p for p in points_parts[1:] if p[0] != canonical[0]]
            reward_points_first, first_end = canonical
            headline = f"Earn {reward_points_first:,} points"
            msr = MSR_RE.search(text, first_end)
            min_spend = deadline = None
            if msr:
                min_spend = money_to_minor("$" + msr.group(1))
                months = int(msr.group(2))
                deadline = months * 30  # approximation; month count kept in notes
                eligibility_notes = f"deadline stated as {months} months on page"
            else:
                eligibility_notes = None
                reviews.append(
                    ReviewItem(
                        field="offer.min_spend", reason="min-spend/deadline pattern not found"
                    )
                )
            notes_m = ELIGIBILITY_NOTES_RE.search(text)
            if notes_m:
                eligibility_notes = " ".join(
                    filter(None, [eligibility_notes, notes_m.group(0)])
                )

            canonical_points = reward_points_first
            alternates: list[AlternateOffer] = []

            # Later-spend components of the same offer (e.g. "25,000 ... in month 13").
            for pts, end in rest:
                alt_msr = MSR_RE.search(text, end)
                later = None if alt_msr else LATER_SPEND_RE.search(text, end)
                alternates.append(
                    AlternateOffer(
                        headline=f"Additional earn component: {pts:,} points",
                        channel="later_spend",
                        reward_points=pts,
                        min_spend_minor=money_to_minor("$" + alt_msr.group(1))
                        if alt_msr
                        else money_to_minor("$" + later.group(1))
                        if later
                        else None,
                        deadline_days=int(alt_msr.group(2)) * 30 if alt_msr else None,
                        source_url=url,
                        seen_on=self._today,
                    )
                )
            # Referral / limited-time variants.
            alt_points_re = re.compile(r"([\d,]+)\s*bonus\s+points", re.I)
            for sentence in re.split(r"(?<=[.!?])\s+", text):
                lowered = sentence.lower()
                if "limited time" not in lowered and "referral" not in lowered:
                    continue
                m = alt_points_re.search(sentence)
                if not m:
                    continue
                channel = "limited_time" if "limited time" in lowered else "referral"
                alternates.append(
                    AlternateOffer(
                        headline=re.sub(r"\s+", " ", sentence)[:200],
                        channel=channel,
                        reward_points=int(m.group(1).replace(",", "")),
                        source_url=url,
                        seen_on=self._today,
                    )
                )

            fyf = bool(FIRST_YEAR_FREE_RE.search(text))
            offer = Offer(
                headline=headline,
                min_spend_minor=min_spend,
                deadline_days=deadline,
                reward_points=canonical_points,
                eligibility_notes=eligibility_notes,
                first_year_free=fyf or None,
                alternate_offers=alternates,
                source_url=url,
                verified_at=datetime.now(timezone.utc),
            )
            return offer, reviews

        if cash_match:
            amount_txt = cash_match.group(2)
            reward_cashback_minor = money_to_minor("$" + amount_txt.replace(",", ""))
            msr = MSR_RE.search(text)
            min_spend = money_to_minor("$" + msr.group(1)) if msr else None
            deadline = int(msr.group(2)) * 30 if msr else None
            if not msr:
                reviews.append(
                    ReviewItem(
                        field="offer.min_spend", reason="min-spend/deadline pattern not found"
                    )
                )
            fyf = bool(FIRST_YEAR_FREE_RE.search(text))
            offer = Offer(
                headline=f"Earn ${reward_cashback_minor // 100} cash back",
                min_spend_minor=min_spend,
                deadline_days=deadline,
                reward_cashback_minor=reward_cashback_minor,
                first_year_free=fyf or None,
                alternate_offers=[],
                source_url=url,
                verified_at=datetime.now(timezone.utc),
            )
            return offer, reviews

        reviews.append(
            ReviewItem(field="offers", reason="no welcome-bonus pattern found")
        )
        return None, reviews

