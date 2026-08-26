# Spec 04 — Program Comparison (Live)

> Status: draft · Phase 2 (live jobs) — static seed in Phase 1 · Depends on: data-sourcing pipeline, effective-dated tables

## 1. Summary

A living dataset of Canadian loyalty **programs**: what a point is worth, where it can be redeemed, which partners accept transfers at what ratios, and which **ongoing/limited-time conversion bonuses** are active. This is the intelligence layer that makes Churney's valuations and churn recommendations credible. It must be demonstrably fresh.

## 2. Scope — Programs (seed list)

| Program | Issuer linkage | Currency |
|---|---|---|
| Aeroplan | Air Canada / Amex TD CIBC partners | points |
| Membership Rewards (MR) | Amex | points |
| Avion Rewards | RBC | points |
| BMO Rewards | BMO | points |
| TD Rewards | TD | points |
| Scene+ | Scotiabank / Cineplex partnerships | points |
| Aventura Rewards | CIBC | points |
| BONUSDOLLARS | Desjardins | cashback units |
| Cash back (generic) | Tangerine, Simplii, Neo, etc. | cents |
| Marriott Bonvoy, Choice, Best Western | hotel transfer targets | points |

Programs are entities with card memberships; cards link to exactly one earn program (some cards can choose program at signup — model as card variants `[VERIFY]`).

## 3. Data Captured Per Program

### 3.1 Redemption options (`redemption_options`)
- Type: `fixed_travel` (portal), `transfer_partner`, `statement_credit`, `gift_card`, `merchandise`, `experiences`, `pay_with_points`
- Value: baseline cpp range (min/typical/max) + example redemptions
- Notes: blackout/degradation warnings

### 3.2 Transfer/conversion matrix (`transfer_rates`)
- From-program → to-program ratio (e.g., MR → Aeroplan 1:1; Avion → Avios 1:1 up to annual cap `[VERIFY]`; hotel ratios often non-1:1)
- Minimum transfer blocks, caps
- **Effective-dated**: rows carry `valid_from/valid_to`; historical ratios preserved

### 3.3 Conversion bonuses (`conversion_bonuses`) ⭐ differentiator
- Limited-time multiplier events (e.g., "+25% when transferring MR→Aeroplan until Aug 31")
- Fields: bonus_pct or bonus_ratio, start/end dates, eligibility constraints (card-specific? first-transfer-only?)
- Sourced via scheduled jobs + manual admin confirmation; status lifecycle `rumored → confirmed → active → ending_soon → expired`
- Powers UI: banner strip "Active conversion bonuses" on dashboard + program pages; optional user notification opt-in

### 3.4 Valuations (`program_valuations`)
- Admin-maintained cpp baselines per redemption context (economy, business, hotels, cash-equivalents)
- Change log public-facing ("we lowered typical Aeroplan economy value from X to Y because…")
- **Cashback programs** (BONUSDOLLAR, generic cash back): single `cash_floor` row at 1.00 cpp — no redemption-option matrix or transfer graph applies; these programs are excluded from flexibility scoring and surface instead as daily-wallet/keeper candidates (Specs 03 §4, 05 §2)

## 4. Freshness Pipeline

| Cadence | Job | Output |
|---|---|---|
| Daily 06:00 ET | Scrape broker/aggregator partner pages + issuer promo pages for bonus/ratio changes (see docs/04 §scrapers) | Candidate diffs |
| Daily 07:00 ET | LLM-assisted diff extraction → structured candidates → review queue | Draft changes |
| Weekly Mon | Full audit sweep of every live row against sources; stamp `last_verified_at` | Freshness report |
| Event-driven | Admin manual edit anytime | Immediate publish w/ changelog entry |
| On expiry end-date passes | Auto-flip bonus status → `expired` | None |

**Change detection:** normalized snapshots hashed per source page; hash drift → re-extract → diff vs current DB → open review item (never auto-publish ratio/bonus changes).

**Public freshness signal:** every program page shows "Last verified {date}"; stale >14d rows get warning badge and drop out of recommendation weighting (Specs 02/05/06 consume only fresh rows).

## 5. Comparison UI

- **Matrix view:** programs as columns × dimensions as rows: baseline cpp, best fixed value, # transfer partners, notable ratios, active bonuses, flexibility score.
- **Transfer graph:** interactive visualization (force-directed or sankey) of the transfer network from any program; edges annotated with ratio + live-bonus flame icon.
- **"I have X points" calculator:** input balances → show portfolio value under each redemption strategy; suggests best current bonus plays.
- **History tab:** ratio/bonus/valuation timeline (effective-dating pays off here) — e.g., "Avios ratio changed Mar 2025".

## 6. Flexibility Score (0–100)

Applies to **points programs only**. Cashback programs skip this metric (their value needs no flexibility). Composite heuristic, weights tunable in admin:
- # of transfer partners (30)
- Ratio quality (fraction of partners at ≥1:1... normalized) (20)
- Non-airline redemption floor cpp (cash/gift floor) (20)
- Active bonus frequency over trailing 12m (15)
- Point stability history (# of devaluations) (15)

## 7. Acceptance Criteria

1. Seed dataset covers all §2 programs with ≥1 verified source each before launch.
2. Bonus expiry auto-transitions work; no expired bonus renders as active (tested across DST boundaries).
3. Review queue prevents unpublishable states (ratio null, overlapping effective ranges).
4. Transfer calculator matches hand-computed fixtures including a stacked bonus case.
5. Weekly audit produces report listing every row's age; ops dashboard shows % fresh.
