# Spec 05 — Rotation Planner

> Status: draft · Phase 2 · Depends on: Spec 01 (spend), Spec 02 (rewards), Spec 06 (issuer rules), curated DB

## 1. Summary

Model a user's card portfolio as **two coordinated tracks**: a **rotation** (planned, time-ordered sequence of card acquisitions, product switches, and exits that capture welcome bonuses) and a **daily wallet** (stable keeper cards — including cashback cards — that absorb everyday spend month after month and are never churned). The optimizer maximizes combined value across both tracks: every dollar of real spend lands on the best card at every point in time, welcome bonuses are captured without violating issuer approval rules, and the user always has a sensible set of everyday cards they keep long-term.

## 2. Core Concepts

| Concept | Definition |
|---|---|
| **Rotation** | User's active plan: ordered `rotation_events` on a timeline |
| **Event types** | `apply` (new card), `product_switch` (convert existing card within issuer), `cancel`, `downgrade_no_fee`, `pause`, `convert_to_keeper` (exit rotation; card joins daily wallet permanently) |
| **Slot** | A position in rotation occupied by one card from its start event onward |
| **Keeper card** | A card designated for the daily wallet (`user_cards.role='keeper'`, or `'auto'` cards the optimizer promotes). Keepers never receive exit events (`cancel`/`downgrade_no_fee`) unless the user unpins them, or the planner issues a keeper-replacement recommendation — a rationale-backed proposal to unpin and swap in a better daily option (which may itself require a churn cycle; see §6) |
| **Daily wallet** | The planner's stable category→card assignment over keeper cards (e.g., "grocery → Card A, everything else → Card B"). Stored on `rotation_plans.daily_wallet`; changes rarely, only when a materially better keeper emerges |
| **Utilization window** | Period where a card is "the right card to tap" for specific categories |
| **Churn friction** | Cost model of applying again: credit inquiry impact, approval-rule cooldowns (from Spec 06 rulebook) |

Keeper designation is **both user-driven and optimizer-suggested**: users can pin any card as a keeper (including no-fee cashback cards like bank flat-rate cards `[VERIFY]` terms); the optimizer may additionally recommend promoting a churned card to keeper when its ongoing net annual value beats all alternatives for its categories.

## 3. Timeline View (three.js)

The signature visualization:

- **Scene:** horizontal timeline rail; each wallet/rotated card rendered as a 3D card-object with height = net annual value contribution over that segment; color = program.
- **Overlays:** min-spend progress rings on cards mid-bonus; fee-posting markers; eligibility unlock dates as gates on the rail; conversion-bonus flames (Spec 04) when they intersect planned redemption timing.
- Interactions: drag to shift an apply-date → optimizer re-solves and animates delta ("+2 weeks delay costs $140 in bonus value"); click card → detail panel; pinch to zoom year↔quarter.
- Fallback 2D gantt view (accessibility + low-power devices); scene is progressive enhancement.

## 4. Optimizer

### 4.1 Inputs
- Personal spend profile (monthly by category, from confirmed txns; manual sliders fallback)
- Current wallet + open dates + bonus statuses + per-card `role` (`keeper`/`churner`/`auto`)
- Keeper preferences: user-pinned keeper cards (immutable exits), optional max keepers / max total annual keeper fees
- Candidate universe: all live offers in curated DB filtered by issuer-rule eligibility (Spec 06) and income requirements — **includes cashback-card offers**, which are eligible both as churn targets (welcome bonus) and as keeper candidates
- Constraints: max simultaneous new applications per month (default 1 `[VERIFY]` guidance), user risk tolerance setting (conservative/balanced/aggressive)

### 4.2 Objective
Maximize expected 24-month value across both tracks:

```
V = churn_track + daily_wallet_track

churn_track =
    Σ_events  welcome_bonus_eav            -- points bonuses via cpp; cashback bonuses at face value
  − Σ_cards   fees_paid (netting credits actually used)
  − churn_friction_penalty(events)

daily_wallet_track =
    Σ_months Σ_categories spend_cat × best_daily_rate(cat, month) × cpp
  − Σ_keepers annual_fee_amortized
```

- `best_available_rate` (rotation slots) and `best_daily_rate` (daily wallet) respect network acceptance per merchant mix (Spec 02 §4) and category caps consumed in-month.
- Mixed portfolios valued coherently: points earn × program `baseline_cpp`; cashback earn at 1 cpp (`cash_floor` valuation). Both tracks may mix points and cashback cards.
- Keeper cards contribute to `daily_wallet_track` only — they never incur churn friction or exit events.
- The optimizer may schedule `convert_to_keeper` when a slot's post-bonus ongoing net value (its `best_daily_rate` contribution minus fee) beats promoting any other candidate — this is how a churned card becomes tomorrow's daily driver.
- Bonus EAV discounted by approval probability estimate from issuer rules + history.
- Constraint: keeper/daily-wallet cards count toward issuer `concurrent_limit` rules (Spec 06 §2) — keeping 3 TD cards constrains TD applications.

### 4.3 Algorithm
- v1: greedy beam search over next-event candidates (beam width ~50) with constraint pruning; the daily-wallet assignment is re-solved as best-per-category over keeper ∪ active-slot cards at each timeline step — sufficient given small candidate space (~40–80 live CA offers).
- Deterministic; same inputs → same plan. Every recommendation carries explanation trace: top 3 contributing terms.
- Recompute triggers: new txn week rollover, offer DB change affecting candidates, completed event, settings change, keeper pin/unpin.

### 4.4 Outputs
- **Daily wallet**: stable category→card mapping ("grocery → Amex Gold, everything else → Tangerine MC") with per-category monthly value math — surfaced prominently on dashboard as *the* daily answer for non-churning usage
- Ranked next-actions: "Apply for X around {date}" with rationale, min-spend feasibility (Spec 06 §4), projected completion date from spend velocity
- "Tap this card until {event}" utilization guidance per category for rotation cards mid-bonus
- Keeper recommendations: "After bonus posts, keep X as your {category} card" (`convert_to_keeper` events) with net-annual-value rationale
- Warning list: conflicts (e.g., applying while Amex lifetime-burned on target product), fee cliff alerts, keeper-fee creep alerts (total daily-wallet fees exceeding stated budget)

## 5. Min-Spend Tracking Integration

Each `apply` event links its offer:
- Start clock configurable: approval date or first statement `[VERIFY]` per offer
- Progress from confirmed qualifying txns (Spec 02 §7)
- Projection & deadline warnings (T-14d, T-7d, T-3d escalation)
- On completion: prompt "Bonus posted?" → confirm updates history feeding Spec 06

## 6. Fee Calendar & Exit Planning

- Per-card annual fee posting dates with reminder T-30d/T-7d
- Exit playbooks per card: downgrade paths known in DB (`product_switch` targets), retention-offer notes field
- First-year-free tracking: auto-flag "value delivered vs fee" at month 10
- Keeper cards: no exit playbook; instead an annual "keeper health check" — is this card still the best daily option for its categories net of fee? If not, planner proposes a replacement (which may itself require a churn cycle, respecting Spec 06 rules)

## 7. Edge Cases

| Case | Handling |
|---|---|
| Application rejected | Mark event `rejected`; record date; rules engine uses it for spacing heuristics |
| Offer pulled from market mid-plan | Plan flags stale slot; suggests nearest equivalent candidate |
| User spends way off-profile | Optimizer sensitivity note if plan robustness < threshold across ±30% category variance |
| Household pooling | Out of scope v1 (see vision P3) |
| User unpins a keeper | Planner re-solves: card re-enters candidate universe; daily wallet rebalances with explanation trace |
| Keeper card degrades (fee hike, category cut) | Effective-dated terms change triggers keeper health check; recommend switch/downgrade if beaten |
| All-spend-on-keepers user (no churning interest) | Plan degenerates to pure daily-wallet optimization; zero rotation events is a valid plan |

## 8. Acceptance Criteria

1. Golden fixture: 3-card household profile produces hand-verifiable plan improving naive baseline ≥15% over 24 months.
2. Drag-interaction re-solve < 500ms p95 (client-side approximation acceptable with server confirm).
3. All recommendations carry explanation traces; no unexplainable numbers.
4. Eligibility gates from Spec 06 respected in 100% of generated plans (property tests).
5. 2D fallback fully functional without WebGL.
6. Property test: user-pinned keeper cards receive zero exit events across 10k random plans.
7. Golden fixture: cashback-only profile (e.g., flat-rate bank cards) produces a coherent daily wallet with all values in CAD minor units — no cpp assumptions leak into cashback math.
