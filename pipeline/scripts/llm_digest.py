"""Build an LLM-review digest of evidence snippets for missing card fields.

For every emitted card JSON with gaps, extracts trimmed context windows around
reward/offer/fee keywords from the cached source page into
data/llm_digest.md. The digest is the input for a manual (LLM-assisted) fill
pass; values are then applied via scripts/apply_fill.py.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

HOST_TO_SOURCE = {
    "www.americanexpress.com": "amex_ca",
    "www.td.com": "td",
    "www.cibc.com": "cibc",
    "www.scotiabank.com": "scotiabank",
    "www.tangerine.ca": "tangerine",
    "www.simplii.com": "simplii",
}

SNIPPET_PATTERNS = [
    r"[^.]{0,140}\d+% cash ?back[^.]{0,160}",
    r"[^.]{0,100}\b\d+ points? for every[^.]{0,160}",
    r"[^.]{0,60}\d+[xX]\s+(?:\w+\s+){0,3}points[^.]{0,120}",
    r"[^.]{0,80}[Ee]arn\s+(?:up to\s+)?[\d,]{3,}[^.]{0,180}",
    r"[^.]{0,80}[Gg]et\s+(?:a total of\s+)?(?:up to\s+)?[\d,]{3,}[^.]{0,180}",
    r"[^.]{0,80}welcome(?: bonus| offer)?[^.]{0,160}",
    r"[^.]{0,60}when you spend[^.]{0,160}",
    r"[^.]{0,60}first purchase[^.]{0,160}",
    r"[^.]{0,40}monthly statement periods?[^.]{0,120}",
    r"[^.]{0,50}(?:foreign|outside canada)[^.]{0,150}",
    r"[^.]{0,30}\b2\.5% service charge[^.]{0,100}",
    r"[^.]{0,50}purchase interest rate[^.]{0,120}",
    r"[^.]{0,20}annual fee[^.]{0,140}",
]


def page_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for t in soup.find_all(["nav", "footer"]):
        t.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    return re.sub(r"(\d)\s*,\s*(\d)", r"\1,\2", text)


def snippets(text: str, wanted: set[str]) -> list[str]:
    pats = SNIPPET_PATTERNS
    if wanted == {"fx_fee_pct"}:
        pats = [p for p in SNIPPET_PATTERNS if "foreign" in p or "service charge" in p]
    out: list[str] = []
    seen_spans: list[tuple[int, int]] = []
    for pat in pats:
        for m in re.finditer(pat, text):
            if any(s <= m.start() < e for s, e in seen_spans):
                continue
            seen_spans.append((m.start(), m.end()))
            out.append(text[max(0, m.start()) : m.end()].strip())
            if len(out) >= 14:
                return out
    return out


def main() -> int:
    index = json.loads((PIPELINE_DIR / "cache" / "index.json").read_text(encoding="utf-8"))
    lines = ["# LLM Fill Digest", ""]
    n = 0
    for f in sorted((PIPELINE_DIR / "data" / "cards").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        c, v = d["card"], d["card_version"]
        gaps: set[str] = set()
        rates = d["earn_rates"]
        if not rates:
            gaps.add("earn_rates")
        elif not any(r.get("category_slug") is None for r in rates):
            gaps.add("base_rate")
        if not d["offers"]:
            gaps.add("offers")
        else:
            o = d["offers"][0]
            if o.get("min_spend_minor") is None:
                gaps.add("min_spend")
            if o.get("deadline_days") is None:
                gaps.add("deadline")
        if v.get("fx_fee_pct") is None:
            gaps.add("fx_fee_pct")
        if v.get("purchase_apr") is None:
            gaps.add("purchase_apr")
        if c["program_slug"] == "unknown":
            gaps.add("program_slug")
        # skip cards whose only gap is FX (handled issuer-wide)
        if not gaps - {"fx_fee_pct"}:
            continue

        url = c.get("page_url")
        entry = index.get(url or "")
        if not entry or not Path(entry["body"]).exists():
            lines += [f"## {c['slug']}", "", f"NO CACHE for {url}", ""]
            continue
        text = page_text(Path(entry["body"]).read_text(encoding="utf-8"))
        snips = snippets(text, gaps)
        lines += [
            f"## {c['slug']}  [{','.join(sorted(gaps))}]",
            f"program={c['program_slug']} name={c['name']!r}",
            "",
        ]
        for s in snips:
            lines.append(f"- {s}")
        lines.append("")
        n += 1
    out = PIPELINE_DIR / "data" / "llm_digest.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} ({n} cards)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
