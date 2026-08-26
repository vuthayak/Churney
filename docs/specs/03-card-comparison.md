# Spec 03 — Card Comparison

> Status: draft · Phase 1 (basic) → Phase 2 (personalized) · Depends on: curated DB, Spec 02 valuations

## 1. Summary

Compare Canadian credit cards head-to-head and rank them against the user's real spend. Three modes:

1. **Head-to-head** (public, anonymous): 2–3 cards side by side
2. **Wallet ranking**: rank *my* cards for my actual spend mix
3. **Explorer ranking**: which card should I get next given my spend profile

## 2. Comparison Dimensions

Every comparison renders the full matrix; sections collapsible:

| Group | Fields |
|---|---|
| Costs | Annual fee ($0 first year?), extra cardholder fee, FX fee %, interest rates |
| Welcome bonus | Offer terms (min spend, deadline days, reward, EAV), eligibility notes, last verified |
| Earn structure | Rate matrix: rows = categories (taxonomy v1), cols = cards; base rate row; caps annotated inline |
| Program | Loyalty program, baseline cpp valuation, transfer partners count, redemption flexibility score (see Spec 04) |
| Perks | Credits (e.g., annual travel credit, Uber/Netflix credits `[VERIFY]`), lounge access, Nexus/TSA |
| Insurance suite | Travel medical, trip cancel/interruption, delay, baggage, mobile device, purchase security, extended warranty `[VERIFY]` |
| Requirements | Personal/household income minimums, province availability |
| Acceptance | Network(s); network caveats surfaced contextually (e.g., "Costco Canada accepts Mastercard only") |

## 3. Personalized Net Value (core algorithm)

```
net_annual_value(card, profile) =
    Σ_categories  min(spend_cat, cap_remaining) × rate_cat × cpp_program
  + Σ_categories  overflow(spend_cat) × base_rate × cpp
  + welcome_bonus_eav_first_year            [year 1 only]
  + Σ perk_credits_utilized(profile)        [only if profile says user uses them]
  − annual_fee
```

- `profile.spend_by_category`: monthly averages from **confirmed transactions** (last 90d weighted 2x, prior 90d 1x), or manual sliders when insufficient history (onboarding state).
- Caps modeled against current-year consumption if wallet-tracked, else naive.
- Perk utilization: user toggles which perks they'd actually use (default: none — conservative).
- Output both **points value** and **cash-equivalent**, labeled with cpp assumption used.

## 4. Ranking Modes

- **For my spend:** sort wallet (or explorer candidates) by net_annual_value; show delta vs current-best card; flag "you're paying N dollars/year for this card you underuse".
- **Break-even views:** "grocery spend needed for card A to beat card B"; sensitivity slider.
- **Churn lens toggle:** include first-year bonus EAV and assume downgrade/cancel at month 12 (P1 mode; links to Spec 06).
- **Long-term hold lens:** exclude bonus EAV and exit assumptions; rank by ongoing net_annual_value as if held indefinitely — the lens for choosing daily-driver/keeper cards (Spec 05 §2). Cashback cards compete on equal footing here: their earn values at 1 cpp face value with no redemption assumptions. This is also how keeper recommendations are justified when a churned card's hold value beats its churn value.

## 5. UI Notes

- Sticky header with winner-per-row highlighting; tie handling explicit.
- Category matrix cells: rate chip + capped indicator + effective $ from user profile (when logged in).
- Mobile: horizontal scroll with frozen first column; key-facts summary card above fold.
- three.js optional flourish here is LOW priority — reserved for rotation planner instead; keep compare utilitarian.

## 6. Edge Cases

- Cards retired from market: comparable but flagged "no longer offered".
- Terms changed recently: show diff tooltip (effective-dated versions power this).
- Income requirement unmet: banner, not hard block (issuer discretion exists `[VERIFY]`).

## 7. Acceptance Criteria

1. Fixture profiles produce hand-computable net values exactly (golden tests ×5).
2. Head-to-head shareable via URL params; renders for logged-out users.
3. Wallet ranking updates within 24h of new transactions (or on-demand recompute button).
4. Every displayed number has derivation tooltip.
