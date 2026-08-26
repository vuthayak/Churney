"""Generate data/verification-checklist.md for manual [VERIFY] passes.

Groups cards by issuer with all captured facts in human-readable form plus the
source URL, so a human can tick off each card against the live issuer page.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent


def _rate_label(r: dict) -> str:
    if r["kind"] == "cashback":
        return f"{r['rate'] * 100:g}% cash back"
    return f"{r['rate']:g}x points"


def _money(minor: int | None) -> str:
    if minor is None:
        return "— (review)"
    if minor == 0:
        return "$0"
    return f"${minor / 100:,.2f}"


def generate(cards_dir: Path | None = None, out: Path | None = None) -> Path:
    cards_dir = cards_dir or PIPELINE_DIR / "data" / "cards"
    out = out or PIPELINE_DIR / "data" / "verification-checklist.md"

    by_issuer: dict[str, list[dict]] = {}
    for f in sorted(Path(cards_dir).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        by_issuer.setdefault(d["card"]["issuer_slug"], []).append(d)

    lines = [
        "# Manual Verification Checklist",
        "",
        f"Generated {date.today().isoformat()} · "
        f"{sum(len(v) for v in by_issuer.values())} cards across {len(by_issuer)} issuers.",
        "",
        "For each card: open the **source page**, confirm every fact below, then",
        "tick the box. Anything wrong → fix in `data/cards/<slug>.json` and note",
        "`verified_at`. Convention: cashback rates are stored as pct/100",
        "(4% -> `0.04`) but shown here as percentages.",
        "",
    ]

    total_facts = 0
    for issuer in sorted(by_issuer):
        lines += [f"## {issuer}", ""]
        for d in sorted(by_issuer[issuer], key=lambda x: x["card"]["name"]):
            card, v = d["card"], d["card_version"]
            offer = d["offers"][0] if d["offers"] else None
            checks: list[str] = []
            lines.append(f"### ☐ {card['name']}  `{card['slug']}`")
            lines.append("")
            lines.append(f"Source: <{card['page_url']}>")
            lines.append("")

            af = v.get("annual_fee_minor")
            lines.append(f"- Annual fee: **{_money(af)}**")
            total_facts += 1
            extra = v.get("extra_card_fee_minor")
            if extra is not None:
                lines.append(f"- Additional card fee: {_money(extra)}")
                total_facts += 1
            for label, key in (
                ("Purchase APR", "purchase_apr"),
                ("Cash advance APR", "cash_apr"),
                ("FX fee %", "fx_fee_pct"),
            ):
                val = v.get(key)
                lines.append(f"- {label}: {val if val is not None else '— (review)'}")
                total_facts += 1

            if d["earn_rates"]:
                rates = ", ".join(
                    f"{_rate_label(r)} ({r.get('category_slug') or 'base'})"
                    for r in d["earn_rates"]
                )
                lines.append(f"- Earn rates: **{rates}**")
                total_facts += len(d["earn_rates"])
            else:
                lines.append("- Earn rates: ⚠️ none captured")

            if offer:
                reward = ""
                if offer.get("reward_points") is not None:
                    reward = f"{offer['reward_points']:,} points"
                elif offer.get("reward_cashback_minor") is not None:
                    reward = _money(offer["reward_cashback_minor"]) + " cash back"
                msr = offer.get("min_spend_minor")
                dl = offer.get("deadline_days")
                lines.append(
                    f"- Welcome offer: **{offer['headline']}**"
                    + (f" | min spend {_money(msr)}" if msr is not None else "")
                    + (f" | deadline {dl} days" if dl is not None else "")
                    + (f" | reward: {reward}" if reward else "")
                )
                total_facts += 1
                for i, alt in enumerate(offer.get("alternate_offers") or [], 1):
                    lines.append(
                        f"  - Alternate [{alt['channel']}]: {alt['headline']}"
                        + (f" | reward: {alt['reward_points']:,} pts"
                           if alt.get("reward_points") is not None else "")
                    )
                    total_facts += 1

            if d["needs_manual_review"]:
                lines.append(f"- ⚠️ Review items ({len(d['needs_manual_review'])}):")
                for item in d["needs_manual_review"]:
                    lines.append(f"  - **{item['field']}**: {item['reason']}")
            lines.append("")

    lines += [
        "---",
        f"",
        f"~{total_facts} facts to verify. Priority order: fees → earn rates →",
        f"welcome offers → APRs/FX. Fill FX fee once per issuer (most are 2.5%)",
        f"and propagate to every card of that issuer.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    return out
