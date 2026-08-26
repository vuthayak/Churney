"""Pydantic schemas mirroring docs/03-data-model.md (docs/04 §9.2).

Conventions carried over from the data model:
- Money as integer minor units (cents).
- Every fact carries `source_url` + `verified_at` where applicable.
- Unparseable fields emit as null plus an entry in `needs_manual_review` —
  never guessed values.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION = "1"

# Spec 02 §3.3 category taxonomy v1 (closed set, stable slugs)
CATEGORY_SLUGS_V1 = frozenset(
    {
        "grocery",
        "dining",
        "gas",
        "transit_rideshare",
        "travel_air",
        "travel_hotel",
        "travel_other",
        "drugstore",
        "streaming_subs",
        "recurring_bills",
        "entertainment",
        "retail_online",
        "retail_other",
        "other",
    }
)


class Network(StrEnum):
    AMEX = "amex"
    VISA = "visa"
    MASTERCARD = "mastercard"


class RewardKind(StrEnum):
    POINTS = "points"
    CASHBACK = "cashback"
    BONUS_DOLLARS = "bonus_dollars"


class Card(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    issuer_slug: str
    name: str
    network: Network
    program_slug: str
    card_type: Literal["personal", "business"]
    status: Literal["live", "retired"] = "live"
    page_url: str | None = None


class CardVersion(BaseModel):
    """Effective-dated terms snapshot for one scrape pass."""

    model_config = ConfigDict(extra="forbid")

    valid_from: date
    annual_fee_minor: int | None = None
    extra_card_fee_minor: int | None = None
    fx_fee_pct: float | None = None  # typically 2.5 [VERIFY]
    income_req_personal: int | None = None  # whole dollars
    income_req_household: int | None = None
    purchase_apr: float | None = None
    cash_apr: float | None = None
    source_url: str

    @field_validator("annual_fee_minor", "extra_card_fee_minor")
    @classmethod
    def _nonnegative_money(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("fee must be non-negative minor units")
        return v


class EarnRate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_slug: str | None = None  # None = base rate
    rate: float  # multiplier (points) or fraction of spend (cashback, 0.02 = 2%)
    kind: RewardKind
    cap_amount_minor: int | None = None  # boosted-portion cap
    cap_period: Literal["monthly", "annual"] | None = None
    excluded: bool = False  # category earns nothing under this structure
    notes: str | None = None
    source_url: str

    @field_validator("category_slug")
    @classmethod
    def _known_category(cls, v: str | None) -> str | None:
        if v is not None and v not in CATEGORY_SLUGS_V1:
            raise ValueError(f"unknown category slug {v!r} (taxonomy v1)")
        return v


class AlternateOffer(BaseModel):
    """Referral portal / GCR / limited-time variant of the canonical public offer."""

    model_config = ConfigDict(extra="forbid")

    headline: str
    channel: str  # e.g. 'referral', 'gcr', 'limited_time'
    min_spend_minor: int | None = None
    deadline_days: int | None = None
    reward_points: int | None = None
    reward_cashback_minor: int | None = None
    source_url: str
    seen_on: date


class Offer(BaseModel):
    """Canonical public welcome offer."""

    model_config = ConfigDict(extra="forbid")

    headline: str
    min_spend_minor: int | None = None
    deadline_days: int | None = None
    reward_points: int | None = None
    reward_cashback_minor: int | None = None
    eligibility_notes: str | None = None
    first_year_free: bool | None = None
    alternate_offers: list[AlternateOffer] = Field(default_factory=list)
    source_url: str
    verified_at: datetime


class ReviewItem(BaseModel):
    """Something the parser could not determine reliably; requires human review."""

    model_config = ConfigDict(extra="forbid")

    field: str
    reason: str


class CardFile(BaseModel):
    """Envelope written to data/cards/<slug>.json."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    card: Card
    card_version: CardVersion
    earn_rates: list[EarnRate] = Field(default_factory=list)
    offers: list[Offer] = Field(default_factory=list)
    needs_manual_review: list[ReviewItem] = Field(default_factory=list)
    content_hash: str | None = None  # sha256 of the page this data came from
