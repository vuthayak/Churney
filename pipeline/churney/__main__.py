"""CLI entry point: python -m churney scrape <issuer> | scrape all [--force] [--limit N]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from churney.config import load_sources
from churney.fetch import Fetcher
from churney.report import RunReport

PIPELINE_DIR = Path(__file__).resolve().parent.parent


def make_fetcher(source, cache_dir: Path):
    if source.fetch_mode == "playwright":
        from churney.playwright_fetch import PlaywrightFetcher

        return PlaywrightFetcher(cache_dir)
    from churney.fetch import Fetcher

    return Fetcher(cache_dir)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="churney", description="Churney scraper pipeline")
    sub = p.add_subparsers(dest="command", required=True)
    scrape = sub.add_parser("scrape", help="scrape one issuer or 'all'")
    scrape.add_argument("source", help="source name from sources.yaml, or 'all'")
    scrape.add_argument("--force", action="store_true", help="re-parse unchanged pages")
    scrape.add_argument("--limit", type=int, default=None, help="max card URLs to process")
    build_ui = sub.add_parser("build-ui", help="regenerate ui/cards.js from data/cards")
    sub.add_parser("verify-report", help="generate data/verification-checklist.md for manual review")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "build-ui":
        from churney.build_ui import build

        build()
        return 0

    if args.command == "verify-report":
        from churney.verify_report import generate

        generate()
        return 0

    sources = load_sources(PIPELINE_DIR / "sources.yaml")

    # Import after arg parsing so --help is instant.
    from churney.fetch import Fetcher
    from scrapers import SCRAPER_REGISTRY

    names = list(sources) if args.source == "all" else [args.source]
    report = RunReport()
    had_error = False
    for name in names:
        source = sources.get(name)
        if source is None:
            print(f"error: unknown source {name!r} (known: {', '.join(sources)})", file=sys.stderr)
            had_error = True
            continue
        try:
            source.assert_crawlable()
        except Exception as exc:  # noqa: BLE001 - compliance gates are user-facing
            print(f"skip {name}: {exc}", file=sys.stderr)
            had_error = True
            continue
        cls = SCRAPER_REGISTRY.get(name)
        if cls is None:
            print(f"error: no scraper registered for {name!r}", file=sys.stderr)
            had_error = True
            continue
        fetcher = make_fetcher(source, PIPELINE_DIR / "cache")
        try:
            scraper = cls(fetcher, source, PIPELINE_DIR / "data")
            report.outcomes.extend(scraper.run(force=args.force, limit=args.limit))
        finally:
            fetcher.close()

    print(report.render())
    return (
        1
        if had_error
        or (report.outcomes and all(o.status == "failed" for o in report.outcomes))
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
