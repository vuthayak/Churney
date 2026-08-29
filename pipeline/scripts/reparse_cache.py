"""Re-parse all cached pages through current scrapers without network access.

Uses cache/index.json (url -> {body, hash}) written by the Fetcher, runs each
page's registered scraper parse_card(), and re-emits data/cards/<slug>.json with
semantic change detection. Useful after parser improvements: `uv run python
scripts/reparse_cache.py`. Live freshness still requires a real scrape run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

from churney.config import load_sources  # noqa: E402
from churney.emit import card_file_path, emit, load_card_file, semantic_dict  # noqa: E402

HOST_TO_SOURCE = {
    "www.americanexpress.com": "amex_ca",
    "www.td.com": "td",
    "www.cibc.com": "cibc",
    "www.scotiabank.com": "scotiabank",
    "www.tangerine.ca": "tangerine",
    "www.simplii.com": "simplii",
    "www.rbcroyalbank.com": "rbcroyalbank",
    "www.nbc.ca": "nbc",
    "www.bmo.com": "bmo",
    "www.desjardins.com": "desjardins",
    "www.neofinancial.com": "neo",
    "brimfinancial.com": "brim",
}


def _url_allowed(name: str, source, url: str) -> bool:
    """Mirror discovery-time filtering so verification fetches and listing
    pages never become card files."""
    from urllib.parse import urlparse

    path = urlparse(url).path
    if source.card_urls:
        return url.rstrip("/") in {u.rstrip("/") for u in source.card_urls}
    if name == "amex_ca":
        # AmexCaScraper carries its discovery regex + exclusions internally.
        from scrapers.amex_ca import CARD_LINK_RE, EXCLUDED_SLUGS

        m = CARD_LINK_RE.match(path)
        return bool(m) and m.group(1) not in EXCLUDED_SLUGS
    if source.link_pattern:
        import re

        if not re.match(source.link_pattern, path):
            return False
    else:
        return False
    tail = path.rstrip("/").split("/")[-1].removesuffix(".html")
    return not tail.startswith(("compare", "activate"))


def main() -> int:
    from scrapers import SCRAPER_REGISTRY

    sources = load_sources(PIPELINE_DIR / "sources.yaml")
    index = json.loads((PIPELINE_DIR / "cache" / "index.json").read_text(encoding="utf-8"))

    # Never parse listing/entry pages as cards (the live scraper's discovery
    # filters by link_pattern; offline reparse mirrors that by URL).
    entry_urls = {u for src in sources.values() for u in src.entry_urls}

    def is_listing(url: str) -> bool:
        host = url.split("/")[2] if "//" in url else ""
        name = HOST_TO_SOURCE.get(host)
        if name is None or name not in SCRAPER_REGISTRY:
            return True
        if not _url_allowed(name, sources[name], url):
            return True
        tail = url.rstrip("/").split("/")[-1].removesuffix(".html")
        return tail.startswith(("compare", "activate", "browse-all", "manage"))

    counts = {"new": 0, "updated": 0, "unchanged": 0, "failed": 0, "skipped": 0}
    for url, entry in sorted(index.items()):
        if is_listing(url):
            counts["skipped"] += 1
            continue
        name = HOST_TO_SOURCE.get(url.split("/")[2] if "//" in url else "")
        if name is None or name not in SCRAPER_REGISTRY:
            counts["skipped"] += 1
            continue
        body = Path(entry["body"])
        if not body.exists():
            print(f"missing cache body for {url}", file=sys.stderr)
            counts["failed"] += 1
            continue
        try:
            scraper = SCRAPER_REGISTRY[name](None, sources[name], PIPELINE_DIR / "data")
            card_file = scraper.parse_card(body.read_text(encoding="utf-8"), url)
            card_file.content_hash = entry["hash"]
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"FAIL {url}: {exc}", file=sys.stderr)
            counts["failed"] += 1
            continue
        out_path = card_file_path(PIPELINE_DIR / "data", card_file.card.slug)
        old = load_card_file(out_path) if out_path.exists() else None
        emit(card_file, PIPELINE_DIR / "data")
        if old is None:
            status = "new"
        elif semantic_dict(old) == semantic_dict(card_file):
            status = "unchanged"
        else:
            status = "updated"
        counts[status] += 1
        if status != "unchanged":
            print(f"{status:<10} {card_file.card.slug}")
    print()
    print("summary:", "  ".join(f"{k}={v}" for k, v in counts.items()))
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
