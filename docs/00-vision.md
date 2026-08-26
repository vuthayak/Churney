# 00 — Product Vision

## One-liner

**Churney** is the command center for Canadian credit card optimizers: automatic spend capture from Apple Wallet, real-time reward estimation across every card in your wallet, live rewards-program intelligence, a churning engine that tells you exactly which card to get next and when, and a daily-wallet planner that keeps your everyday cards (points or cashback) earning their best — no churning required.

## Problem Statement

Canadians who play the points game face three compounding problems:

1. **Blind spots on spend.** No Canadian tool automatically captures transactions at the moment of purchase. Bank syncs are unreliable/aggregator-gated, open banking isn't live, so people track bonuses in spreadsheets or not at all — and miss minimum-spend deadlines.
2. **Opaque reward math.** Every card earns differently by category, caps rewards, values its currency differently (Aeroplan point ≠ Avion point ≠ BONUSDOLLAR), and runs rotating transfer/conversion bonuses. Nobody can answer "what did that coffee actually earn me?" or "which card *should* I have tapped?" without manual math.
3. **Churning is tribal knowledge.** Issuer approval rules (once-per-lifetime bonuses, bonus-cycle windows), min-spend feasibility, and application timing live in subreddit threads and YouTube videos. There is no systematic tooling — all existing tools are US-centric.

Existing Canadian sites (Ratehub, creditcardGenius, GreedyRates) are **comparison marketing sites**, not personal trackers. US tools (AwardWallet, CardPointers) don't model Canadian programs deeply and have no spend capture.

## Vision

> Tap your phone. Churney knows what you spent, what you earned, what you should have earned, whether your welcome bonus is on track, and which card you should apply for next.

## Target Users / Personas

### P1 — "The Optimizer" (primary)
- Holds 4–8 cards, actively churns 2–6/year, targets Aeroplan/business-class redemptions — but keeps 1–3 keeper cards as daily drivers they never churn
- Currently: spreadsheet for bonus tracking, r/churning_ca for intel
- Pain: manual transaction logging; forgotten min-spend deadlines; uncertainty about eligibility windows; no systematic answer to "which cards should I actually keep?"
- Kill feature: rotation planner + churn engine + keeper/daily-wallet recommendations

### P2 — "The Points-Curious"
- Has 1–3 cards, mostly cashback or one airline program; **no interest in churning**
- Pain: doesn't know if they're leaving value on the table; overwhelmed by program jargon
- Kill feature: personalized net-value comparison + "you earned X, best wallet card would've earned Y" nudges + a stable daily-wallet recommendation ("grocery → this card, everything else → that card") that works entirely with cashback and no-fee cards

### P3 — "The Household Optimizer" (later phase)
- Manages spend across partner/family cards
- Pain: pooled category caps (e.g., grocery multiplier capped at $X/month across household)
- Kill feature: shared wallets, combined cap tracking *(explicitly out of v1)*

## Value Propositions

| Persona | Before | After |
|---|---|---|
| P1 | Spreadsheet + memory + Reddit; gut-feel on which cards to keep vs cancel | Automated capture, deadline alerts, eligibility engine, apply-timing recommendations, explicit keeper-vs-churn plan per card |
| P2 | Guesswork | Personalized card ranking from their actual spend mix + stable daily-wallet assignment (cashback-friendly, zero churn required) |
| All | Static comparison articles | Live program data with conversion-bonus tracking |

## Positioning

| Competitor | What they are | Gap we exploit |
|---|---|---|
| Ratehub / creditcardGenius / GreedyRates | Affiliate comparison sites | No personalization against your real spend; no tracking; stale program data |
| AwardWallet | Loyalty balance tracking (US-centric) | No spend capture, no churning logic, weak Canada coverage |
| CardPointers | Offer/amex-credit tracking (US-first) | Not Canadian; no spend capture; no churn planning |
| TravelMaxx | Agent-first points "maxxing" subscription (US-centric; award search, alerts, AI consultant, points marketplace) | No spend capture or transaction layer; no Canadian issuer rules/programs/WB tracking; leans into gray-area features (points marketplace) we deliberately avoid — see research/06 |
| r/churning_ca spreadsheets | Community templates | Manual, no automation, no data freshness |
| Budget apps (YNAB, Mint-successors) | Expense tracking | Zero reward/churn intelligence |

**Moat:** iOS-native capture UX + curated Canadian merchant/category graph + live program dataset (redemptions, transfers, bonuses) + churn rulebook. Each is defensible through operational effort.

## Non-Goals (v1)

- ❌ Android app (revisit after iOS traction)
- ❌ Open banking / bank credential aggregation (Canada framework still unlaunched; revisit Phase 3+)
- ❌ US cards & programs (Canada-only dataset at launch)
- ❌ Applying for cards on users' behalf (we link out; affiliate integration later)
- ❌ Credit score monitoring
- ❌ Business/corporate card management (personal cards first; sole-prop business cards supported as regular cards)

## Success Metrics (first 12 months)

- **Activation:** ≥60% of signups complete Shortcut setup within first session
- **Capture health:** median captured transactions/user/week ≥ 8; draft→confirmed acceptance rate ≥ 85%
- **Retention:** M3 retention ≥ 35% of activated users
- **Data quality:** ≥90% of transactions auto-categorized with confidence ≥ 0.9
- **Program data freshness:** redemption/transfer table updated ≤ 48h after public change
- **North-star:** # of "optimizations taken" (user acts on a suggestion: applies, switches card, redeems)

## Principles

1. **Capture is king.** Everything downstream depends on frictionless spend ingestion.
2. **Never lose a bonus.** Deadline and eligibility alerts are sacred notifications.
3. **Show the math.** Every reward number is explainable down to the rate × amount line.
4. **Canada-deep, not global-shallow.**
5. **Educational, not financial advice.** Clear disclaimers; no dark patterns pushing applications for affiliate revenue.
