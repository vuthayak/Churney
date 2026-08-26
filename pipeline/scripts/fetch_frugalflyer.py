"""Fetch Frugal Flyer card pages for gap-filling / cross-checking.

Frugal Flyer (frugalflyer.ca) publishes a structured "Fees & Eligibility" block
per card (income reqs, annual fee, FX fee, APRs) that issuer pages often omit.
This is a *manual reference source*: robots.txt permits card pages (checked
2026-08-24), fetched politely via the shared compliance-gated Fetcher.

Usage: uv run python scripts/fetch_frugalflyer.py [--limit N]
Writes data/frugalflyer_map.json (slug -> url) and data/frugalflyer_facts.json.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

FEES_BLOCK_RE = re.compile(
    r"Fees & Eligibility\s*"
    r"Personal Income\s*(?:\$\s?[\d,]+|—|-)?\s*"
    r"Household Income\s*(?:\$\s?[\d,]+|—|-)?\s*"
    r"Annual Fee\s*\$\s?(?P<annual_fee>[\d,]+)\s*"
    r"Foreign Exchange Fee\s*(?P<fx_fee>[\d.]+)\s*%\s*"
    r"(?:Purchase Rate\s*(?P<purchase_apr>[\d.]+)\s*%\s*)?"
    r"(?:Cash Advance Rate\s*(?P<cash_apr>[\d.]+)\s*%)?",
    re.I,
)


def main() -> int:
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    from churney.fetch import Fetcher

    map_path = PIPELINE_DIR / "data" / "frugalflyer_map.json"
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    # drop weak/unmatched entries
    todo = {
        slug: url
        for slug, (url, score) in sorted(mapping.items())
        if url and score >= 0.5
    }
    if limit:
        todo = dict(list(todo.items())[:limit])

    facts_path = PIPELINE_DIR / "data" / "frugalflyer_facts.json"
    facts = json.loads(facts_path.read_text(encoding="utf-8")) if facts_path.exists() else {}

    fetcher = Fetcher(PIPELINE_DIR / "cache", min_interval=5.0)
    try:
        for i, (slug, url) in enumerate(todo.items(), 1):
            if slug in facts:
                continue
            try:
                page = fetcher.fetch(url)
            except Exception as exc:  # noqa: BLE001
                print(f"[{i}/{len(todo)}] FAIL {slug}: {exc}")
                continue
            from bs4 import BeautifulSoup

            text = re.sub(
                r"\s+", " ",
                BeautifulSoup(page.html, "lxml").get_text(" ", strip=True),
            )
            m = FEES_BLOCK_RE.search(text)
            if not m:
                print(f"[{i}/{len(todo)}] no fees block: {slug}")
                continue
            g = {k: v for k, v in m.groupdict().items() if v}
            facts[slug] = {"url": url, **g}
            print(
                f"[{i}/{len(todo)}] {slug}: fx={g.get('fx_fee')}% "
                f"apr={g.get('purchase_apr')} fee=${g.get('annual_fee')}"
            )
        facts_path.write_text(json.dumps(facts, indent=1), encoding="utf-8")
        print(f"\nwrote {facts_path} ({len(facts)} cards)")
    finally:
        fetcher.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
