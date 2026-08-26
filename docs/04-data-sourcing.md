# 04 — Data Sourcing Strategy

> Status: draft · Owner: Ops + Engineering
> Governs: card/offer DB, program intelligence (Spec 04), FX, merchant graph

## 1. Strategy Tiers

| Tier | Source | Latency | Trust | Role |
|---|---|---|---|---|
| T0 | **Admin-curated core DB** | Immediate | Highest | Source of truth for anything user-facing |
| T1 | **Scheduled scrapers** (select broker/aggregator pages) | Daily | High (signals) | Drift detection → review queue |
| T2 | **LLM-assisted ingestion** of issuer pages/T&Cs | On-demand / weekly | Medium until verified | New cards, term changes, promo discovery |
| T3 | Community submissions + user corrections | Continuous | Low until review | Alias harvesting, error reports (Phase 2+) |

Principle: **scrapers propose, humans dispose.** No scraped fact reaches users without passing through the review/publish workflow.

## 2. Scraping Rules of Engagement

- Review each target's ToS before adding; skip sites prohibiting automated access. Maintain `sources` registry: `{url, tos_reviewed_at, allowed, cadence}`.
- Respect robots.txt; identify honestly (`ChurneyBot/1.0 (+about contact)`); rate-limit ≤ 1 req/5s/domain, off-peak.
- Store structured facts + source URL + content hash — never republish page text verbatim; summaries link to source.
- Cache aggressively; full re-crawl weekly max; drift-triggered re-extract only on hash change.
- Back off permanently on 403/blocks; fall back to manual checks for that source.

## 3. Target Sources (seed)

| Source | What we take | Cadence |
|---|---|---|
| Issuer sites (amex.ca, td.com, rbc.com, cibc.com, bmo.com, scotiabank.com) | Card terms, offers, T&C PDFs | Weekly + drift |
| Broker/aggregator listing pages (Ratehub, creditcardGenius, GreedyRates) `[ToS per site]` | Offer-change *signals*, comparison cross-checks | Daily drift watch |
| Program pages (Aeroplan, Amex MR partners, Avion, Scene+, Bonvoy) | Ratios, redemption tables, bonus promos | Weekly |
| Points blogs (Prince of Travel, Pointshogger etc.) | Rumor signals for conversion bonuses → status `rumored` | Daily |

Each curated row carries `source_url` + `verified_at`; UI shows "Last verified" everywhere.

## 4. LLM-Assisted Ingestion Pipeline

> **Status: DEFERRED to post-MVP.** For v1, card data is collected by the hand-written
> scraper pipeline described in **§9 — Scraper Implementation Design**. This section is
> retained as the target-state design for T2 ingestion of messy issuer pages/T&Cs once
> the curated base exists.

```
drifted page / new issuer URL
   → fetcher (cleaned HTML/text, PDF→text)
   → extractor: LLM w/ strict JSON schema:
     {entity_type, fields{...}, effective_dates, quotes[]}   # quotes = verbatim evidence snippets
   → validator: schema check + quote-presence check (each field must cite a quote)
   → differ vs current DB rows
   → review_queue item (editor/admin UI shows side-by-side old/new + evidence)
   → publish → change_log entry + cache revalidation
```

Rules:
- Structured outputs enforced at API level; any missing evidence quote ⇒ auto-reject to manual queue.
- Confidence scoring; low-confidence extraction flagged for senior review.
- Never auto-publish: ratio changes, bonus terms, fee changes. (Copy edits may auto-flow with editor approval.)

## 5. FX Rates

- **Primary:** Bank of Canada Valet API — free official noon/indicateive rates vs CAD (~100+ currencies). Daily sync into `fx_rates`.
- **Backup:** exchangerate.host (free tier) or OpenExchangeRates (paid) when BoC unavailable.
- Historical backfill 24 months at seed; on-demand fetch for older dates during CSV imports.
- Staleness: weekends/holidays walk back to last observation; store its date and display it (Spec 01 §6).
- Alert if primary fails twice consecutively; auto-failover with source stamped per rate row.

## 6. Merchant & Category Graph

- Seed top ~200 Canadian merchants across taxonomy v1 with brand families and network acceptance notes (e.g., Costco → Mastercard-only warehouses).
- Alias harvesting loop: unmatched ingest strings accumulate in `pending_merchants` with occurrence counts; ops reviews top-frequency weekly; user corrections create private aliases instantly, global promotion after admin review + k-anonymity check.
- LLM fallback assigns provisional category to unknown merchants (confidence ≤0.75, flagged) so reward estimates still work day one.
- Quarterly pruning: merge duplicate merchants, retire dead aliases.

## 7. Change Management

- Every curated table is effective-dated where terms matter (versions/ratios/valuations); corrections add new rows rather than mutating history.
- `change_log` powers public changelogs ("what changed this week") — a trust feature.
- Freshness SLOs: offers ≤7d; ratios/bonuses ≤14d; earn rates ≤90d; stale rows excluded from recommendation weighting (Specs 02/05/06 honor this).

## 8. Ops Runbook (admin surfaces)

- `/admin/review`: queue of drift diffs + LLM extractions with evidence side-by-side
- `/admin/sources`: health dashboard per scraper (last run, hash age, failure streaks)
- `/admin/freshness`: % of live rows within SLO, oldest rows list
- Weekly digest to admins: proposed changes pending count, stale hotspots

## 9. Scraper Implementation Design (v1)

> Status: approved design · Build target: pre-MVP data collection
> Scope: collect structured card data (rewards, costs, welcome bonuses, card type) for
> the full Canadian market into versioned JSON, later loaded into Supabase.

### 9.1 Decision Log

| Decision | Choice | Rationale |
|---|---|---|
| Runtime | **Python 3.12+** (`uv`-managed) | Strongest scraping ecosystem (httpx, lxml/BeautifulSoup, Playwright); pipeline shares no code with the Next.js app |
| Extraction | **Hand-written per-site selectors** | Deterministic and free; supersedes §4 LLM extraction for v1. Each issuer's site design gets a dedicated parser module |
| Output store | **Versioned JSON files** — `data/cards/<slug>.json` | Reviewable in git (history = change log until `change_log` table exists); validated against schemas mirroring `03-data-model.md`; loadable into Supabase when it exists |
| Market scope | **Full Canadian market** (~12 issuers) | Not just the 6 seed issuers of §3 |
| Fetching | httpx primary + **Playwright fallback** per site | Several Big 5 card pages are JS-rendered; per-site fetch mode flag in `sources.yaml` |
| Language | **English-only v1** | Desjardins/NBC English pages scraped; French support deferred to i18n phase; `source_url` records whichever page was parsed |

### 9.2 Architecture

```
pipeline/
├── pyproject.toml            # uv-managed deps
├── sources.yaml              # registry: {issuer, url, tos_reviewed_at, allowed,
│                             #   cadence, fetch_mode: httpx|playwright}
├── churney/
│   ├── fetch.py              # robots.txt check, ChurneyBot/1.0 UA, rate limit
│   │                         #   ≤1 req/5s/domain, HTML cache + content-hash drift
│   ├── models.py             # Pydantic schemas mirroring docs/03-data-model.md:
│   │                         #   Card, CardVersion, EarnRate, Offer
│   ├── emit.py               # validates + writes data/cards/<slug>.json
│   └── report.py             # run summary: new / changed / failed cards
└── scrapers/
    ├── base.py               # IssuerScraper ABC: discover_card_urls(), parse_card(html)
    └── <issuer>.py           # one module per issuer (see §9.3)
```

Conventions carried over from `03-data-model.md`:
- Money as integer **minor units**; every fact carries `source_url` + `verified_at`.
- Unparseable fields emit as `null` plus an entry in the file's
  `"needs_manual_review": [...]` list — never guessed values.
- Welcome bonuses use **two-layer capture**: canonical public offer in `offers`, and an
  optional `alternate_offers[]` array recording referral portals / GCR /
  higher limited-time variants (each with its own `source_url`). The public offer is
  often not the best available offer, which matters for churning users.

### 9.3 Issuer Inventory

Build order reflects churn relevance (Amex MR first) then site stability:

| Phase | Issuer | Entry point (approx.) | Notes |
|---|---|---|---|
| 2a | American Express CA | amex.ca card listing | ~20 cards; cleanest markup; proves the pattern |
| 2b | TD, RBC, CIBC, BMO, Scotiabank | each bank's credit-cards section | Likely Playwright (JS-rendered) |
| 3a | National Bank, Desjardins | nbc.ca / desjardins.com cards | English pages only (v1) |
| 3b | Tangerine, Simplii, Neo, Brim | direct-to-consumer sites | Cashback-first issuers |
| watchlist | PC Financial, Rogers, Canadian Tire Bank, Home Trust | — | Add opportunistically after core set is stable |

Aggregators (Ratehub, creditcardGenius, GreedyRates) stay out of the automated v1
pipeline per §2 ToS caution; they're used as manual cross-check references in Phase 4.

### 9.4 Phased Rollout

1. **Scaffold + framework** — Pydantic models, fetcher (cache/drift/rate-limit),
   `IssuerScraper` ABC, CLI: `python -m churney scrape <issuer>` / `scrape all`
2. **Amex CA** — end-to-end proof (~20 cards) through emit + report
3. **Big 5 banks** — TD, RBC, CIBC, BMO, Scotiabank
4. **Remaining market** — NBC, Desjardins, Tangerine, Simplii, Neo, Brim (+ watchlist)
5. **Cross-check pass** — spot-check scraped fees/WBs against aggregator listings
   manually; resolve all `needs_manual_review` items before Supabase load

### 9.5 Compliance

All targets inherit §2 rules without exception: ToS review recorded in `sources.yaml`
before first crawl, robots.txt respected, honest UA, ≤1 req/5s/domain off-peak,
content-hash caching, permanent backoff on blocks. No page text is republished — only
structured facts with source links.

