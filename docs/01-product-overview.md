# 01 — Product Overview

## Feature Map

```
┌─────────────────────────────────────────────────────────────────┐
│                          CHURNEY                                │
│                                                                 │
│  [F1 Spend Tracking] ──► [F2 Reward Engine] ──► [F3 Compare]    │
│   iOS Wallet capture        category + earn          cards      │
│   manual / CSV              calculation                        │
│         │                        │                             │
│         ▼                        ▼                             │
│  [Spend History] ◄──────  [Personal Spend Profile]              │
│                                  │                             │
│            ┌─────────────────────┼──────────────────┐          │
│            ▼                     ▼                  ▼          │
│   [F5 Rotation Planner]   [F6 Churn Engine]   [F4 Programs]     │
│    daily wallet + rotation  next-card advice     live data     │
└─────────────────────────────────────────────────────────────────┘
```

- **F1** feeds everything. F2 turns raw spend into reward truth. The resulting *personal spend profile* powers personalized comparison (F3), rotation + daily-wallet optimization (F5), and churn feasibility (F6). F4 is a shared live dataset used by F2 (valuations) and F5/F6 (bonus values). F5 plans two coordinated tracks: a **daily wallet** of keeper cards (cashback or points, never churned — serves P2 entirely) and a **rotation** of churn targets (P1's bonus engine).
- Full specs live in [`docs/specs/`](./specs/).

## Platform Strategy

| Surface | Role | Phase |
|---|---|---|
| **Web app** (Next.js PWA, installable on iOS home screen) | Primary product: dashboards, comparisons, rotation planner, churn tools | Phase 1 |
| **iOS Shortcut automation** (user-configured, guided in-app) | Spend capture: Wallet Transaction trigger → POST to ingest API. Works without any native app | Phase 1 |
| **Native iOS app** (SwiftUI) | One-tap Shortcut setup via App Intents, draft-review notifications, widgets | Phase 3 |
| **Android** | Not planned v1 | TBD |

**Why capture works without a native app:** the Shortcuts Transaction trigger exposes card/merchant/amount and can run an HTTP action (`Get Contents of URL` → POST). Users install our shortcut template (deep-linked with their device token pre-filled). Native app later replaces the manual install with one tap.

## Core User Journeys

### J1 — Onboarding (first session, target < 10 min)
1. Sign up (email + Google OAuth)
2. Add wallet: search & add current cards → set `opened_date`, credit limit optional
3. Set default currency (CAD), timezone
4. **Shortcut setup wizard:** step-by-step screenshots; deep link opens Shortcuts with pre-configured template; user selects their cards in the trigger config; test transaction
5. Seed historical spend (optional): CSV import from bank/card statement
6. First insight shown immediately: "Based on your last 30 days, card X would have earned you $Y more"

### J2 — Daily loop (passive)
- User pays with Apple Pay → Transaction trigger fires → payload POSTs to `/api/v1/ingest/transactions`
- Server resolves merchant → category → computes earned rewards per the tapped card **and** best-in-wallet
- Draft appears in review queue if confidence < threshold or duplicate suspected; else auto-confirmed

### J3 — Weekly review (engagement hook)
- Digest: total spend, rewards earned vs optimal ("missed $4.20 this week"), min-spend progress bars, program bonus alerts (e.g., "Amex→Aeroplan 25% transfer bonus ends Friday")

### J4 — Churn cycle (P1 core journey)
1. Rotation planner shows current rotation timeline + "safe to apply" dates per issuer rules
2. Churn engine ranks next-best applications with rationale + min-spend feasibility score
3. User marks application submitted → tracker starts min-spend countdown with projected completion date from real spend velocity
4. Bonus posted → user confirms → history updated → engine unlocks next recommendations

### J5 — Daily-wallet setup (P2 core journey; P1 sets keepers once and forgets)
1. Planner reads real spend mix → proposes a daily wallet: per-category card assignment over keeper cards (cashback cards fully supported, valued at face value)
2. User pins/unpins keeper cards; planner never schedules exits for pinned cards
3. Dashboard answers "which card do I tap today?" from the stable daily wallet; weekly digest shows "missed $" vs that assignment
4. When terms change or a better card appears, planner recommends a keeper swap with full math — not churn pressure

## Information Architecture (Web App)

```
/                   Dashboard (spend, rewards, alerts, deadlines)
/wallet             My cards (add/edit/close, fee calendar)
/spend              Transactions (list, drafts queue, categories, corrections)
/spend/import       CSV import wizard
/cards              Card explorer (public DB, filters)
/cards/[slug]       Card detail (rates, offer, insurance, history of terms)
/compare            Card comparison ([?a=...&b=...&c=...])
/programs           Program comparison matrix
/programs/[slug]    Program detail (redemptions, transfers, bonus history)
/rotation           Rotation planner (daily wallet + timeline + settings)
/churn              Churn hub (recommendations, eligibility, application log)
/settings           Profile, currency/timezone, devices/tokens, notifications
/admin              Curated DB management (role-gated)
```

## Cross-Cutting UX Rules

1. Every monetary figure has a tooltip showing its derivation.
2. Draft transactions never silently affect stats; confirmed-only by default with toggle.
3. All public card/program pages show "Last verified" timestamp.
4. Dark-mode first aesthetic; three.js reserved for dashboard hero + rotation visualization (see spec 05).
5. Empty states always teach: e.g., empty compare page suggests top cards for the user's dominant category.

## Roles

| Role | Capabilities |
|---|---|
| `user` | Personal features |
| `admin` | + curated DB CRUD, ingestion review queue, publish rights |
| `editor` | + propose changes to curated DB, no publish |

## Glossary

| Term | Meaning |
|---|---|
| **Wallet** | A user's set of tracked cards (`user_cards`) |
| **Rotation** | Planned ordered sequence of card applications/switches over time |
| **Churning** | Repeatedly acquiring cards primarily for welcome bonuses |
| **Min spend** | Spend threshold required to earn a welcome bonus within a deadline |
| **EAV** | Effective annual value: rewards value − fees (+ insurance/perk estimates) |
| **cpp** | Cents-per-point valuation of a loyalty currency in a given redemption context |
| **Draft** | Ingested capture pending confirmation |
| **Effective-dating** | Versioned rows with `valid_from`/`valid_to` for terms that change over time |
