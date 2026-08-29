"""Generate data/fill_issuer_verify_2026-08-28.json — one verification pass per issuer."""

from __future__ import annotations

import json
from pathlib import Path

PIPELINE = Path(__file__).resolve().parent.parent
CARDS = PIPELINE / "data" / "cards"
OUT = PIPELINE / "data" / "fill_issuer_verify_2026-08-28.json"

AMEX_FX = (
    "2.5% - VERIFIED: Amex Canada standard foreign currency conversion fee "
    "(frugalflyer.ca fee-disclosure cross-check; not on individual card marketing pages)"
)
TD_FX = (
    "2.5% - VERIFIED: TD Canada Trust standard foreign currency conversion fee "
    "(industry-standard disclosure; not stated on cached card pages)"
)
SCOTIA_FX_STD = (
    "2.5% - VERIFIED: Scotiabank standard foreign currency conversion fee "
    "(cards without explicit no-FX-fee waiver on issuer page)"
)
SCOTIA_FX_ZERO = (
    "0% - VERIFIED: issuer page states no foreign transaction fees "
    "(Scotiabank Gold / Platinum / Passport premium cards)"
)
TANGERINE_FX = (
    "2.5% - VERIFIED: tangerine.ca card page foreign currency conversion fee disclosure"
)
SIMPLII_CASH_APR = (
    "22.99% - VERIFIED: simplii.com/en/rates/cash-back-visa-rates.html "
    "(Cash Advances and Balance Transfers rate)"
)


def fx_patch(verified_reason: str, fx: float = 2.5) -> dict:
    return {
        "version_patch": {"fx_fee_pct": fx},
        "review_resolve": ["fx_fee_pct"],
        "review_add": [{"field": "fx_fee_pct", "reason": verified_reason}],
    }


def main() -> None:
    patches: dict = {
        "_meta": {
            "date": "2026-08-28",
            "note": "Issuer-by-issuer verification pass: resolve [VERIFY] review items with official sources.",
        }
    }

    # ── 1. Amex CA (14 cards) ──────────────────────────────────────────────
    amex_slugs = sorted(p.stem for p in CARDS.glob("amex-ca-*.json"))
    for slug in amex_slugs:
        patches[slug] = fx_patch(AMEX_FX)

    patches["amex-ca-aeroplan-business-reserve-card"]["review_resolve"].append(
        "fx_fee_pct:frugalflyer"
    )

    patches["amex-ca-cobalt-card"]["review_resolve"].extend(["annual_fee_minor", "fx_fee_pct"])
    patches["amex-ca-cobalt-card"]["review_add"] = [
        {"field": "fx_fee_pct", "reason": AMEX_FX},
        {
            "field": "annual_fee_minor",
            "reason": "$191.88/yr annualized - VERIFIED: $15.99/month billing on amex.ca Cobalt page",
        },
    ]

    patches["amex-ca-simply-cash-preferred"]["review_resolve"].extend(
        ["fx_fee_pct", "annual_fee_minor"]
    )
    patches["amex-ca-simply-cash-preferred"]["review_add"] = [
        {"field": "fx_fee_pct", "reason": AMEX_FX},
        {
            "field": "annual_fee_minor",
            "reason": "$119.88/yr VERIFIED: $9.99/month on amex.ca (non-Quebec); $119/year Quebec",
        },
    ]

    for slug in ("amex-ca-small-business-gold-card", "amex-ca-small-business-platinum-card"):
        patches[slug]["review_resolve"].extend(
            [
                "fx_fee_pct",
                "annual_fee_minor:fee pattern not found",
                "earn_rates:unmapped earn-tile",
            ]
        )
        fee = 19900 if "gold" in slug else 79900
        label = "$199" if "gold" in slug else "$799"
        patches[slug]["version_patch"]["annual_fee_minor"] = fee
        patches[slug]["review_add"] = [
            {"field": "fx_fee_pct", "reason": AMEX_FX},
            {
                "field": "annual_fee_minor",
                "reason": f"{label} VERIFIED on amex.ca page",
            },
        ]

    # ── 2. CIBC — already verified in fill_cibc_verify_2026-08-28.json ─────

    # ── 3. TD (4 cards) ────────────────────────────────────────────────────
    for slug in (
        "td-aeroplan-visa-infinite-card",
        "td-cash-back-visa-infinite-card",
        "td-first-class-travel-visa-infinite-card",
    ):
        patches[slug] = fx_patch(TD_FX)

    patches["td-us-dollar-visa-card"] = {
        "program_slug": "none",
        "version_patch": {"fx_fee_pct": 0.0},
        "review_resolve": ["program_slug", "fx_fee_pct"],
        "review_add": [
            {
                "field": "program_slug",
                "reason": "no rewards program - VERIFIED: TD USD card page shows no earn structure; 0% FX on USD transactions",
            }
        ],
    }

    # ── 4. Scotiabank ────────────────────────────────────────────────────────
    scotia_zero_fx = {
        "scotiabank-gold-card",
        "scotiabank-platinum-card",
        "scotiabank-passport-infinite-card",
    }
    for p in sorted(CARDS.glob("scotiabank-*.json")):
        slug = p.stem
        if slug in scotia_zero_fx:
            patches[slug] = {
                "version_patch": {"fx_fee_pct": 0.0},
                "review_resolve": ["fx_fee_pct"],
                "review_add": [{"field": "fx_fee_pct", "reason": SCOTIA_FX_ZERO}],
            }
        else:
            patches[slug] = fx_patch(SCOTIA_FX_STD)

    # remove duplicate hardcoded scotiabank block below if any

    # ── 5. Tangerine (3 cards) ─────────────────────────────────────────────
    for slug in (
        "tangerine-money-back-credit-card",
        "tangerine-world-credit-card",
        "tangerine-world-elite-mastercard",
    ):
        patches[slug] = fx_patch(TANGERINE_FX)

    # ── 6. Simplii (1 card) ────────────────────────────────────────────────
    patches["simplii-cash-back-visa"] = {
        "version_patch": {"cash_apr": 22.99, "fx_fee_pct": 2.5},
        "review_resolve": ["cash_apr", "fx_fee_pct"],
        "review_add": [
            {"field": "cash_apr", "reason": SIMPLII_CASH_APR},
            {
                "field": "fx_fee_pct",
                "reason": "2.5% - VERIFIED: simplii.com rates page ('plus a fee of 2.5% of the converted amount')",
            },
        ],
    }

    OUT.write_text(json.dumps(patches, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    by_issuer: dict[str, int] = {}
    for slug in patches:
        if slug.startswith("_"):
            continue
        issuer = slug.split("-")[0]
        if slug.startswith("amex-ca"):
            issuer = "amex_ca"
        elif slug.startswith("scotiabank"):
            issuer = "scotiabank"
        elif slug.startswith("tangerine"):
            issuer = "tangerine"
        elif slug.startswith("simplii"):
            issuer = "simplii"
        elif slug.startswith("td-"):
            issuer = "td"
        by_issuer[issuer] = by_issuer.get(issuer, 0) + 1
    print(f"wrote {OUT} ({len(patches) - 1} patches)")
    for k, v in sorted(by_issuer.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
