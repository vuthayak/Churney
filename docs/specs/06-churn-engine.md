# Spec 06 — Churn Engine

> Status: draft · Phase 2 · Depends on: curated DB (offers), wallet history, Spec 02 spend velocity, Spec 05 constraints
> Inspiration appendix: US tooling at §7

## 1. Summary

Tailored credit-card-churning suggestions for Canadian cards/programs only: rank which card the user should apply for next, when, and whether they can realistically hit min spend — using a maintained rulebook of issuer approval/eligibility heuristics and the user's tracked history.

**Positioning guardrail:** educational recommendations with explicit disclaimers; never auto-submit applications; future affiliate links clearly labeled.

## 2. Issuer Rulebook (`churn_rules`)

Versioned knowledge base; every rule row carries `source_url`, `last_verified_at`, `confidence` and is `[VERIFY]`-gated before user-facing use.

| Issuer | Heuristics (seed — all require verification + ongoing monitoring) |
|---|---|
| Amex Canada | Welcome bonus **once per lifetime per product**; card-family spacing guidance; charge vs credit card distinctions; no hard credit pull historically for existing holders on some products `[VERIFY]` |
| TD | Bonus typically once per product per N months; product-switch bonus eligibility differs from new application `[VERIFY]` |
| CIBC | Similar product-cycle windows; Aventura family nuances `[VERIFY]` |
| RBC | Once-per-product-lifetime pattern; Premier Banking relationship effects `[VERIFY]` |
| BMO | Product-cycle windows; frequent promo variants count as separate products? `[VERIFY]` |
| Scotiabank | Bonus eligibility conditions incl. prior holders on account `[VERIFY]` |
| NBC / Desjardins / Tangerine / Simplii / Neo | Simpler rules; cashback focus; Neo soft-pull pre-qualification angle |

Rule types modeled:
- `lifetime_lockout(issuer?, product)` — burned forever after bonus
- `program_lockout(program, tier)` — loyalty-program-level cap independent of issuer (Aeroplan one-bonus-per-tier-lifetime; clawback risk — see research/03)
- `cycle_window(issuer, months)` — reapply cooldown
- `concurrent_limit(issuer, n)` — max open/held products; application velocity. **Keeper/daily-wallet cards count toward this limit** (Spec 05 §4.2) — holding 3 TD keepers constrains TD applications
- `inquiry_limit(issuer, bureau, max, window)` — hard inquiry-count gate (MBNA 5/6 TransUnion)
- `pull_policy(issuer)` — inquiry sensitivity notes / bureau pulled
- `switch_vs_new(product_a → product_b)` — whether switch earns bonus

Seed rows: [`db/seeds/churn_rules.sql`](../../db/seeds/churn_rules.sql), derived from research doc [02-issuer-rules-canada.md](../research/02-issuer-rules-canada.md).

## 3. Eligibility Engine

Inputs: user's `user_cards` (open/closed dates, `role`), application log, bonus-posted confirmations.

Output per candidate offer:
```
eligible | eligible_with_caveats(caveat[]) | blocked(rule_refs[])
+ earliest_eligible_date  ← from cycle windows & lockouts
```

Candidate universe includes **cashback-card offers** (bank flat-rate and tiered cashback cards) — they are legitimate churn targets when their welcome bonus is worthwhile (e.g., Tangerine Money-Back 10% promo `[VERIFY]`), and simultaneously strong keeper candidates (Spec 05 §4.2). Cashback bonuses are valued at face value (`reward_cashback_minor`, 1 cpp) with no redemption assumptions.

Keeper-role interaction: cards the user has pinned as keepers are excluded from *exit* recommendations, but their continued holding still feeds eligibility math (open-card counts, product-cycle windows).
Property tested against Spec 05: optimizer plans never contain blocked applies before their unlock date.

## 4. Min-Spend Feasibility Score

Given offer(min_spend M, deadline_days D) and user's trailing spend:

```
organic_28d      = qualifying spend rate (excl. offer-excluded categories)
horizon_days     = days until deadline
organic_total    = organic_28d × horizon/28
gap              = max(0, M − organic_total)
feasibility      = f(gap):
   gap == 0                → "comfortable"
   gap ≤ 0.5 × organic     → "achievable" (mild acceleration)
   gap > that              → "stretch" (needs planned spend)
```

Stretch mitigation suggestions (informational): known categories where users legitimately accelerate (prepaid recurring, insurance premiums, tax installments) — generic education, not fabricated-spend advice; compliance-reviewed copy.

## 5. Application Timing

Recommendations adjust apply-date by:
- Cycle-window unlocks (wait-until date)
- Statement-close awareness for reporting `[VERIFY]` utility
- Offer expiry dates in DB ("current public offer ends X — apply by")
- Big-ticket known events from rotation plan (apply *before* planned large spend)
- Personal pacing setting caps inquiries/month

## 6. Recommendation Output

Ranked list, each item:

```jsonc
{
  "offer_id": "...",
  "rank": 1,
  "expected_value": { "bonus_eav": 85000 /* cents */, "fee_net_year1": -79900, "assumptions_ref": "..." },
  "eligibility": "eligible",
  "min_spend": { "amount": 300000, "deadline_days": 90, "feasibility": "comfortable",
                 "projected_completion": "2026-10-14" },
  "timing": { "recommended_date": "2026-09-01", "reasons": ["cycle window opens", "before Q4 travel spend"] },
  "post_churn_role": "keeper" | null,
    // non-null when Spec 05 optimizer projects the card's ongoing net value beats all
    // keeper alternatives for its categories — recommendation becomes
    // "apply, earn bonus, then keep as daily driver" instead of apply→cancel
  "rationale_trace": ["+MR 60k @1.75cpp baseline", "−$250 fee", "+grocery multiplier fits profile #2 category"],
}
```

Cashback offers use the same shape with `bonus_eav` = `reward_cashback_minor` at face value and a cashback-specific rationale trace (e.g., `"+$250 cashback bonus @1cpp face value"`).

UI: card stack with expandable math; "why not higher?" per item shows blocking rules or weaker fit.

## 7. Appendix — US Inspiration Map

| US tooling | What we borrow | What doesn't transfer |
|---|---|---|
| r/churning tracking spreadsheets | Event log model (apps, approvals, bonus posts), eligibility mental models | Chase 5/24 (no Canadian analog), issuer-specific US quirks |
| CardPointers | Offer/credit tracking UX, alert cadence | Amex-offer-centric scope |
| AwardWallet | Balance-linked insights concept | US program depth |
| Frequent Miler / TPG "best current offers" | Live-offer freshness discipline, bonus calendars | Affiliate-driven ranking bias (avoid) |

## 8. Compliance & Trust

- Prominent "educational information, not financial advice" on every recommendation surface.
- No dark patterns: recommendations ranked by user value, not affiliate potential; sponsored placement (future) visually distinct and excluded from default sort.
- Rule rows cite sources; stale rules (>90d unverified) excluded from blocking decisions (advisory-only).

## 9. Acceptance Criteria

1. Every rule type exercised in fixtures incl. multi-issuer interactions; blocked/unlock logic property-tested.
2. Feasibility scorer matches hand-computed cases across comfortable/achievable/stretch bands.
3. Rationale traces render fully; no recommendation without trace.
4. Stale-rule advisory behavior verified (>90d case).
5. Compliance copy review sign-off before Phase 2 launch.
6. Cashback-offer fixture: bonus EAV computed at face value with no cpp assumptions; `post_churn_role` populated per Spec 05 keeper logic.
7. Property test: plans never recommend exiting a user-pinned keeper card.
