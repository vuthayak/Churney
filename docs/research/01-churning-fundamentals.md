# 01 — Churning Fundamentals

> Confidence legend: see [README](./README.md). Compiled 2026-08-22.
> Primary source: r/churningcanada Starter Guide (community wiki).

## 1. Definition

**Churning** is the practice of repeatedly opening credit cards to earn **welcome
bonuses (WB)**, then cancelling or downgrading the card before the next annual fee
(AF) hits, and moving on to the next offer. The term also covers broader
"maximizing credit card and bank account rewards." `[COMMUNITY]`

- Legal in Canada; it is not fraud as long as nothing is misrepresented to issuers.
  Issuers discourage it via T&Cs and uneven enforcement. `[OFFICIAL/COMMUNITY]`
- r/churningcanada frames it as a hobby requiring "hard work, commitment, time, and
  being responsible with money."

## 2. Bank Economics — Why Welcome Bonuses Exist

- WBs are customer-acquisition spend. Issuers earn ~2–4% interchange per
  transaction plus interest revenue from revolvers; most new cardholders more than
  repay the bonus over their lifetime. `[COMMUNITY]`
- Typical Canadian WB value: **$500–$2,500+** in travel value vs. $200–$300 for
  cash-back cards. `[COMMUNITY]`
- Issuers tolerate churners because: (a) interchange still flows during MSR
  completion, (b) competitive pressure to poach rivals' customers, (c) many churners
  keep 1–2 "keeper" cards with organic spend.

## 3. The Churn Cycle

The canonical loop (all sources agree):

```
research → apply → hit MSR → collect bonus + extract perks
        → cancel/downgrade before year-2 AF → repeat
```

Key operational facts:

| Fact | Detail |
|---|---|
| MSR clock | Starts at **approval**, not card receipt or activation `[COMMUNITY]` |
| Typical MSR | $3K–$7.5K within 3 months `[COMMUNITY]` |
| Cancellation timing | ~11 months in, before year-2 AF posts. RBC pro-rates AF refunds `[COMMUNITY]` |
| Bonus posting | Bank in-house points often post next business day after spend clears; airline/hotel co-brand points post after statement close (1–3 business days later) `[COMMUNITY]` |
| Points on closure | Some programs forfeit unredeemed points when the card is closed — redeem/transfer first `[COMMUNITY]` |

## 4. Earning Hierarchy

From the r/churningcanada Starter Guide — effective earn rates by strategy:

| Strategy | Effective rate |
|---|---|
| Single-card regular earning | ~1–2X |
| Category multiplier optimization (right card per purchase) | ~3–5X |
| Welcome bonus churning | **~10–20X** |

This hierarchy is the core product insight for Churney: WBs dominate everything, so
the app's highest-value job is never letting a user miss one (eligibility windows,
MSR deadlines), and its second-highest is routing daily spend to the right card.

## 5. Reward-Type Taxonomy

Three reward classes, ordered by increasing value but decreasing flexibility:

1. **Cash back** — simplest; some point currencies convert to cash easily.
2. **Bank in-house loyalty points** — Amex MR, RBC Avion, TD Rewards, Scotiabank
   Scene+, CIBC Aventura, BMO Rewards, HSBC Rewards, MBNA Rewards. Redeemable in
   issuer travel portals (OTA-style), merchandise, or transfers to airline/hotel
   partners. Mid flexibility.
3. **Airline/hotel loyalty points** — Aeroplan, Avios, Asia Miles, Flying Blue,
   Bonvoy, etc. Highest ceiling (business class, luxury hotels) but requires award
   availability research and program knowledge.

Transferable Canadian currencies and ratios → see [03-programs-and-transfers.md](./03-programs-and-transfers.md).

## 6. Award Availability Dynamics (why redemptions need planning)

`[COMMUNITY]`

- Airlines release limited award inventory; best selection opens at the schedule
  horizon (**~300–360 days out**); Lufthansa famously releases seats at T-14.
- Home-airport alliance coverage matters (e.g., Star Alliance Maldives options:
  Air India, Austrian, Singapore, Turkish).
- Community guidance: have an exit strategy for points *before* earning them.

## 7. Who Churning Fits

`[COMMUNITY — synthesized across Ratehub / Debt.ca / creditcardGenius]`

Good fit: good-to-excellent credit, pays balances in full, organized tracking,
comfortable with program complexity.

Bad fit (and who Churney should gently redirect): carries revolving debt, plans a
mortgage application within ~12 months, struggles to track bills, tends to overspend.

> Product note (per `00-vision.md` P2 persona): the "Points-Curious" segment mostly
> needs category optimization, not churning. The funnel should default them there.

## Sources

- r/churningcanada Starter Guide: https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/getting-started
- Ratehub, "Credit Card Churning 101": https://www.ratehub.ca/blog/credit-card-churning/
- WOWA, "Credit Card Churning in Canada": https://wowa.ca/credit-card-churning-canada
- creditcardGenius: https://creditcardgenius.ca/blog/credit-card-churning-canada
- Debt.ca: https://www.debt.ca/blog/credit-card-churning-should-you-do-it
- PointsBinder beginner guide: https://pointsbinder.com/blog/credit-card-churning-canada-beginners-guide
