"""Spot-check fixed cards: CIBC Dividend scaling + Tangerine WE program."""

import json
from pathlib import Path

for slug in ("cibc-dividend-visa-infinite-card", "tangerine-world-elite-mastercard"):
    d = json.loads(Path(f"data/cards/{slug}.json").read_text(encoding="utf-8"))
    print("===", slug)
    print("  program:", d["card"]["program_slug"])
    for r in d["earn_rates"]:
        if r["kind"] == "cashback":
            label = f"{r['rate'] * 100:g}% cashback"
        else:
            label = f"{r['rate']:g}x points"
        print(f"   {label:<22} {r.get('category_slug') or '(base)'}")
