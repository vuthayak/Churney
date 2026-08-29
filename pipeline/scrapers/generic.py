"""Config-driven generic issuer scraper.

Per-issuer behaviour comes from sources.yaml:
  link_pattern:   regex (string) selecting card-detail paths from listing hrefs
  program_tokens: ordered [token, program_slug] pairs for program inference
Subclasses may override parse_card for site-specific quirks.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime, timezone
from urllib.parse import urlparse

from bs4 import BeautifulSoup

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
from scrapers.common import (
    BASE_SENTINEL,
    CASH_APR_RE,
    EARN_LINE_RE,
    EARN_TILE_RE,
    ELIGIBILITY_NOTES_RE,
    FEE_RE,
    FIRST_YEAR_FREE_RE,
    FX_FEE_RE,
    HOUSEHOLD_INCOME_RE,
    INCOME_RE,
    LATER_SPEND_RE,
    MONTHLY_FEE_RE,
    MSR_DAYS_RE,
    MSR_MONTHS_RE,
    MSR_STATEMENT_RE,
    NO_ANNUAL_FEE_RE,
    is_no_annual_fee_primary,
    PCT_BACK_RE,
    POINTS_PER_DOLLAR_RE,
    PURCHASE_APR_RE,
    SUPP_FEE_RE,
    WB_CASH_RE,
    WB_POINTS_RE,
    is_base_context,
    match_all_categories,
    match_category,
    money_to_minor,
    tile_title_category,
)

DEFAULT_PROGRAM_TOKENS = (
    ("aeroplan", "aeroplan"),
    ("aventura", "aventura"),
    ("scene", "scene_plus"),
    ("scene+", "scene_plus"),
    ("bonvoy", "marriott_bonvoy"),
    ("marriott", "marriott_bonvoy"),
    ("cash back", "cashback"),
    ("cashback", "cashback"),
    ("money-back", "cashback"),
    ("money back", "cashback"),
)


class GenericIssuerScraper(IssuerScraper):
    """Works off the shared copy-pattern toolkit. Subclasses tune via class attrs."""

    issuer_slug = "generic"
    network = None  # set by subclass
    default_program = "unknown"
    program_tokens: tuple[tuple[str, str], ...] = ()
    # families whose two-segment paths are NOT cards (scotiabank-style)
    excluded_families: set[str] = {"browse-all", "manage-your-credit-card"}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        from datetime import date

        self._today = date.today()
        self._link_re = re.compile(self.source.link_pattern) if source_has(self.source, "link_pattern") else None

    # -- discovery ------------------------------------------------------------

    def discover_card_urls(self) -> Iterable[str]:
        # Explicit card URL lists skip listing discovery entirely (single-card
        # issuers, JS-rendered listings with known detail paths).
        if self.source.card_urls:
            yield from self.source.card_urls
            return
        seen: set[str] = set()
        netloc = None
        for entry in self.source.entry_urls:
            page = self.fetcher.fetch(entry)
            netloc = urlparse(entry).netloc
            soup = BeautifulSoup(page.html, "lxml")
            for a in soup.find_all("a", href=True):
                path = a["href"].split("?")[0].split("#")[0]
                if path.startswith("http"):
                    path = urlparse(path).path
                if not self._keep_link(path):
                    continue
                url = path if path.startswith("http") else f"https://{netloc}{path}"
                url = url.rstrip("/") + ("/" if path.endswith("/") else "")
                if url not in seen:
                    seen.add(url)
                    yield url

    def _keep_link(self, path: str) -> bool:
        if not self._link_re:
            return False
        m = self._link_re.match(path)
        if not m:
            return False
        tail = path.rstrip("/").split("/")[-1].removesuffix(".html")
        if tail.startswith(("compare", "activate")):
            return False
        groups = [g for g in m.groups() if g]
        return not any(g in self.excluded_families for g in groups)

    # -- parsing ---------------------------------------------------------------

    def parse_card(self, html: str, url: str) -> CardFile:
        soup = BeautifulSoup(html, "lxml")
        # Nav/footer chrome carries other cards' marketing copy (cross-sell
        # blocks) - removing it prevents phantom rates from sibling products.
        for tag in soup.find_all(["nav", "footer"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        # Rejoin numbers split across inline DOM nodes (CIBC renders "35 ,000"):
        # "35 ,000" -> "35,000". Safe: only touches digit-comma-digit sequences.
        text = re.sub(r"(\d)\s*,\s*(\d)", r"\1,\2", text)
        review: list[ReviewItem] = []

        name = self._extract_name(soup, url)
        program_slug = self._classify_program(name)
        if program_slug is None:
            review.append(
                ReviewItem(field="program_slug", reason=f"could not infer from name {name!r}")
            )
            program_slug = self.default_program

        version = self._extract_version(text, url, review)
        earn_rates, earn_reviews = self._extract_earn_rates(text, url)
        review.extend(earn_reviews)
        offer, offer_reviews = self._extract_offer(text, url)
        review.extend(offer_reviews)

        card = Card(
            slug=self._slug_for(url),
            issuer_slug=self.issuer_slug,
            name=name,
            network=self.network_for(name),
            program_slug=program_slug,
            card_type="business" if self._is_business(name, url) else "personal",
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

    # -- hooks / helpers ---------------------------------------------------------

    def _extract_name(self, soup: BeautifulSoup, url: str) -> str:
        h1 = soup.find("h1")
        raw = h1.get_text(strip=True) if h1 else ""
        name = re.sub(r"\s+", " ", raw)
        name = re.sub(r"[®*™‡†]+", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        if not name:
            raise ValueError(f"no <h1> on {url}")
        return name

    def _slug_for(self, url: str) -> str:
        tail = url.rstrip("/").split("/")[-1].removesuffix(".html").removesuffix(".htm")
        return f"{self.issuer_slug.replace('_', '-')}-{tail.lower()}"

    def _classify_program(self, name: str) -> str | None:
        lowered = name.lower()
        for token, slug in (*self.program_tokens, *DEFAULT_PROGRAM_TOKENS):
            if token in lowered:
                return slug
        return None

    def _is_business(self, name: str, url: str) -> bool:
        blob = f"{name} {url}".lower()
        return "business" in blob

    def network_for(self, name: str) -> Network:
        if self.network:
            return self.network
        lowered = name.lower()
        if "visa" in lowered:
            return Network.VISA
        if "mastercard" in lowered:
            return Network.MASTERCARD
        return Network.VISA

    def _extract_version(self, text: str, url: str, review: list[ReviewItem]) -> CardVersion:
        monthly = MONTHLY_FEE_RE.search(text)
        fee_match = FEE_RE.search(text)
        if monthly:
            annual_txt = monthly.group(2) or str(float(monthly.group(1).replace(",", "")) * 12)
            annual_fee_minor = money_to_minor("$" + annual_txt)
            review.append(
                ReviewItem(
                    field="annual_fee_minor",
                    reason=f"monthly-billed (${monthly.group(1)}/mo); annualized {annual_fee_minor}",
                )
            )
        elif fee_match:
            annual_fee_minor = money_to_minor("$" + fee_match.group(1))
        elif is_no_annual_fee_primary(text):
            annual_fee_minor = 0
        else:
            annual_fee_minor = None
            review.append(ReviewItem(field="annual_fee_minor", reason="fee pattern not found"))

        supp = SUPP_FEE_RE.search(text)
        extra = money_to_minor("$" + supp.group(1)) if supp else None

        fx = FX_FEE_RE.search(text)
        fx_fee_pct = float(fx.group(1)) if fx else None
        if fx_fee_pct is None:
            review.append(
                ReviewItem(field="fx_fee_pct", reason="per-card FX fee not stated; most CA cards 2.5% [VERIFY]")
            )

        income_m = INCOME_RE.search(text)
        hh_m = HOUSEHOLD_INCOME_RE.search(text)

        apr_m = PURCHASE_APR_RE.search(text)
        purchase_apr = float(apr_m.group(1)) if apr_m else None
        cash_m = CASH_APR_RE.search(text)
        cash_apr = float(cash_m.group(1) or cash_m.group(2)) if cash_m else None

        return CardVersion(
            valid_from=self._today,
            annual_fee_minor=annual_fee_minor,
            extra_card_fee_minor=extra,
            fx_fee_pct=fx_fee_pct,
            income_req_personal=int(income_m.group(1).replace(",", "")) if income_m else None,
            income_req_household=int(hh_m.group(1).replace(",", "")) if hh_m else None,
            purchase_apr=purchase_apr,
            cash_apr=cash_apr,
            source_url=url,
        )

    def _extract_earn_rates(self, text: str, url: str) -> tuple[list[EarnRate], list[ReviewItem]]:
        rates: list[EarnRate] = []
        seen: set[tuple[str | None, float]] = set()
        reviews_ppd: list[ReviewItem] = []

        def add(category, value: float, kind: RewardKind, cap=None) -> None:
            key = (category, value)
            if key in seen:
                return
            seen.add(key)
            rates.append(
                EarnRate(category_slug=category, rate=value, kind=kind,
                         cap_amount_minor=cap, source_url=url)
            )

        tiles = list(EARN_TILE_RE.finditer(text))
        for i, m in enumerate(tiles):
            start = m.end()
            end = tiles[i + 1].start() if i + 1 < len(tiles) else min(len(text), start + 200)
            chunk = text[start:end]
            title = re.split(r"\b(?:For eligible|From|on your|when you|such as|Such as)\b",
                             chunk, maxsplit=1)[0]
            title = re.sub(r"\s+", " ", re.sub(r"\d+$", "", title)).strip(" .,-&")
            cat = tile_title_category(title)
            category = None if cat is BASE_SENTINEL else (cat if isinstance(cat, str) else None)
            add(category, float(m.group(1)), RewardKind.POINTS)

        seen_cats = {r.category_slug for r in rates if r.category_slug}

        # Grouped point lines without 'earn': "2 points for every $1 spent on
        # eligible travel", "1.5 points for every $1 you spend at eligible gas
        # stations, grocery stores and drug stores" (CIBC-style).
        ppd = list(POINTS_PER_DOLLAR_RE.finditer(text))
        for i, m in enumerate(ppd):
            value = float(m.group(1))
            end = ppd[i + 1].start() if i + 1 < len(ppd) else len(text)
            ctx = text[m.end() : min(end, m.end() + 400)].lower()
            if is_base_context(ctx):
                add(None, value, RewardKind.POINTS)
                continue
            cats = [c for c in match_all_categories(ctx) if c not in seen_cats]
            if not cats:
                # Unmatched context would be a guess — flag for review instead.
                reviews_ppd.append(
                    ReviewItem(
                        field="earn_rates",
                        reason=f"points-per-dollar context not matched: {ctx[:90]!r}",
                    )
                )
                continue
            for cat in cats:
                add(cat, value, RewardKind.POINTS)
            seen_cats.update(cats)

        # Verb-less feature copy: "4% cash back on gas and groceries" (CIBC-style tables).
        # Multi-category aware: one rate often spans several taxonomy categories.
        for m in PCT_BACK_RE.finditer(text):
            ctx = (m.group(2) or "").lower()
            is_base = any(
                k in ctx for k in ("everything", "all purchases", "all other")
            )
            cats = [c for c in match_all_categories(ctx) if c not in seen_cats] if ctx else []
            if not ctx or (not cats and not is_base):
                continue  # unmatched context (e.g. sibling-card promos) would be a guess
            cap = re.search(r"(?:up to|first)\s*\$([\d,]+)", m.group(0), re.I)
            # Data-model convention: cashback rate is pct/100 (4% -> 0.04)
            value = float(m.group(1)) / 100
            cap_minor = money_to_minor("$" + cap.group(1)) if cap else None
            if is_base:
                add(None, value, RewardKind.CASHBACK, cap_minor)
            else:
                for cat in cats:
                    add(cat, value, RewardKind.CASHBACK, cap_minor)
                seen_cats.update(cats)

        for sentence in re.split(r"(?<=[.!?])\s+", text):
            m = EARN_LINE_RE.search(sentence)
            if not m:
                continue
            value = float(m.group(1))
            marker = m.group(2)
            kind = RewardKind.CASHBACK if marker == "%" else RewardKind.POINTS
            if marker == "%":
                value /= 100  # pct/100 convention
            lowered = sentence.lower()
            category = match_category(lowered, exclude=seen_cats)
            if category is None and not is_base_context(lowered):
                # Uncategorizable earn line (e.g. a marketing headline whose
                # category was already captured precisely) — adding it as base
                # would be a guess. Skip.
                continue
            cap = re.search(r"(?:up to|cap(?:ped)? (?:at)?)\s*\$([\d,]+)", lowered)
            add(category, value, kind,
                money_to_minor("$" + cap.group(0)) if cap else None)
            if category:
                seen_cats.add(category)

        rates.sort(key=lambda r: r.category_slug is not None)
        reviews: list[ReviewItem] = []
        reviews.extend(reviews_ppd)
        if not rates:
            reviews.append(ReviewItem(field="earn_rates", reason="no earn patterns found on page"))
        elif not any(r.category_slug is None for r in rates):
            reviews.append(ReviewItem(field="earn_rates", reason="no base-rate pattern found"))
        return rates, reviews

    def _extract_offer(self, text: str, url: str) -> tuple[Offer | None, list[ReviewItem]]:
        reviews: list[ReviewItem] = []
        points_parts = [
            (int(m.group(1).replace(",", "")), m.end()) for m in WB_POINTS_RE.finditer(text)
        ]
        canonical = points_parts[0] if points_parts else None

        if canonical:
            rest = [p for p in points_parts[1:] if p[0] != canonical[0]]
            pts, first_end = canonical
            min_spend = deadline = None
            msr = (
                MSR_DAYS_RE.search(text, first_end)
                or MSR_MONTHS_RE.search(text, first_end)
                or MSR_STATEMENT_RE.search(text, first_end)
            )
            eligibility_notes = None
            if msr:
                min_spend = money_to_minor("$" + msr.group(1))
                n = int(msr.group(2))
                unit_days = 1 if MSR_DAYS_RE.match(msr.group(0), 0) else 30
                deadline = n * unit_days
                eligibility_notes = f"deadline stated as {n} {'days' if unit_days == 1 else 'months'} on page"
            else:
                reviews.append(
                    ReviewItem(field="offer.min_spend", reason="min-spend/deadline pattern not found")
                )
            notes = ELIGIBILITY_NOTES_RE.search(text)
            if notes:
                eligibility_notes = " ".join(filter(None, [eligibility_notes, notes.group(0)]))

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
                        deadline_days=(int(a_msr.group(2)) * (1 if MSR_DAYS_RE.match(a_msr.group(0), 0) else 30))
                        if a_msr
                        else None,
                        source_url=url,
                        seen_on=self._today,
                    )
                )
            offer = Offer(
                headline=f"Earn {pts:,} points",
                min_spend_minor=min_spend,
                deadline_days=deadline,
                reward_points=pts,
                eligibility_notes=eligibility_notes,
                first_year_free=bool(FIRST_YEAR_FREE_RE.search(text)) or None,
                alternate_offers=alternates,
                source_url=url,
                verified_at=datetime.now(timezone.utc),
            )
            return offer, reviews

        cash = WB_CASH_RE.search(text)
        if cash:
            cb = money_to_minor("$" + cash.group(2).replace(",", ""))
            msr = MSR_DAYS_RE.search(text) or MSR_MONTHS_RE.search(text) or MSR_STATEMENT_RE.search(text)
            min_spend = money_to_minor("$" + msr.group(1)) if msr else None
            deadline = None
            if msr:
                n = int(msr.group(2))
                days_unit = 1 if MSR_DAYS_RE.match(msr.group(0), 0) else 30
                deadline = n * days_unit
            if not msr:
                reviews.append(
                    ReviewItem(field="offer.min_spend", reason="min-spend/deadline pattern not found")
                )
            offer = Offer(
                headline=f"Earn ${cb // 100} cash back",
                min_spend_minor=min_spend,
                deadline_days=deadline,
                reward_cashback_minor=cb,
                first_year_free=bool(FIRST_YEAR_FREE_RE.search(text)) or None,
                alternate_offers=[],
                source_url=url,
                verified_at=datetime.now(timezone.utc),
            )
            return offer, reviews

        reviews.append(ReviewItem(field="offers", reason="no welcome-bonus pattern found"))
        return None, reviews


def source_has(source, attr: str) -> bool:
    try:
        return getattr(source, attr) is not None
    except AttributeError:
        return False
