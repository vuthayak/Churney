# 03 — Loyalty Programs & Transfers

> Feeds Spec 04 (program comparison) and the Aeroplan overlay rules in Spec 06.
> Confidence legend: see [README](./README.md). Compiled 2026-08-22.

## 1. Aeroplan Program-Level Rules ⚠️ Highest-Priority Knowledge

Aeroplan is "the crown jewel of Canadian churning" — co-branded with TD, CIBC, and
Amex — but it carries **program-level bonus restrictions that sit on top of issuer
rules**.

### The New Card Bonus T&C (Dec 19, 2022)

`[OFFICIAL]`

> A member may be granted a maximum of **one New Card Bonus for each type of
> Aeroplan Credit Card** they become a holder of, **regardless of issuer**. Card
> types: entry, core, premium, core small business, premium small business.
> → Maximum of ~5 Aeroplan card bonuses per lifetime across all issuers.

Practical consequences:

- Getting the TD Aeroplan Visa Infinite bonus blocks the CIBC Aeroplan Visa Infinite
  bonus (same "core" tier). `[OFFICIAL]`
- An Amex Aeroplan card can be a separate bonus since Amex cards are charge-style
  products outside TD/CIBC's Visa tiers — but holding >1 same-tier card may itself
  violate T&Cs. `[COMMUNITY]`
- Holding >1 Aeroplan card of any tier or at the same bank "may constitute violation
  of Aeroplan Program Terms" (per ChurningCanada wiki annotation).

### October 2024 Clawbacks — precedent event

`[COMMUNITY — widely reported]`

- ~Oct 30, 2024: Aeroplan deducted points (~10,000 per incident, multiple deductions
  possible) from members who'd earned multiple same-tier WBs since 2022.
- Scale: roughly **17,000 members affected**; TD/CIBC Visa cards hit; Amex largely
  spared (community hypothesis: Visa duplication is the clear T&C violation).
- Only the initial welcome-bonus portion was clawed back; MSR-based bonuses kept;
  no account closures reported. Enforcement was described as customer-friendly *but*
  retroactive.
- Earlier datapoint (2022–2023): >3 WBs since policy change triggered firm warnings
  before points were taken.

**Engine implication:** the churn engine must model Aeroplan tier-level lockouts as a
first-class rule (`program_lockout(program, tier)`) and warn users *before*
they apply for a same-tier co-brand, not after.

### Excessive-use clause

Aeroplan T&Cs also reserve the right to suspend/terminate accounts for "excessive use
of Welcome Bonus offers" — vague language, sole discretion. `[OFFICIAL]`

## 2. Transferable Currencies & Ratios

From the r/churningcanada Starter Guide `[COMMUNITY — ratios change; monitor]`:

### Amex MR (Canada)

| Partner | Ratio |
|---|---|
| Aeroplan | 1:1 |
| British Airways Executive Club (Avios) | 1:1 |
| Flying Blue (AF/KLM) | 1:0.75 |
| Asia Miles (Cathay) | 1:0.75 |
| Delta SkyMiles | 1:0.75 |
| Etihad Guest | 1:0.75 |
| Hilton Honors | 1:1 |
| Marriott Bonvoy | 1:1.2 |

### HSBC Rewards

| Partner | Ratio |
|---|---|
| Asia Miles | 25:8 |
| KrisFlyer (Singapore) | 25:9 |
| Avios | 25:10 |

⚠️ Legacy post-RBC acquisition. `[VERIFY]`

### RBC Avion (while holding an Avion card)

| Partner | Ratio |
|---|---|
| Avios | 1:1 |
| Asia Miles | 1:1 |
| American AAdvantage | 1:0.7 |
| WestJet Rewards | 100:1 |

### Marriott Bonvoy

Unfavorable airline transfers: 3:1 base, +5,000 airline points per 60K Bonvoy block
→ effective **2.4:1**. `[COMMUNITY]`

### Direct-earn programs (no transfer needed)

Aeroplan (via TD/CIBC/Amex co-brands), Avios, Asia Miles, Flying Blue, WestJet
Rewards. `[COMMUNITY]`

### Other bank programs

Scene+ (Scotiabank), TD Rewards, CIBC Aventura, BMO Rewards, MBNA Rewards — mostly
portal-redemption currencies; some cash-out paths exist (see tactics doc, RHT).
`[COMMUNITY]`

## 3. Transfer Bonuses

Issuers run periodic transfer bonuses of **10%–50%**, unpredictable in timing.
Churney's Spec 04 live-program tracking should treat these as first-class,
time-boxed data rows (they materially change redemption math and the optimal
transfer moment). `[COMMUNITY]`

## 4. Points Valuation Baselines

Community valuation conventions Churney should adopt for its `expected_value` math
(all `[VERIFY]` + user-configurable):

- Value depends entirely on redemption; never quote a single "point value" without
  a redemption context ("show the math" principle from `00-vision.md`).
- Aeroplan business-class redemptions = highest CPP sweet spots, though devaluations
  have raised sweet-spot pricing over time. `[COMMUNITY]`
- Cash-equivalent floors (statement credits, gift cards) set the minimum rational CPP
  for each currency.

## Sources

- Rewards Canada — Aeroplan clawbacks: https://blog.rewardscanada.ca/credit-cards/aeroplan-clawing-back-points/
- Seat 31B — Aeroplan T&C excessive-use language: https://www.seat31b.com/2022/10/avoid-chase-aeroplan-co-branded-cards/
- ChurningCanada wiki — Starter Guide (transfer tables): https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/getting-started
- ChurningCanada wiki — Application Rules (Aeroplan annotations): https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/application-rules
- Fimaster — Aeroplan factor in 2026 profitability: https://fimaster.com.br/ca/credit-card-churning-canada/
