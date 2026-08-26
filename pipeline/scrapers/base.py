"""IssuerScraper ABC — one module per issuer implements discovery + parsing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path

from churney.config import SourceConfig
from churney.emit import card_file_path, emit, load_card_file, semantic_dict
from churney.fetch import Fetcher
from churney.models import CardFile
from churney.report import Outcome


class IssuerScraper(ABC):
    """Lifecycle per run:
    discover_card_urls() -> fetch each -> skip if unchanged & output exists ->
    parse_card() -> emit JSON -> collect Outcomes for the report.
    """

    issuer_slug: str

    def __init__(self, fetcher: Fetcher, source: SourceConfig, out_dir: Path) -> None:
        self.fetcher = fetcher
        self.source = source
        self.out_dir = Path(out_dir)

    @abstractmethod
    def discover_card_urls(self) -> Iterable[str]:
        """Yield card-detail page URLs from the source's entry pages."""

    @abstractmethod
    def parse_card(self, html: str, url: str) -> CardFile:
        """Parse one card-detail page into a validated CardFile.

        Must never guess: unparseable fields become null plus a
        `needs_manual_review` entry.
        """

    def run(self, *, force: bool = False, limit: int | None = None) -> list[Outcome]:
        self.source.assert_crawlable()
        outcomes: list[Outcome] = []
        urls = list(self.discover_card_urls())
        if limit is not None:
            urls = urls[:limit]
        for url in urls:
            outcomes.append(self._process(url, force=force))
        return outcomes

    def _process(self, url: str, *, force: bool) -> Outcome:
        slug_hint = self._slug_from_url(url)
        out_path = card_file_path(self.out_dir, slug_hint)
        try:
            page = self.fetcher.fetch(url)
        except Exception as exc:  # noqa: BLE001 - report, don't crash the run
            return Outcome(card_slug=slug_hint, status="failed", detail=str(exc))

        # Fast path: markup unchanged (httpx hash match) and we already have output.
        if page.status == "unchanged" and out_path.exists() and not force:
            return Outcome(card_slug=slug_hint, status="unchanged", path=str(out_path))
        try:
            card_file = self.parse_card(page.html, url)
            card_file.content_hash = page.content_hash
            old = load_card_file(out_path) if out_path.exists() else None
            path = emit(card_file, self.out_dir)
        except Exception as exc:  # noqa: BLE001
            return Outcome(card_slug=slug_hint, status="failed", detail=str(exc))

        # Semantic drift: rendered DOM hashes are unstable, so compare parsed data.
        if old is not None:
            status = (
                "unchanged"
                if semantic_dict(old) == semantic_dict(card_file)
                else "updated"
            )
        else:
            status = "new"
        detail = f"{len(card_file.needs_manual_review)} review items" if card_file.needs_manual_review else ""
        return Outcome(
            card_slug=card_file.card.slug,
            status=status,
            path=str(path),
            detail=detail,
        )

    def _slug_from_url(self, url: str) -> str:
        tail = url.rstrip("/").split("/")[-1]
        tail = tail.removesuffix(".html").removesuffix(".aspx")
        return f"{self.issuer_slug.replace('_', '-')}-{tail.lower()}"
