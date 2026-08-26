# 02 — Issuer Rules (Canada)

> The heart of the Canadian churning rulebook. Feeds Spec 06 `churn_rules` table.
> Confidence legend: see [README](./README.md). Compiled 2026-08-22.

## 1. Mapping to Engine Rule Types

Per `docs/specs/06-churn-engine.md` §2, each fact below should seed one of:

- `lifetime_lockout(issuer?, product)` — bonus burned forever after earning
- `program_lockout(program, tier)` — loyalty-program-level cap independent of issuer
- `cycle_window(issuer, months)` — reapply cooldown before next bonus
- `concurrent_limit(issuer, n)` / velocity limits — max cards or applications per window
- `inquiry_limit(issuer, bureau, max, window)` — hard inquiry-count gate at a bureau
- `pull_policy(issuer)` — bureau pulled + inquiry sensitivity
- `switch_vs_new(product_a → product_b)` — whether a product switch earns a WB

**Critical structural difference vs. the US:** Canada has **no Chase 5/24-style
universal rule**. Rules are issuer-specific, often unwritten, and enforced unevenly
— which is exactly why they must live in a versioned, sourced, `[VERIFY]`-gated DB.

## 2. Issuer-by-Issuer

### American Express Canada

| Rule | Detail | Confidence |
|---|---|---|
| Once-per-lifetime per **product** | "Welcome offer not available to applicants who have or have had this Card." Per-product, not per-family: holding Gold doesn't block Platinum bonus | `[OFFICIAL]` enforcement `[COMMUNITY]` |
| Possible resets | Community datapoints suggest eligibility may return after ~3+ years; not guaranteed, do not rely on it | `[DATAPoint]` |
| Business 90-day rule | Auto-reject if applying for Business Gold and Business Platinum within 90 days ("duplicate" on backend) | `[COMMUNITY]` |
| Pop-up jail | Application may warn "approved but not eligible for the bonus." Triggers: rapid open/close cycles, low organic Amex spend. Recovery: months of organic spend | `[COMMUNITY]` |
| Enforcement | Strictly enforced; calling the bank to dispute forfeits future goodwill | `[COMMUNITY]` |

Sources: ChurningCanada wiki Application Rules; Prince of Travel; churncards.com issuer rules.

### RBC

| Rule | Detail | Confidence |
|---|---|---|
| **1/90 rule** | Only **one approved application per 90 days**, firmly enforced with auto-rejection | `[COMMUNITY]` |
| Product switching | Switches can trigger WB eligibility (e.g., ION → Avion VI); community-documented cycle ION → Avion VI → BA VI → WestJet WE over 18–24 months | `[DATAPoint]` |
| AF refunds | Pro-rated annual fee refund on cancellation | `[COMMUNITY]` |

Source: Prince of Travel (1/90), getchurn.app issuer guide, ChurningCanada wiki.

### TD

| Rule | Detail | Confidence |
|---|---|---|
| Cycle window | Aeroplan Visa products: eligible for bonus if last application for that product was **>12 months ago**. First Class Travel family: eligible if last activation/closure >12 months ago | `[COMMUNITY — wiki w/ enforcement note]` |
| Terms reservation | T&Cs reserve the right to limit accounts/bonuses per person | `[OFFICIAL]` |
| Ineligibility effect | Missing bonus generally forfeits only the first-purchase bonus portion, not the full MSR-based bonus | `[COMMUNITY]` |

Source: ChurningCanada wiki Application Rules (TD panel).

### CIBC

| Rule | Detail | Confidence |
|---|---|---|
| Lenient | No widely-reported exclusion period or firm application rules | `[COMMUNITY]` |
| Multi-card trick | High-limit approvals sometimes allow opening multiple CIBC cards off a single inquiry | `[DATAPoint]` |
| Product switches | Supported across Aventura/Aeroplan families but not all switches earn bonuses — must confirm per switch | `[COMMUNITY]` |
| Elevated offers | Predictable elevated WB windows (back-to-school, Black Friday, RRSP season) worth waiting for | `[COMMUNITY]` |

Source: Prince of Travel, getchurn.app issuer guide.

### Scotiabank

| Rule | Detail | Confidence |
|---|---|---|
| 24-month exclusion | Not eligible for any WB if an existing Scotia consumer cardholder **or** held one in the prior 24 months | `[COMMUNITY]` |
| Enforcement | Partially enforced; system may not auto-block but CSRs will not help when blocked | `[COMMUNITY — wiki annotation]` |
| Dual-network strategy | Same franchise exists as separate Visa and Amex products (e.g., Gold Amex vs Passport VI) = two distinct WBs | `[COMMUNITY]` |

Source: ChurningCanada wiki Application Rules (Scotiabank panel).

### BMO

| Rule | Detail | Confidence |
|---|---|---|
| Velocity sensitivity | Datapoints suggest declines after >2 BMO applications in 12 months; no published rule | `[DATAPoint]` |
| Pull policy | TransUnion in most provinces; Equifax in Quebec/some Atlantic provinces | `[DATAPoint]` |

Source: getchurn.app issuer guide.

### MBNA

| Rule | Detail | Confidence |
|---|---|---|
| **5/6 rule** | Rejects if **5+ TransUnion inquiries in the past 6 months** including the current application. Failed applications count against you. Existing cardholders can bypass via splitting credit from another MBNA card | `[COMMUNITY]` |

Source: Prince of Travel.

### HSBC (now RBC-owned — status `[VERIFY]`)

| Rule | Detail | Confidence |
|---|---|---|
| 12-month exclusion | No WB if held HSBC World Elite MC within prior 12 months; no WB via card switching | `[COMMUNITY — wiki, marked enforced]` |

⚠️ HSBC Canada was acquired by RBC (closed early 2024). Card lineup is winding down;
treat as legacy data. `[VERIFY]`

### National Bank (NBC)

| Rule | Detail | Confidence |
|---|---|---|
| 24-month exclusion | No WB if any NBC cardholder in the last 24 months | `[COMMUNITY — wiki, marked enforced]` |

## 3. Cross-Cutting Rules

- **Velocity guideline:** community consensus caps at ~2–3 new cards per 6 months
  across all issuers to avoid decline spirals. `[COMMUNITY]`
- **Bureau spreading:** know each issuer's pull (Equifax vs TransUnion) and time
  applications so neither bureau accumulates too many recent inquiries. `[COMMUNITY]`
- **Aeroplan program-level overlay:** independent of issuer rules, Aeroplan's own
  T&Cs cap New Card Bonuses — see [03-programs-and-transfers.md](./03-programs-and-transfers.md).
  Any engine rule involving an Aeroplan co-brand must check BOTH the issuer rule and
  the program rule.
- **Never-call policy:** r/churningcanada explicitly instructs members never to call
  banks about missing bonuses (see [04-risks-and-compliance.md](./04-risks-and-compliance.md)
  §4). Churney UI copy must mirror this guidance.

## 4. Seed Table (proposed `churn_rules` rows)

> **Lifted into SQL:** [`db/seeds/churn_rules.sql`](../../db/seeds/churn_rules.sql)
> (idempotent, keyed on `params.seed = 'churn_rules_v1'`; canonical — the table below
> mirrors it). The DDL lives in `docs/03-data-model.md` §9. Reference table below.

All rows `[VERIFY]` before user-facing use.

| issuer | product_scope | rule_type | value | source_confidence |
|---|---|---|---|---|
| AMEX_CA | any_product | lifetime_lockout | once_per_lifetime | official_tnc |
| AMEX_CA | biz_gold+biz_plat | concurrent_limit | 90d_between_apps | community |
| AMEX_CA | any_product | concurrent_limit | popup_jail_risk (advisory-only heuristic) | heuristic |
| RBC | any | cycle_window | 90d_between_approvals | community_strong |
| RBC | ion→avion_vi cycle | switch_vs_new | switch_earns_bonus=true | datapoint |
| TD | aeroplan_visa_* | cycle_window | 12mo_same_product | community_wiki |
| TD | fct_family | cycle_window | 12mo_since_close_or_activation | community_wiki |
| SCOTIA | any_consumer | cycle_window | 24mo_any_cardholder | community_partial_enforcement |
| BMO | any | concurrent_limit | ≤2 apps/12mo | datapoint |
| BMO | any | pull_policy | TU default; Equifax QC/Atlantic | datapoint |
| MBNA | any | inquiry_limit | <5 TU_inquiries/6mo | community_strong |
| MBNA | any | pull_policy | TransUnion | community_strong |
| HSBC (legacy, inactive) | world_elite_mc | cycle_window | 12mo_prior_holder; no bonus via switch | community |
| NBC | any | cycle_window | 24mo_any_cardholder | community_wiki_enforced |
| AEROPLAN_PROGRAM (program_id set) | any_co_brand | program_lockout | one_bonus_per_tier_lifetime | official_tnc |

CIBC: no rules seeded — no widely-reported exclusion period or firm application rules
(§2). Revisit if enforcement patterns emerge.

## Sources

- ChurningCanada wiki — Application Rules: https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/application-rules
- Prince of Travel — application rules by issuer: https://princeoftravel.com/guides/credit-card-rules-how-often-can-you-apply/
- getchurn.app — issuer-by-issuer guide: https://getchurn.app/blog/canadian-churning-rules-by-issuer
- PointsBinder — Canadian-specific rules: https://pointsbinder.com/blog/credit-card-churning-canada-beginners-guide
