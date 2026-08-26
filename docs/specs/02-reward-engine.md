# Spec 02 — Reward Engine

> Status: draft · Phase 1 · Owner: TBD
> Depends on: Spec 01 (transactions), data model (`cards`, `earn_rates`, `merchants`, `categories`), program valuations (Spec 04)

## 1. Summary

For every confirmed transaction, determine **what it was** (spend category via merchant resolution) and **what it earned** (points/cashback under the tapped card's earn structure), plus **what it should have earned** (best-in-wallet counterfactual). Output feeds dashboards, comparisons, rotation progress (min-spend tracking uses raw amounts, not this engine), and churn insights.

## 2. Pipeline

```
raw merchant string
      │
      ▼
[1] Normalize ──► [2] Merchant match ──► [3] Category assign ──► [4] Earn-rate resolve ──► [5] Compute
                  (exact/alias/fuzzy)     (default cat, overrides,   (base + multipliers,         rewards
                                           LLM fallback)              caps, promos)                + counterfactual
```

Runs async post-ingest; re-runs incrementally whenever any input below changes (merchant mapping correction, card terms update, valuation change).

## 3. Stage Details

### 3.1 Normalize
- Trim, uppercase, strip store numbers (`#123`, `\d{4,}` suffixes), strip city/province tokens, collapse whitespace, remove legal suffixes (LTD, INC).
- Keep original string alongside normalized form (`merchant_raw`, `merchant_norm`).

### 3.2 Merchant match (against `merchants` + `merchant_aliases`)
1. Exact alias hit → confidence 0.99
2. Normalized exact → 0.97
3. Token-set fuzzy (trigram similarity ≥ 0.85 within same brand family) → 0.80–0.90
4. No match → create `pending_merchants` entry; route to LLM fallback classifier for category-only assignment (confidence capped 0.75, flagged `unmatched_merchant`)
- User corrections write `merchant_aliases` (user-scoped first; admin can promote to global after review).

### 3.3 Category taxonomy (v1 — closed set)

| Slug | Examples (CA) |
|---|---|
| `grocery` | Loblaws, Superstore, Metro, Sobeys, No Frills, FreshCo, Costco* |
| `dining` | Tim Hortons, Starbucks, restaurants, Uber Eats, DoorDash, SkipTheDishes |
| `gas` | Petro-Canada, Esso, Shell, Husky, Ultramar |
| `transit_rideshare` | TTC/Presto, Uber, Lyft, gas-adjacent transit |
| `travel_air` | Air Canada, WestJet, airlines, OTAs (Expedia, Flight Centre) |
| `travel_hotel` | Marriott, Hilton, hotels, Airbnb |
| `travel_other` | Via Rail, car rentals, parking |
| `drugstore` | Shoppers Drug Mart, Rexall, London Drugs |
| `streaming_subs` | Netflix, Spotify, Crave, Disney+ |
| `recurring_bills` | Telus/Rogers/Bell, hydro, insurance (usually excluded from bonus categories `[VERIFY]`) |
| `entertainment` | Cineplex, Ticketmaster, Live Nation |
| `retail_online` | Amazon.ca, Best Buy |
| `retail_other` | Canadian Tire, Home Depot, Winners, everything else |
| `other` | Unclassified |

*Costco: warehouse accepts Mastercard only — network acceptance matters downstream (§5).

Rules:
- Categories are stable slugs; display names/themes change freely.
- Each merchant has exactly one `default_category`; per-user overrides allowed (`category_overrides`, applies to that merchant for that user).
- Some merchants are seasonal/ambiguous (e.g., Amazon sells groceries) — v1 keeps single default; document limitation.

### 3.4 Earn-rate resolution

Input: `(user_card, category, cad_amount_actual, occurred_at)`.

Resolution order (first applicable wins per card):
1. **Active promotion** (`earn_promotions`, effective-dated): e.g., "5x grocery Aug–Oct, cap $2,000"
2. **Category rate** (`earn_rates` where `category_id` matches): e.g., 3x dining
3. **Base rate**

Modifiers applied after base selection:
- **Caps:** monthly/annual caps on boosted portions (`cap_amount`, `cap_period`); overflow falls back to base. Cap ledger computed from confirmed transactions in period (household pooling later).
- **Minimums/exclusions:** some programs exclude government, utilities, etc. from earning entirely (`program_excluded_categories`, program-level) `[VERIFY]`.
- **Rounding:** points round half-up to integer per transaction; cashback accrues fractional cents, displayed rounded.

Output: `{points: int|null, cashback_minor: int|null, breakdown: [{layer, rate, qualifying_amount}], confidence}`.

Breakdown must be human-explainable: *"Tim Hortons $4.85 on Amex Gold: dining 2x = 10 pts ($0.10 @ 1.0cpp)"*.

### 3.5 Valuation (cpp)

- Cashback: 1 cpp trivially — backed by a `program_valuations` row with `context='cash_floor'`, `baseline_cpp=1.00` so mixed points+cashback math flows through one valuation path (Spec 05 §4.2).
- Points: valued per program × redemption context from the **valuation table** maintained via Spec 04 ops (admin-curated ranges, e.g., Aeroplan economy vs business-class redemptions).
- Default dashboard value: program's `baseline_cpp` (conservative). Optimistic values shown only inside comparison tools with labels.
- Mixed-wallet coherence rule: counterfactuals and daily-wallet comparisons (Spec 05) always compare in **CAD value** (points × cpp vs cashback at face), never raw units.

## 4. Counterfactual ("Best card") Calculation

For each confirmed transaction, compute rewards under **every active card in the user's wallet**, applying network acceptance reality:

- `merchants.accepted_networks[]` constrains eligible cards (e.g., Costco → Mastercard only; many independents → no Amex).
- Result: `best_wallet_alternative {user_card_id, would_earn_value, delta_vs_actual}`.
- Aggregate weekly/monthly into "missed optimization" total — the P2 hook metric.
- Never shown accusatorially; framed as "next time, tap X here".
- Daily-driver framing: for users with keeper cards (Spec 05 §2), counterfactuals compare against the **daily wallet assignment**, so "tap X here" guidance stays stable rather than flickering with mid-churn rotation slots.

## 5. Recalculation Triggers

| Input changed | Scope recalculated |
|---|---|
| Merchant alias/category correction | Affected merchant's txns (that user; global if promoted) |
| Card terms/earn rates edited (admin) | That card's txns from `valid_from` forward |
| Promotion added/expired | Affected card+category+window |
| Valuation (cpp) change | Displayed values only (computed lazily); persisted `transactions.value_cpp_snapshot` kept for historical accuracy |
| Wallet card closed | Stops future calc; history retained |

Persisted per transaction: `earned_points`, `earned_cashback_minor`, `value_cpp_snapshot`, `breakdown` jsonb, `engine_version`. Engine version bumps on logic changes enabling bulk recomputes.

## 6. Confidence & Review Queue

- Review gate = the auto-confirm boundary (Spec 01 §4): any confirmed transaction with `confidence < 0.9` OR `unmatched_merchant` OR cap-boundary ambiguity → task in `/spend/review`. There is no confirm-without-review band.
- Batch actions: confirm-all-from-brand-X-as-Y.
- Track precision: sampled audit of auto-categorizations weekly during beta.

## 7. Min-Spend Progress Integration

Welcome-bonus trackers consume **raw confirmed amounts only** (not reward calcs):

- Qualifying rules per offer: excluded categories (often cash-advances, balance transfers, sometimes everything counts `[VERIFY]`), start event (application approval or first statement — configurable), deadline (days or fixed date).
- Progress bar + **projected completion date** = today + (remaining ÷ trailing-28d velocity); warn state when projection > deadline − 7d.

## 8. Edge Cases

| Case | Rule |
|---|---|
| Return/refund pair | Net rewards on pair; if bonus-category cap was consumed, release it (ledger reversal) |
| Statement credits vs points timing | We model at transaction time; issuer posting delays ignored (documented) |
| Program devaluations mid-year | Historical rows keep snapshot cpp; projections use latest |
| Multiple promos stacking | Promos are exclusive per resolution order unless `stackable=true` `[VERIFY per promo]` |
| Gift-card purchases (buy GC with card) | Treated as retail at purchase; redemption-program nuance out of scope |

## 9. Performance

- Per-ingest enrichment target < 500ms async p95 (separate from ingest ack path).
- Bulk recompute: batch job, 100k txns < 10 min; idempotent by `engine_version`.

## 10. Acceptance Criteria (Phase 1 exit)

1. Top-200 curated Canadian merchants achieve ≥90% auto-categorization precision on beta corpus; unknown merchants degrade gracefully with review tasks.
2. Caps/promos/exclusions exercised in unit-tested fixtures for at least 6 representative card structures (flat cashback, tiered cashback, 5x-category-points, capped-multiplier, travel-fixed-value, transferable-points).
3. Counterfactual respects network acceptance (Costco example passes).
4. Breakdown strings render for every earned transaction; every number traceable.
5. Min-spend tracker reflects confirmed txns within 60s, with projected-date warnings firing correctly on fixture timelines.
