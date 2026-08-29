# 05 — Roadmap

> Status: draft · Phases sized for 1–2 builders · Dates relative to project start (T0)

## Phase 0 — Foundations & Spikes (Weeks 0–3)

**Goal:** de-risk the three hardest unknowns before building product.

| # | Task | Exit criteria |
|---|---|---|
| 0.1 | iOS Shortcut spike: personal test harness posting Wallet-trigger payloads to a stub endpoint | Real-device payload captured with card/merchant/amount; empty-merchant + FX-amount cases observed and documented |
| 0.2 | Reliability probe: 2-week logging of trigger behavior (timeouts FB16379100, delays) | Failure-rate estimate documented → informs digest-nudge design |
| 0.3 | Data model sign-off | `docs/03` reviewed, migrations run in Supabase |
| 0.4 | Curated seed v0 | 25 cards `[VERIFY]`, categories, programs, transfer matrix, top-50 merchants (grows to top-200 by Phase 1 exit per Spec 02 acceptance) |
| 0.5 | BoC Valet FX integration | Backfill 24mo; weekend/holiday handling tested |
| 0.6 | Repo bootstrap | Next.js + Drizzle + CI (typecheck/lint/test) green |
| 0.7 | Scraper pipeline v1 scaffold + Amex CA (docs/04 §9.4 steps 1–2) | Python/uv pipeline emitting `data/cards/<slug>.json`; **done 2026-08-29** — 12 issuers, 120 cards; `needs_manual_review` triaged (0 actionable `[VERIFY]`; informational `VERIFIED` notes remain). See `pipeline/README.md`. |

## Phase 1 — MVP "Capture & Earn" (Weeks 3–10)

**Goal:** a single user can sign up, capture real spend via shortcut, and see accurate reward truth.

Scope:
1. Auth (email/Google), profiles, settings
2. Ingest API + device tokens + idempotency/dedupe (Spec 01 §2.1, §5)
3. Draft review queue + manual quick-add + CSV import w/ per-issuer presets
4. FX service + multi-currency display
5. Reward engine v1: merchant pipeline, category taxonomy, earn-rate resolution incl. one cap case + exclusions; breakdown strings (Spec 02)
6. Wallet CRUD; dashboard v1 (spend, earned vs optimal, coverage widget)
7. Card explorer + head-to-head compare (anonymous mode) (Spec 03 §2)
8. Admin minimal: curated DB CRUD + review queue
9. Scraper rollout continues: Big 5 banks + remaining market (docs/04 §9.4 steps 3–5), feeding the curated DB

Exit criteria: Spec 01 §10 + Spec 02 §10 acceptance lists pass; 10 beta users capturing ≥3 weeks of real data; categorization precision ≥90% on beta corpus.

## Phase 2 — Intelligence Layer (Weeks 10–20)

**Goal:** from tracker to advisor.

1. Program comparison live pipeline: scrapers+drift detection, LLM extraction→review, conversion bonuses lifecycle, freshness SLOs (Spec 04)
2. Personalized net-value ranking + wallet insights (Spec 03 §3–4)
3. Rotation planner: timeline model, optimizer v1 (beam search) with **dual-track objective (churn + daily wallet)**, keeper-card support (`convert_to_keeper`, user-pinned keepers, keeper health checks), min-spend trackers with projections, fee calendar (Spec 05); three.js timeline viz + 2D fallback
4. Churn engine v1: rulebook seeded+verified, eligibility engine (incl. cashback offers + keeper/concurrent-limit interplay), feasibility scorer, ranked recommendations with rationale traces and `post_churn_role` (Spec 06)
5. Notifications: deadline escalations (T-14/7/3d), bonus-ending alerts, weekly digest email

Exit criteria: Spec 03/04/05/06 acceptance lists pass; rulebook 100% verified or advisory-flagged; compliance copy reviewed.

## Phase 3 — Native & Growth (Weeks 20–30)

1. Native SwiftUI companion app: App Intents-based one-tap shortcut install, draft-review push notifications, home-screen widgets ("tap X today")
2. Public program pages SEO surface + changelog feed
3. Community tier: submissions with review, shared valuation signals
4. Household wallets (P3 persona) — pooled cap tracking
5. Open banking readiness monitor (Bank of Canada framework milestones); Flinks integration evaluation when Phase-1 read access firms up
6. Android decision point (capture story = notification listener service)
7. MCP/CLI surfaces (post-iOS traction): expose rule engine + program DB to power users and third-party agents (research/06 takeaway #2)

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Shortcut trigger unreliable on some issuers' Apple Pay posting delays | Med | High (core capture) | 0.2 probe; digest nudges; manual path first-class; coverage estimator keeps honesty |
| Apple changes Shortcuts/Wallet APIs | Low-Med | High | Native app phase 3 uses same Transaction trigger surface; diversify with manual/CSV |
| Scraper ToS/blocks | Med | Medium | T0-curated core stays source of truth; multi-source redundancy; human verification loop |
| Rulebook errors give wrong churn advice | Med | High (trust/legal) | `[VERIFY]` gates, staleness exclusion, advisory-only fallback, disclaimers |
| LLM extraction hallucination | Med | Medium | Evidence-quote validation, no auto-publish, audit sampling |
| Solo-founder scope creep | High | High | Phase gates above are strict; anything not listed is out by default |
