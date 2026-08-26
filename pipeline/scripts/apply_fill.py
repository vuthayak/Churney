"""Apply an LLM fill patch file (data/fill_*.json) to emitted card JSONs.

Idempotent: re-running against an already-patched repo is a no-op (rates,
offers, offer fields, version fields and review items are all checked before
writing). Every touched card is re-validated through the Pydantic models.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

from churney.emit import emit, load_card_file  # noqa: E402


def _resolve_review(card_file, needle: str) -> None:
    """Remove review items matching the needle.

    Plain needle matches the field name (substring). A 'field:reason-fragment'
    form additionally constrains on the reason text for surgical removal.
    """
    if ":" in needle:
        field_frag, reason_frag = needle.split(":", 1)
        card_file.needs_manual_review = [
            r for r in card_file.needs_manual_review
            if not (field_frag in r.field and reason_frag in r.reason)
        ]
        return
    card_file.needs_manual_review = [
        r for r in card_file.needs_manual_review if needle not in r.field
    ]


def _review_present(card_file, item: dict) -> bool:
    return any(r.field == item["field"] and r.reason == item["reason"] for r in card_file.needs_manual_review)


def apply(patch_path: Path) -> int:
    patches = json.loads(patch_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    applied = skipped = 0

    for slug, patch in patches.items():
        if slug.startswith("_"):
            continue
        path = PIPELINE_DIR / "data" / "cards" / f"{slug}.json"
        if not path.exists():
            print(f"SKIP {slug}: no such card file")
            skipped += 1
            continue
        cf = load_card_file(path)
        marker = f"[FILL {patch_path.stem}]"

        program_changed = "program_slug" in patch and cf.card.program_slug != patch["program_slug"]
        if program_changed:
            cf.card.program_slug = patch["program_slug"]

        def rate_present(r):
            return any(
                e.category_slug == r["category_slug"]
                and float(e.rate) == float(r["rate"])
                and e.kind.value == r["kind"]
                for e in cf.earn_rates
            )

        cf_before = None
        if "rates_replace" in patch:
            from churney.emit import semantic_dict

            cf_before = semantic_dict(cf)

        new_rates = [r for r in patch.get("rates_add", []) if not rate_present(r)]

        # Full replacement of the earn structure (human-verified corrections).
        rates_replaced = False
        if "rates_replace" in patch:
            from churney.models import EarnRate, RewardKind

            cf.earn_rates = [
                EarnRate(
                    category_slug=r.get("category_slug"),
                    rate=r["rate"],
                    kind=RewardKind(r["kind"]),
                    cap_amount_minor=r.get("cap_amount_minor"),
                    cap_period=r.get("cap_period"),
                    notes=r.get("notes"),
                    source_url=cf.card.page_url or "",
                )
                for r in patch["rates_replace"]
            ]
            rates_replaced = semantic_dict(cf) != cf_before
        existing_headlines = {o.headline for o in cf.offers}
        new_offers = [
            o for o in patch.get("offers_add", []) if o["headline"] not in existing_headlines
        ]

        for rate in new_rates:
            from churney.models import EarnRate, RewardKind

            cf.earn_rates.append(
                EarnRate(
                    category_slug=rate["category_slug"],
                    rate=rate["rate"],
                    kind=RewardKind(rate["kind"]),
                    notes=rate.get("notes"),
                    source_url=cf.card.page_url or "",
                )
            )

        for o in new_offers:
            from churney.models import Offer

            cf.offers.append(
                Offer(
                    headline=o["headline"],
                    min_spend_minor=o.get("min_spend_minor"),
                    deadline_days=o.get("deadline_days"),
                    reward_points=o.get("reward_points"),
                    reward_cashback_minor=o.get("reward_cashback_minor"),
                    first_year_free=o.get("first_year_free"),
                    eligibility_notes=o.get("eligibility_notes"),
                    source_url=cf.card.page_url or "",
                    verified_at=now,
                )
            )

        op = patch.get("offer_patch")
        offer_changed = False
        if op and cf.offers:
            offer = cf.offers[0]
            for key in (
                "headline",
                "min_spend_minor",
                "deadline_days",
                "reward_points",
                "reward_cashback_minor",
                "first_year_free",
            ):
                if key in op and getattr(offer, key, None) != op[key]:
                    setattr(offer, key, op[key])
                    offer_changed = True
            append_note = op.get("eligibility_notes_append")
            if append_note and marker not in (offer.eligibility_notes or ""):
                existing = (offer.eligibility_notes or "").strip()
                offer.eligibility_notes = (
                    f"{existing} {marker}: {append_note}"
                    if existing
                    else f"{marker}: {append_note}"
                )
                offer_changed = True

            # Full replacement of alternate_offers (e.g. human-verified T&C
            # components superseding parser-inferred ones).
            alts = op.get("alternate_offers")
            if alts is not None:
                from churney.models import AlternateOffer

                new_alts = [
                    AlternateOffer(
                        headline=a["headline"],
                        channel=a.get("channel", "tnc_verified"),
                        min_spend_minor=a.get("min_spend_minor"),
                        deadline_days=a.get("deadline_days"),
                        reward_points=a.get("reward_points"),
                        reward_cashback_minor=a.get("reward_cashback_minor"),
                        source_url=cf.card.page_url or "",
                        seen_on=now.date(),
                    )
                    for a in alts
                ]
                if cf.offers[0].alternate_offers != new_alts:
                    cf.offers[0].alternate_offers = new_alts
                    offer_changed = True

        vp = patch.get("version_patch", {})
        version_changed = any(getattr(cf.card_version, k, None) != v for k, v in vp.items())
        for key, value in vp.items():
            setattr(cf.card_version, key, value)

        review_before = {(r.field, r.reason) for r in cf.needs_manual_review}
        for needle in patch.get("review_resolve", []):
            _resolve_review(cf, needle)
        for item in patch.get("review_add", []):
            from churney.models import ReviewItem

            if not _review_present(cf, item):
                cf.needs_manual_review.append(ReviewItem(**item))
        review_after = {(r.field, r.reason) for r in cf.needs_manual_review}
        review_changed = review_before != review_after

        if not any([new_rates, new_offers, offer_changed, version_changed, review_changed,
                    rates_replaced, program_changed]):
            print(f"skip {slug}: already applied")
            continue

        emit(cf, PIPELINE_DIR / "data")
        applied += 1

    print(f"\napplied={applied} skipped={skipped}")
    return 0 if not skipped else 1


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else PIPELINE_DIR / "data" / "fill_2026-08-24.json"
    raise SystemExit(apply(target))
