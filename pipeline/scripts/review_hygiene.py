"""Reconcile needs_manual_review entries with actual card data.

After fill patches add rates/offers/programs, stale parser complaints ("no earn
patterns found", "no welcome-bonus pattern found") can linger. This sweep drops
review items contradicted by the card's current state so the verification
checklist only lists genuinely actionable items.

Run after all apply_fill passes: uv run python scripts/review_hygiene.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

from churney.emit import emit, load_card_file  # noqa: E402


def is_stale(cf, r) -> bool:
    field, reason = r.field, r.reason
    if field == "earn_rates":
        if "no earn patterns found" in reason and cf.earn_rates:
            return True
        if "no base-rate pattern" in reason and any(
            e.category_slug is None for e in cf.earn_rates
        ):
            return True
    if (
        field == "program_slug"
        and "could not infer from name" in reason
        and cf.card.program_slug != "unknown"
    ):
        return True
    if "no welcome-bonus pattern found" in reason and cf.offers:
        return True
    # documented no-rewards card: absent earn/offers is expected and already
    # explained by the program note
    if (
        cf.card.program_slug == "none"
        and field in ("earn_rates", "offers", "program_slug")
        and "corporate expense card" not in reason
    ):
        return True
    # charge-card note supersedes a bare "APR pattern not found"
    if (
        field == "purchase_apr"
        and "pattern not found" in reason
        and any("charge card" in x.reason for x in cf.needs_manual_review)
    ):
        return True
    if (
        field == "annual_fee_minor"
        and "fee pattern not found" in reason
        and cf.card_version.annual_fee_minor
        and cf.card_version.annual_fee_minor > 0
    ):
        return True
    if (
        field == "earn_rates"
        and "unmapped earn-tile" in reason
        and cf.earn_rates
    ):
        return True
    if (
        field == "fx_fee_pct"
        and "[VERIFY]" in reason
        and any(
            "VERIFIED" in x.reason and x.field == "fx_fee_pct"
            for x in cf.needs_manual_review
        )
    ):
        return True
    return False


def dedupe_reviews(reviews):
    """Keep one review item per field, preferring VERIFIED and richer notes."""
    by_field: dict[str, list] = {}
    for r in reviews:
        by_field.setdefault(r.field, []).append(r)

    def score(r) -> tuple[int, int]:
        s = 0
        if "VERIFIED" in r.reason:
            s += 100
        if "was mis-parsed" in r.reason:
            s += 10
        return (s, len(r.reason))

    return [max(items, key=score) for items in by_field.values()]


def main() -> int:
    changed = removed = 0
    for f in sorted((PIPELINE_DIR / "data" / "cards").glob("*.json")):
        cf = load_card_file(f)
        kept = dedupe_reviews(
            [r for r in cf.needs_manual_review if not is_stale(cf, r)]
        )
        if len(kept) != len(cf.needs_manual_review):
            removed += len(cf.needs_manual_review) - len(kept)
            cf.needs_manual_review = kept
            emit(cf, PIPELINE_DIR / "data")
            changed += 1
    print(f"swept {removed} stale review items across {changed} cards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
