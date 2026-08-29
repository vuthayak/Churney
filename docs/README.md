# Churney — Documentation Index

Canadian credit card spend tracking, reward optimization, and card churning platform.

## Document Map

| Doc | Purpose | Audience |
|---|---|---|
| [00-vision.md](./00-vision.md) | Problem, vision, personas, positioning, non-goals, success metrics | Everyone |
| [01-product-overview.md](./01-product-overview.md) | Feature map, user journeys, platform strategy | Everyone |
| [02-architecture.md](./02-architecture.md) | Stack, system design, APIs, jobs, security | Engineering |
| [03-data-model.md](./03-data-model.md) | ERD, full Postgres DDL, effective-dating patterns, RLS | Engineering |
| [04-data-sourcing.md](./04-data-sourcing.md) | Card data strategy, scraping rules, LLM ingest pipeline (deferred), FX sourcing, **§9 scraper implementation design (v1)** | Engineering + Ops |
| [05-roadmap.md](./05-roadmap.md) | Phased delivery plan, acceptance criteria, risk register | Everyone |

## Spikes (`docs/spikes/`)

| Spike | Purpose |
|---|---|
| [spikes/0.1-ios-shortcut.md](./spikes/0.1-ios-shortcut.md) | iOS Shortcut Transaction trigger → stub ingest harness (Phase 0.1) |

## Domain Research (`docs/research/`)

| Doc | Purpose | Audience |
|---|---|---|
| [research/01-churning-fundamentals.md](./research/01-churning-fundamentals.md) | Churning concept, bank economics, churn cycle, earning hierarchy, reward taxonomy | Everyone |
| [research/02-issuer-rules-canada.md](./research/02-issuer-rules-canada.md) | Per-issuer WB eligibility rules; seeds `churn_rules` | Engineering |
| [research/03-programs-and-transfers.md](./research/03-programs-and-transfers.md) | Aeroplan program T&Cs/clawbacks, transfer matrices, award availability | Engineering + Ops |
| [research/04-risks-and-compliance.md](./research/04-risks-and-compliance.md) | Credit-score mechanics, clawbacks/blacklisting, compliance guardrails | Everyone |
| [research/05-tactics-playbook.md](./research/05-tactics-playbook.md) | Community tactics tagged [ENGINE] vs [CONTENT] | Product + Content |
| [research/06-competitive-analysis.md](./research/06-competitive-analysis.md) | TravelMaxx & adjacent tools; Canada gap analysis | Everyone |

Research docs carry confidence tags (`[OFFICIAL]` / `[COMMUNITY]` / `[DATAPoint]` /
`[VERIFY]`) — see [research/README.md](./research/README.md).

## Feature Specs (`docs/specs/`)

| Spec | Feature |
|---|---|
| [01-spend-tracking.md](./specs/01-spend-tracking.md) | iOS Wallet capture via Shortcuts Transaction trigger, manual entry, CSV import, multi-currency FX |
| [02-reward-engine.md](./specs/02-reward-engine.md) | Merchant → category resolution, per-card earn-rate calculation, missed-optimization detection |
| [03-card-comparison.md](./specs/03-card-comparison.md) | Head-to-head and personalized net-value card comparison |
| [04-program-comparison.md](./specs/04-program-comparison.md) | Live rewards program comparison: redemptions, transfers, conversion bonuses |
| [05-rotation-planner.md](./specs/05-rotation-planner.md) | Card rotation planning + daily-wallet (keeper card) planning, min-spend progress, dual-track optimizer |
| [06-churn-engine.md](./specs/06-churn-engine.md) | Churning eligibility heuristics (points & cashback offers), min-spend feasibility, application timing suggestions |

## Reading Order for New Contributors

1. `00-vision.md` — what we're building and why
2. `01-product-overview.md` — how the features fit together
3. `02-architecture.md` + `03-data-model.md` — how it's built
4. Relevant spec(s) for your feature area
5. `05-roadmap.md` — what's next

## Conventions

- All monetary values are stored as integer **minor units** (cents) in the DB.
- All timestamps are UTC (`timestamptz`); display uses user's `America/Toronto` (configurable) timezone.
- Seed data referencing real-world rates/bonuses/rules is marked `[VERIFY]` and must be confirmed against issuer T&Cs before publishing to users.
