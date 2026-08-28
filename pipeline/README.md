# Churney Card-Data Scraping Pipeline

Implements `docs/04-data-sourcing.md` §9 — hand-written per-site scrapers emitting
versioned JSON (`data/cards/<slug>.json`) mirroring the schemas in
`docs/03-data-model.md`.

## Setup

```powershell
uv sync              # creates .venv from pyproject.toml (Python >= 3.12)
uv run pytest        # offline test suite (fixture-driven, no network)
```

## Running a scrape

```powershell
uv run python -m churney scrape amex_ca            # one source
uv run python -m churney scrape all --force        # re-parse unchanged pages
uv run python -m churney scrape amex_ca --limit 5  # first N card URLs only
uv run python -m churney build-ui                  # regenerate ui/cards.js after scraping
```

## Card explorer UI

Open `ui/index.html` in any browser (double-click — data is embedded, no server needed).
Rebuild the bundle with `build-ui` after each scrape. Features: search, issuer/program/
type filters, fee sorting, full breakdowns (costs, earn structure, welcome offer incl.
alternate offers, review items, source links).

## Issuer status (2026-08-23)

| Issuer | Status | Mode | Cards |
|---|---|---|---|
| Amex CA | ✅ active | playwright (SPA) | 14 |
| TD | ✅ active | httpx | 4 |
| CIBC | ✅ active | httpx | 27 |
| Scotiabank | ✅ active | httpx | 12 |
| Tangerine | ✅ active | httpx | 3 |
| Simplii | ✅ active | httpx | 1 |
| RBC Royal Bank | ✅ active | httpx | 15 |
| NBC | ⏸ pending | — | card-page taxonomy unconfirmed |
| Neo Financial | ⏸ pending | — | client-rendered; needs Playwright |
| Brim | ⏸ pending | — | JS-heavy; needs Playwright + URL list |
| BMO | 🚫 backed off | — | TCP-level block from this network (docs/04 §2); needs different egress/manual saves |
| Desjardins | ⏸ pending | — | URLs unmapped; lower priority (English-only v1) |

See `sources.yaml` notes for details.

## Compliance gates (docs/04 §2, §9.5)

A source in `sources.yaml` will refuse to crawl unless:

1. `allowed: true`
2. `tos_reviewed_at` set by a human who reviewed the site's ToS and robots.txt

The fetcher additionally enforces: robots.txt rules, honest `ChurneyBot/1.0` UA,
≤ 1 request / 5s per domain, content-hash caching with drift detection.

## Output

`data/cards/<slug>.json` — validated envelope:

```jsonc
{
  "schema_version": "1",
  "card": { ... },
  "card_version": { "annual_fee_minor": 25000, "...": "money = integer minor units" },
  "earn_rates": [ ... ],
  "offers": [ { "headline": "...", "alternate_offers": [ ... ] } ],
  "needs_manual_review": [ { "field": "...", "reason": "..." } ],  // never guessed values
  "content_hash": "sha256 of the parsed page"
}
```

Git history of this directory doubles as the change log until the Supabase
`change_log` table exists.

## Adding an issuer

1. Add an entry to `sources.yaml` (with ToS review recorded).
2. Create `scrapers/<issuer>.py` implementing `IssuerScraper`
   (`discover_card_urls()` + `parse_card()`).
3. Register it in `scrapers/__init__.py`.
4. Save page snapshots under `tests/fixtures/<issuer>/` and write golden tests.

## Refresh workflow (do not deviate)

Re-scrapes regenerate `data/cards/*.json` from issuer pages, which **overwrites
human/LLM-verified corrections**. Always finish with the fill chain:

```powershell
uv run python -m churney scrape all          # or per-source
uv run python scripts/reparse_cache.py       # offline reparse through current parsers
uv run python scripts/apply_fill.py data/fill_2026-08-24.json
uv run python scripts/apply_fill.py data/fill_frugalflyer_2026-08-24.json
uv run python scripts/apply_fill.py data/fill_research_2026-08-24.json
uv run python scripts/apply_fill.py data/fill_cibc_verify_2026-08-28.json
uv run python scripts/apply_fill.py data/fill_issuer_verify_2026-08-28.json
uv run python scripts/apply_fill.py data/fill_scotiabank_momentum_2026-08-28.json
uv run python scripts/apply_fill.py data/fill_amex_gaps_2026-08-28.json
uv run python scripts/review_hygiene.py      # drop review items contradicted by data
uv run python -m churney build-ui && uv run python -m churney verify-report
uv run pytest
```

All fill files are idempotent. Sources ladder: issuer pages/disclosures >
official rate PDFs > aggregator cross-checks (frugalflyer.ca, milesopedia.com)
> flagged [VERIFY] external knowledge.
