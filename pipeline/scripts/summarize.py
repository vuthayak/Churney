"""Summarize emitted card files + review backlog."""

import json
from collections import Counter
from pathlib import Path

files = sorted(Path("data/cards").glob("*.json"))
biz = sum(
    1 for f in files if json.loads(f.read_text(encoding="utf-8"))["card"]["card_type"] == "business"
)
print(f"{len(files)} cards ({biz} business)")
c = Counter()
for f in files:
    d = json.loads(f.read_text(encoding="utf-8"))
    card, v = d["card"], d["card_version"]
    fee = (v.get("annual_fee_minor") or 0) / 100
    print(
        f"  {card['name'][:42]:<44} {card['card_type']:<8} "
        f"{card['program_slug']:<15} ${fee:>7.2f} rates={len(d['earn_rates'])} "
        f"offers={len(d['offers'])} review={len(d['needs_manual_review'])}"
    )
    for i in d["needs_manual_review"]:
        c[i["field"]] += 1
print()
print("backlog:", dict(c.most_common()))
