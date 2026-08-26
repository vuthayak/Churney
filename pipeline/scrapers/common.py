"""Shared parsing toolkit for Canadian bank card pages.

Extracted from the Amex CA work (docs/04 §9.2 conventions): money = integer minor
units, every fact carries source_url, unparseable -> null + needs_manual_review,
never guessed values.
"""

from __future__ import annotations

import re


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


# --- copy-pattern regexes (tuned against live CA bank copy) ------------------

FEE_RE = re.compile(r"annual (?:card )?fee[:\s]*\$([\d,]+(?:\.\d{2})?)", re.I)
NO_ANNUAL_FEE_RE = re.compile(r"(?:no|without an?) annual (?:card )?fee", re.I)
# "Additional Cards No annual fee" / supplementary-card context — describes extra
# cards, not the primary annual fee.
SUPP_NO_FEE_CONTEXT = re.compile(
    r"(?:additional|supplementary|extra)\s+(?:\w+\s+){0,3}cards?[^.]{0,40}$",
    re.I,
)


def is_no_annual_fee_primary(text: str) -> bool:
    """True only if a 'no annual fee' occurrence refers to the PRIMARY card:
    skips menu/filter chips ("No Annual Fee Cards") and
    additional/supplementary-card contexts."""
    for m in NO_ANNUAL_FEE_RE.finditer(text):
        if text[m.end() : m.end() + 6].lower().startswith(" cards"):
            continue  # "No Annual Fee Cards" category chip
        if SUPP_NO_FEE_CONTEXT.search(text[max(0, m.start() - 80) : m.start()]):
            continue
        return True
    return False
SUPP_FEE_RE = re.compile(
    r"(?:supplementary|additional)\s+cards?[^.]*?\$\s?([\d,]+(?:\.\d{2})?)", re.I
)
MONTHLY_FEE_RE = re.compile(
    r"card fee[:\s]*\$([\d,]+(?:\.\d{2})?)\s*/?\s*(?:per month|month(?:ly)?)(?:[^.]*?=\s*\$([\d,]+(?:\.\d{2})?)\s*annually)?",
    re.I,
)
FX_FEE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*%\s*(?:service charge|fee|conversion)[^.]*(?:foreign|outside canada|currencies other)", re.I
)
INCOME_RE = re.compile(r"minimum\s+(?:personal\s+)?income[^.\d$]{0,30}\$([\d,]+)", re.I)
HOUSEHOLD_INCOME_RE = re.compile(r"(?:household|family)\s+income[^.\d$]{0,30}\$([\d,]+)", re.I)
PURCHASE_APR_RE = re.compile(
    r"(?:purchases?|standard rate|annual interest rate)[^.]{0,40}?(\d+(?:\.\d+)?)\s*%", re.I
)
CASH_APR_RE = re.compile(
    r"(?:(?:cash|funds)\s+advances?[^.]{0,60}?(\d+(?:\.\d+)?)\s*%)"
    r"|(?:(\d+(?:\.\d+)?)\s*%\s*on\s+(?:cash|funds)\s+advances)",
    re.I,
)

# Welcome bonuses: points amounts possibly separated from the word 'points' by
# program names / trademark glyphs ("Earn 60,000 Aeroplan ® * points").
# Also CIBC-style totals without 'earn': "Get a total of up to 35,000 Aventura Points".
WB_POINTS_RE = re.compile(
    r"(?:[Ee]arn|[Gg]et|[Rr]eceive)\s+(?:a total of\s+)?(?:up to\s+)?(?:a welcome bonus of\s+)?"
    r"([\d,]{3,})(?:[^\d.]{0,45}?)?\s+[Pp]oints\b"
)
WB_CASH_RE = re.compile(
    r"[Ee]arn\s+(?:up to\s+)?(?:\$|(\d+)\s*)([\d,]+(?:\.\d{2})?)\s*(?:cash ?back|dollars)",
    re.I,
)
MSR_MONTHS_RE = re.compile(
    r"(?:spending|spend)s?[^.]{0,25}?\$([\d,]+)[^.]{0,90}?(?:first\s+|\w+\s)?(\d+)\s*months?\b",
    re.I,
)
MSR_DAYS_RE = re.compile(
    r"(?:spending|spend)s?[^.]{0,25}?\$([\d,]+)[^.]{0,90}?within\s+(\d{2,3})\s*days\b",
    re.I,
)
# CIBC: "when you spend $3,000 or more in the first 4 monthly statement periods"
MSR_STATEMENT_RE = re.compile(
    r"(?:spending|spend)s?[^.]{0,25}?\$([\d,]+)[^.]{0,90}?first\s+(\d+)\s*monthly\s+statement\s+periods?\b",
    re.I,
)
# CIBC points earn lines: "2 points for every $1 spent on eligible travel ...",
# "1.5 point for every $1 you spend at eligible gas stations, grocery stores ...",
# "1.5 points for every eligible $1 you spend at participating Hyatt hotels".
POINTS_PER_DOLLAR_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*points?\s+for\s+(?:every|each)\s+(?:eligible\s+)?"
    r"\$1(?:\s+(?:you\s+)?spend(?:ing)?|\s+spent)?\b",
    re.I,
)
LATER_SPEND_RE = re.compile(
    r"(?:spending|spend)\s+\$([\d,]+)[^.]{0,70}?\bmonth\s+(\d{1,2})\b", re.I
)
ELIGIBILITY_NOTES_RE = re.compile(
    r"(?:Current or former [Cc]ardmembers|not eligible[^.]{0,120}|account must be in good standing[^.]{0,80})\.?",
    re.I,
)
FIRST_YEAR_FREE_RE = re.compile(r"first year free", re.I)

# Earn-rate tiles: "3X AEROPLAN POINTS On Air Canada", "5X POINTS On eats & drinks"
EARN_TILE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*[xX]\s+(?:[A-Z][A-Za-z®*'&+.\s]*?\s+)?(?:POINTS|points|cash ?back)"
    r"\s+[Oo]n\s+",
)
# Sentences: "Earn 5 points for every $1 ...", "Earn 4% cash back ...", "Earn 2% cashback"
# "Earn 5 points for every $1 ...", "Earn 4% cash back ..." — but NOT marketing
# multipliers like "Earn 3X the points on flights" (the 'x the' lookahead), which
# describe a category rate already captured by tiles/ppd and would corrupt base.
EARN_LINE_RE = re.compile(
    r"[Ee]arn\s+(\d+(?:\.\d+)?)\s*(points|point|x(?!\s*the\b)|%)(?:\s*cash\s?back)?"
)
# Table/feature copy without a verb: "4% cash back on gas and groceries"
# (?<![\d.]) prevents "1.25%" matching as "25%".
PCT_BACK_RE = re.compile(
    r"(?<![\d.])(\d+(?:\.\d+)?)\s*%\s*(?:unlimited\s+)?cash ?back(?:\s*(?:on|in|at)\s+([^.;()]{3,80}))?",
    re.I,
)

CATEGORY_HINTS = {
    "grocery": ["grocery", "supermarket", "groceries"],
    "gas": ["gas station", "fuel", "gas stations", "electric vehicle charging"],
    "dining": ["restaurant", "dining", "food delivery", "eats & drinks", "eats",
               "coffee shop", "bar ", "fast food"],
    "travel_air": ["airline", "air canada", "flight", "westjet", "air travel"],
    "travel_hotel": ["hotel", "motel", "hyatt", "marriott", "hilton", "bonvoy", "hotels"],
    "travel_other": ["car rental", "car rentals", "vacation", "tour ", "cruise", "travel"],
    "transit_rideshare": ["transit", "rideshare", "uber", "lyft", "taxi", "commuter",
                          "public transportation", "transportation"],
    "streaming_subs": ["streaming", "subscription", "digital media", "netflix", "spotify"],
    "drugstore": ["drugstore", "drug store", "drug stores", "pharmacy"],
    "recurring_bills": ["recurring bill", "utility bills", "phone bills", "recurring payment"],
    "entertainment": ["entertainment", "theatre", "concert", "movie theatre"],
    "retail_online": ["online retail", "e-commerce"],
    "retail_other": ["department store", "home improvement", "furniture", "office supply"],
}


def match_category(text_lower: str, exclude: set[str] | None = None) -> str | None:
    exclude = exclude or set()
    for slug, hints in CATEGORY_HINTS.items():
        if slug in exclude:
            continue
        if any(h in text_lower for h in hints):
            return slug
    return None


def match_all_categories(text_lower: str) -> list[str]:
    """All taxonomy slugs hinted in a context string.

    Used for CIBC-style grouped earn lines ("at eligible gas stations, electric
    vehicle charging stations, grocery stores and drug stores") where one rate
    spans several categories — each gets its own EarnRate row.
    """
    return [
        slug
        for slug, hints in CATEGORY_HINTS.items()
        if any(h in text_lower for h in hints)
    ]


def is_base_context(text_lower: str) -> bool:
    """True when an earn-line context describes the base/all-other rate."""
    return any(
        k in text_lower
        for k in (
            "everything else",
            "everywhere else",
            "all other purchases",
            "all other spend",
            "all purchases",
            "all other spending",
            "everyday purchases",
        )
    )


def tile_title_category(title: str) -> str | None | object:
    """Map an earn-tile title ('Air Canada', 'everything else') to a taxonomy slug.
    Returns the sentinel BASE_SENTINEL for base-rate titles, None if unknown."""
    lowered = title.lower().strip()
    if not lowered or any(
        k in lowered
        for k in ("everything else", "all other", "everyday spending", "all purchases", "everyday purchases")
    ):
        return BASE_SENTINEL
    return match_category(lowered)


BASE_SENTINEL = "__base__"
