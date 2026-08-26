"""Run summary: new / updated / unchanged / failed counts + review backlog (docs/04 §9.2)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Outcome:
    card_slug: str
    status: str  # new | updated | unchanged | failed
    path: str = ""
    detail: str = ""


@dataclass
class RunReport:
    outcomes: list[Outcome] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    def render(self) -> str:
        self.counts = {}
        for o in self.outcomes:
            self.counts[o.status] = self.counts.get(o.status, 0) + 1
        lines = []
        width = max((len(o.card_slug) for o in self.outcomes), default=0)
        for o in self.outcomes:
            suffix = f"  [{o.detail}]" if o.detail else ""
            target = o.path or ""
            lines.append(f"{o.status:<10} {o.card_slug:<{width}} {target}{suffix}")
        summary = "  ".join(f"{k}={v}" for k, v in sorted(self.counts.items()))
        lines.append("")
        lines.append(f"summary: {summary or 'nothing scraped'}")
        return "\n".join(lines)
