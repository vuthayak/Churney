# 02 — Technical Architecture

> Status: draft · Owner: Engineering

## 1. System Overview

```
                        ┌────────────────────────────┐
  iOS Shortcut ──POST──►│                            │
  (Wallet trigger)      │        Next.js App         │
                        │   (Vercel, edge+node)      │
  Web/PWA users ───────►│  /api/v1/* route handlers  │
                        └──────────┬─────────────────┘
                                   │
                    ┌──────────────┼───────────────────┐
                    ▼              ▼                   ▼
             ┌───────────┐  ┌───────────┐    ┌────────────────┐
             │ Supabase  │  │ Inngest   │    │ LLM ingest svc │
             │ Postgres  │  │ workers   │    │ (batch)        │
             │ Auth/RLS  │  │ - fx sync │    └────────────────┘
             │ Realtime  │  │ - scrapers│
             └───────────┘  │ - audits  │
                            └─────┬─────┘
                                  │ reads/writes
                                  ▼
                          external sources
                          (BoC Valet, broker sites,
                           issuer pages)
```

## 2. Stack Decisions

| Layer | Choice | Rationale |
|---|---|---|
| Framework | **Next.js 15 (App Router) + TypeScript strict** | One deployable for UI + API; PWA support; Vercel hosting |
| Styling | Tailwind CSS + shadcn/ui | Speed, dark-mode-first |
| 3D | **react-three-fiber + drei** (three.js) | Dashboard hero + rotation timeline viz (Spec 05); lazy-loaded, 2D fallback |
| DB | **Supabase Postgres** | Managed Postgres, Auth with OAuth, RLS multi-tenancy, Realtime for draft queues |
| ORM | Drizzle ORM | SQL-transparent; effective-dating and window functions stay first-class |
| Validation | Zod | Shared schemas client/server/ingest payload |
| Jobs/cron | **Inngest** | Scheduled functions (FX daily, scrapers, weekly audits), retries, no infra to run |
| LLM ingestion | Anthropic API batch w/ structured outputs (JSON schema) | Offer/T&C extraction (docs/04 §4) |
| FX | Bank of Canada Valet API primary; exchangerate.host backup | Free official CAD rates (Spec 01 §6) |
| Hosting | Vercel (app), Supabase (data), Inngest Cloud (jobs) | All serverless; minimal ops |
| Observability | Sentry (errors), PostHog (product analytics), Better Stack or Axiom (logs) | — |
| Email | Resend | Digests/deadline alerts |

## 3. API Surface (`/api/v1`)

| Route | Method | Auth | Purpose |
|---|---|---|---|
| `/ingest/transactions` | POST | Device token (Bearer) | Shortcut capture (Spec 01 §2.1). Ack <150ms; enrichment async |
| `/transactions` | GET/POST/PATCH | Session | List/manual add/edit status |
| `/transactions/:id/recompute` | POST | Session | Force reward recompute |
| `/wallet` CRUD | * | Session | User cards |
| `/cards`, `/programs` | GET | Public (+session personalization) | Curated DB reads |
| `/compare?cards=` | GET | Public | Computed comparison payloads |
| `/rotation` | GET/PUT | Session | Plan read/solve |
| `/churn/recommendations` | GET | Session | Ranked suggestions |
| `/admin/*` | * | Role admin/editor | Curated DB, review queue, publish |

Conventions: Zod-validated bodies; cursor pagination; RFC7807-ish error envelope `{error:{code,message,details}}`.

## 4. Ingest Path Detail (hot path)

1. Edge middleware: rate limit (Upstash Redis sliding window, e.g., 120/min/device), reject early.
2. Node handler: verify device token hash → idempotency lookup → insert raw row (`ingest_logs`) → enqueue `txn.enrich` event → 201 ack.
3. `txn.enrich` (Inngest): dedupe pass → card resolve → currency/FX resolve → merchant pipeline (Spec 02 §3) → status set → Realtime push to user's draft queue.

## 5. Scheduled Jobs (Inngest cron, ET)

| Schedule | Job |
|---|---|
| Daily 02:00 | FX sync (BoC Valet all pairs in use; backup failover) |
| Daily 06:00 | Source scrapers → page-hash snapshots → drift detection |
| Daily 07:00 | LLM diff extraction on drifted pages → review queue items |
| Weekly Mon 05:00 | Full program-data audit sweep; freshness report to admin |
| Hourly | Bonus end-date transitions; deadline warning notifications (T-14/7/3d) |
| Nightly | Draft auto-expire sweeps; coverage estimator recompute; digest emails queued |

## 6. Data Flow Boundaries & Privacy

- No PANs ever exist in our systems (Apple exposes none; we store user-assigned card hints).
- Transaction data is per-user, RLS-enforced; global merchant alias promotion only via k≥50 aggregation + admin review.
- Scraped content stored as structured facts + source URLs/hashes, not republished verbatim (docs/04 §2).

## 7. Environments & CI/CD

- `local` (supabase cli + inngest dev server) / `preview` (Vercel PR envs, branch DB schema shadow) / `prod`.
- GitHub Actions: typecheck, lint, unit (vitest), integration (pgTAP + testcontainers), property tests for engines (fast-check), e2e smoke (Playwright).
- Migrations: Drizzle Kit forward-only; destructive changes require two-phase (expand → migrate → contract).
- Feature flags: simple `flags` table + cached provider.

## 8. Scaling Notes

- Phase 1 scale (<10k users): single Postgres fine; hot path already async.
- Reward engine recomputes are batch/idempotent by `engine_version` — safe to parallelize.
- Read-heavy public card pages → ISR/static generation with tag-based revalidation on admin publish.
- If shortcut adoption spikes ingest: move ack path to edge function + queue write only.

## 9. Security Checklist (pre-launch gates)

- [ ] RLS policies tested adversarially (cross-user access suite)
- [ ] Device tokens: hashed at rest, rotation endpoint, revocation UI
- [ ] Rate limits per token/IP; anomaly alerts on ingest volume
- [ ] Admin actions audit-trailed (`audit_log`)
- [ ] Dependency + container scanning in CI; secrets via platform env only
