# Graph Report - Churney  (2026-08-28)

## Corpus Check
- 147 files · ~379,986 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 394 nodes · 690 edges · 47 communities (25 shown, 22 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 63 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Amex Scraper & Models
- Card Emit Pipeline
- HTTP Fetch Layer
- Product Features & Vision
- Churn Rules & Eligibility
- Scraper Config & Tests
- CLI & Summarize Scripts
- Generic Scraper Parsing
- Amex CA Tests
- Generic Scraper Tests
- Issuer Listing Fixtures
- Data Sourcing Pipeline
- Card Explorer UI
- Research Fill Scripts
- Amex CA Fixtures
- Architecture & Data Model
- CIBC Live Fixtures
- Vision & Churning Research
- Product Specs Bridge
- Issuer Rules Research
- LLM Digest Scripts
- Brim Live Fixtures
- Neo Live Fixtures
- Vision & Spend Specs
- Architecture & FX Specs
- Supabase & Inngest
- Programs & Transfers
- Tactics Playbook
- CIBC Rates PDF
- Verification Checklist
- UI Smoke Scripts
- Reparse Cache Scripts
- LLM Digest Data
- RBC Live Fixtures
- TD Live Fixtures
- P3 Household Optimizer
- Show the Math Principle
- Drizzle ORM
- Competitive Analysis
- Spend Tracking Spec
- Churn Engine Spec
- Scotia Live Fixtures
- Simplii Live Fixtures
- Churney Main Entry

## God Nodes (most connected - your core abstractions)
1. `GenericIssuerScraper` - 31 edges
2. `Fetcher` - 26 edges
3. `AmexCaScraper` - 20 edges
4. `ReviewItem` - 19 edges
5. `IssuerScraper` - 17 edges
6. `CardFile` - 16 edges
7. `load_card_file()` - 15 edges
8. `SourceConfig` - 14 edges
9. `Offer` - 14 edges
10. `make_scraper()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `Beam Search Optimizer v1` --semantically_similar_to--> `Eligibility Engine`  [INFERRED] [semantically similar]
  docs/specs/05-rotation-planner.md → docs/specs/06-churn-engine.md
- `CIBC Standard Purchase Interest Rate 21.99%` --conceptually_related_to--> `American Express Aeroplan Reserve Card`  [INFERRED]
  pipeline/data/cibc_rates.pdf → pipeline/tests/fixtures/amex_ca/aeroplan-reserve.html
- `IssuerScraper` --uses--> `SourceConfig`  [INFERRED]
  pipeline/scrapers/base.py → pipeline/churney/config.py
- `TestFetcher` --uses--> `RobotsDisallowed`  [INFERRED]
  pipeline/tests/test_fetch.py → pipeline/churney/fetch.py
- `IssuerScraper` --uses--> `Fetcher`  [INFERRED]
  pipeline/scrapers/base.py → pipeline/churney/fetch.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Churney Feature Pipeline** — docs_01_product_overview_f1_spend_tracking, docs_01_product_overview_f2_reward_engine, docs_01_product_overview_personal_spend_profile, docs_01_product_overview_f3_card_comparison, docs_01_product_overview_f4_program_comparison, docs_01_product_overview_f5_rotation_planner, docs_01_product_overview_f6_churn_engine [EXTRACTED 1.00]
- **Aeroplan Issuer + Program Rule Overlay** — docs_research_03_programs_and_transfers_aeroplan, docs_research_03_programs_and_transfers_aeroplan_tier_lockout, docs_research_02_issuer_rules_canada_program_lockout, docs_specs_06_churn_engine_eligibility_engine [EXTRACTED 1.00]
- **v1 Scraper Pipeline Architecture** — docs_04_data_sourcing_scraper_pipeline_v1, docs_04_data_sourcing_issuer_scraper_abc, docs_04_data_sourcing_versioned_json_output, pipeline_sources_yaml_source_registry, pipeline_readme_scraper_pipeline, pipeline_readme_fill_chain [EXTRACTED 1.00]
- **Aeroplan Co-Brand Credit Cards** — pipeline_tests_fixtures_amex_ca_aeroplan_reserve_aeroplan_reserve_card, pipeline_tests_fixtures_td_live_detail_td_aeroplan_visa_infinite, pipeline_tests_fixtures_amex_ca_aeroplan_reserve_aeroplan_program [INFERRED 0.85]
- **Stale 404 Live Capture Fixtures** — pipeline_tests_fixtures_nbc_live_listing_nbc_404_page, pipeline_tests_fixtures_rbc_live_listing_rbc_404_page, pipeline_tests_fixtures_rbcroyalbank_live_detail_rbc_404_page, pipeline_tests_fixtures_scotiabank_live_detail_scotiabank_404_page, pipeline_tests_fixtures_tangerine_live_listing_tangerine_404_page [INFERRED 0.85]
- **Issuer Credit Card Listing Page Fixtures** — pipeline_tests_fixtures_amex_ca_listing_amex_canada_credit_cards_listing, pipeline_tests_fixtures_brim_live_listing_brim_credit_cards_listing, pipeline_tests_fixtures_cibc_live_listing_cibc_all_credit_cards_listing, pipeline_tests_fixtures_neo_live_listing_neo_credit_cards_listing, pipeline_tests_fixtures_rbcroyalbank_live_listing_rbc_credit_cards_homepage, pipeline_tests_fixtures_scotiabank_live_listing_scotiabank_credit_cards_listing, pipeline_tests_fixtures_td_live_listing_td_credit_cards_listing [INFERRED 0.75]

## Communities (47 total, 22 thin omitted)

### Community 0 - "Amex Scraper & Models"
Cohesion: 0.08
Nodes (44): BaseModel, field_validator, AlternateOffer, Card, CardVersion, EarnRate, Network, Offer (+36 more)

### Community 1 - "Card Emit Pipeline"
Cohesion: 0.11
Nodes (28): ABC, Generate the static UI data bundle from emitted card JSON files. Writes…, card_file_path(), emit(), load_card_file(), Path, Atomic JSON emission to data/cards/<slug>.json (docs/04 §9.2)., Validate (pydantic re-check happens at model construction) and write. Atomic… (+20 more)

### Community 2 - "HTTP Fetch Layer"
Cohesion: 0.10
Nodes (15): BaseTransport, Fetcher, FetchError, PageResult, Path, RuntimeError, Polite fetching: robots.txt gate, honest UA, per-domain rate limit, HTML cache…, Returns a parser, an empty-allow sentinel (None), or raises-free fallback. RFC… (+7 more)

### Community 3 - "Product Features & Vision"
Cohesion: 0.11
Nodes (23): Capture is king, P1 The Optimizer, P2 The Points-Curious, Ratehub, Daily Wallet, F1 Spend Tracking, F2 Reward Engine, F3 Card Comparison (+15 more)

### Community 4 - "Churn Rules & Eligibility"
Cohesion: 0.09
Nodes (23): Churney, TravelMaxx, churn_rules table, keeper card role, user_cards table, Phase 2 Intelligence Layer, Churney Documentation Index, Amex CA once-per-lifetime per product (+15 more)

### Community 5 - "Scraper Config & Tests"
Cohesion: 0.15
Nodes (13): load_sources(), Path, RuntimeError, sources.yaml loading + pre-crawl compliance gates (docs/04 §2, §9.5)., SourceConfig, SourceNotCrawlable, Path, fixture_transport() (+5 more)

### Community 6 - "CLI & Summarize Scripts"
Cohesion: 0.13
Nodes (16): ArgumentParser, build(), Path, build_parser(), main(), make_fetcher(), Path, CLI entry point: python -m churney scrape <issuer> | scrape all [--force]… (+8 more)

### Community 7 - "Generic Scraper Parsing"
Cohesion: 0.15
Nodes (10): BeautifulSoup, GenericIssuerScraper, Works off the shared copy-pattern toolkit. Subclasses tune via class attrs., source_has(), Scraper registry: source name -> IssuerScraper implementation. Thin per-issuer…, ScotiabankScraper, SimpliiScraper, TangerineScraper (+2 more)

### Community 8 - "Amex CA Tests"
Cohesion: 0.14
Nodes (13): CibcScraper, make_scraper(), make_source(), parse_aventura(), Golden tests for the config-driven generic scraper against CIBC fixtures. CIBC…, DOM-split '35 ,000' must become '35,000' before regex extraction., CIBC copy: '1.5 points for every $1 spent at eligible gas stations, electric…, Get a total of up to 35,000 Aventura Points' + '$3,000 ... in the first 4… (+5 more)

### Community 9 - "Generic Scraper Tests"
Cohesion: 0.13
Nodes (8): make_scraper(), make_source(), Path, Golden test for the real americanexpress.com page structure (tiles + two-part…, TestFullRun, TestNeverGuesses, TestParseAeroplanReserveLive, TestParseGoldRewardsCard

### Community 10 - "Issuer Listing Fixtures"
Cohesion: 0.12
Nodes (18): CIBC Credit Card Summary of Annual Interest Rates and Fees, CIBC Standard Purchase Interest Rate 21.99%, Aeroplan, American Express Aeroplan Reserve Card, Simplified Static HTML Fixture Pattern, Aventura Points, CIBC Aventura Visa Infinite Card, CIBC Dividend Visa Infinite Card (+10 more)

### Community 11 - "Data Sourcing Pipeline"
Cohesion: 0.22
Nodes (9): Effective-dating, cards table, IssuerScraper ABC, Scraper Pipeline v1, Versioned JSON output (data/cards/<slug>.json), Churney Card-Data Scraping Pipeline, amex_ca scraper source, BMO backed-off source (+1 more)

### Community 12 - "Card Explorer UI"
Cohesion: 0.47
Nodes (8): earnRateLabel(), fillSelect(), filtered(), init(), kv(), renderDetail(), renderList(), unique()

### Community 13 - "Research Fill Scripts"
Cohesion: 0.60
Nodes (4): main(), page_text(), Build an LLM-review digest of evidence snippets for missing card fields. For…, snippets()

### Community 14 - "Amex CA Fixtures"
Cohesion: 0.40
Nodes (5): American Express Gold Rewards Card, Membership Rewards, American Express Canada Credit Cards Listing, Disallow /private/ Crawl Rule, American Express SimplyCash Preferred Card

### Community 15 - "Architecture & Data Model"
Cohesion: 0.50
Nodes (4): Scrapers propose, humans dispose, conversion_bonuses table, T0 Admin-curated core DB, Program Data Freshness Pipeline

### Community 16 - "CIBC Live Fixtures"
Cohesion: 0.50
Nodes (4): National Bank 404 Page Not Found, Stale Live Capture 404 Fixture Pattern, RBC 404 Page Not Found, Tangerine 404 Error Page

### Community 17 - "Vision & Churning Research"
Cohesion: 0.67
Nodes (3): Never lose a bonus, Minimum Spend Requirement (MSR), Min-Spend Feasibility Scorer

### Community 18 - "Product Specs Bridge"
Cohesion: 0.67
Nodes (3): cpp (cents-per-point), EAV (Effective Annual Value), net_annual_value algorithm

### Community 19 - "Issuer Rules Research"
Cohesion: 0.67
Nodes (3): MBNA 5/6 rule, RBC 1/90 rule, Velocity & Bureau Management

### Community 21 - "Brim Live Fixtures"
Cohesion: 0.67
Nodes (3): Brim Financial Credit Cards Listing, Brim Open Rewards, Brim World Elite Mastercard

### Community 22 - "Neo Live Fixtures"
Cohesion: 0.67
Nodes (3): Scotia Momentum Visa Infinite Card, Scotiabank Credit Cards Listing, Scotiabank Passport Visa Infinite Card

## Ambiguous Edges - Review These
- `program_lockout rule type` → `Scotiabank 24-month exclusion`  [AMBIGUOUS]
  docs/research/02-issuer-rules-canada.md · relation: conceptually_related_to

## Knowledge Gaps
- **66 isolated node(s):** `churney-pipeline`, `P3 The Household Optimizer`, `Ratehub`, `AwardWallet`, `TravelMaxx` (+61 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `program_lockout rule type` and `Scotiabank 24-month exclusion`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Fetcher` connect `HTTP Fetch Layer` to `Amex Scraper & Models`, `Card Emit Pipeline`, `Scraper Config & Tests`, `CLI & Summarize Scripts`, `Generic Scraper Tests`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `GenericIssuerScraper` connect `Generic Scraper Parsing` to `Amex Scraper & Models`, `Card Emit Pipeline`, `Amex CA Tests`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `IssuerScraper` connect `Card Emit Pipeline` to `Amex Scraper & Models`, `HTTP Fetch Layer`, `Scraper Config & Tests`, `Generic Scraper Parsing`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `GenericIssuerScraper` (e.g. with `AlternateOffer` and `Card`) actually correct?**
  _`GenericIssuerScraper` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `AmexCaScraper` (e.g. with `AlternateOffer` and `Card`) actually correct?**
  _`AmexCaScraper` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ReviewItem` (e.g. with `AmexCaScraper` and `GenericIssuerScraper`) actually correct?**
  _`ReviewItem` has 3 INFERRED edges - model-reasoned connections that need verification._