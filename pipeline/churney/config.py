"""sources.yaml loading + pre-crawl compliance gates (docs/04 §2, §9.5)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml


class SourceNotCrawlable(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceConfig:
    name: str
    issuer_slug: str
    display_name: str
    allowed: bool
    tos_reviewed_at: date | None
    cadence: str
    fetch_mode: str
    entry_urls: list[str]
    link_pattern: str | None = None
    card_urls: list[str] | None = None
    notes: str | None = None

    def assert_crawlable(self) -> None:
        if not self.allowed:
            raise SourceNotCrawlable(
                f"source {self.name!r} has allowed=false in sources.yaml"
            )
        if self.tos_reviewed_at is None:
            raise SourceNotCrawlable(
                f"source {self.name!r}: ToS review not recorded. A human must review "
                f"the site's terms and robots.txt, then set `tos_reviewed_at` in "
                f"sources.yaml before first crawl (docs/04 §2)."
            )


def load_sources(path: Path) -> dict[str, SourceConfig]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    out: dict[str, SourceConfig] = {}
    for name, cfg in (raw.get("sources") or {}).items():
        tos = cfg.get("tos_reviewed_at")
        out[name] = SourceConfig(
            name=name,
            issuer_slug=cfg["issuer_slug"],
            display_name=cfg.get("display_name", name),
            allowed=bool(cfg.get("allowed", False)),
            tos_reviewed_at=date.fromisoformat(str(tos)) if tos else None,
            cadence=cfg.get("cadence", "weekly"),
            fetch_mode=cfg.get("fetch_mode", "httpx"),
            entry_urls=list(cfg.get("entry_urls", [])),
            link_pattern=cfg.get("link_pattern"),
            card_urls=list(cfg.get("card_urls") or []),
            notes=cfg.get("notes"),
        )
    return out
