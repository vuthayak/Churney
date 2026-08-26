# 05 — Community Tactics Playbook

> What experienced Canadian churners actually do. Each tactic is tagged:
> **[ENGINE]** = Churney should model/automate it, or **[CONTENT]** = educational
> copy only. Confidence legend: see [README](./README.md). Compiled 2026-08-22.

## 1. Product Switching (PS) — the modern core tactic

`[ENGINE]`

Because fresh-application rules tightened, top churners increasingly **downgrade a
premium card to a no-fee sibling, then re-upgrade when offers reappear**. Benefits:
preserves account age (15% of score), avoids closures, sometimes triggers
"upgrade bonuses."

Documented cycle example — RBC `[DATAPoint]`:

```
hold RBC ION Visa (no fee) → product-switch to Avion VI → earn WB
→ after year 1 switch to BA VI → then WestJet WE → back to ION to reset
(repeatable every ~18–24 months)
```

Engine requirements:

- `switch_vs_new(product_a → product_b)` rules per issuer (doc 02).
- Track card lineage: a closed card is dead; a downgraded card keeps an upgrade path.
- CIBC nuance: switches qualify for bonuses only sometimes — must confirm per pair.

## 2. MSR Strategies (legitimate acceleration)

`[CONTENT]` — informational only; never coach overspending or fabricated spend.

| Method | Notes |
|---|---|
| Timing applications around planned spend | Property tax, insurance premiums, tuition, RRSP season `[COMMUNITY]` |
| Bill-pay services | Plastiq (~2–2.5% fee, no Amex), Paysimply, Chexy (rent) for bills that don't take credit `[COMMUNITY]` |
| Gift cards | Store cards for known future spend; open-loop prepaid cards carry fees `[COMMUNITY]` |
| Prepaying recurring bills | Phone/internet/utilities ahead of schedule `[COMMUNITY]` |

**Excluded entirely:** manufactured spending. Banned on r/churningcanada; issuers
treat it as grounds for closure/clawbacks (see doc 04 §5).

## 3. Refundable Hotel Trick (RHT)

`[CONTENT]` — describe in education content only; do not automate.

Steps as documented by the community wiki: book a refundable hotel via Expedia/
Booking.com with a travel-points card → redeem points against the posted travel
transaction → cancel the booking → points convert to near-cash value. Works with
bank portal currencies (not most portals' own bookings, not airline/hotel points).
CIBC Aventura requires redeeming while the transaction is pending. `[COMMUNITY]`

Compliance note: arguably against the spirit of travel-redemption categories;
keep as user-discoverable education, never a recommendation.

## 4. Multiplayer Mode (P2/household)

`[ENGINE — later phase]`

Spouses/partners each churn independently, doubling household capacity and letting
the household route applications to whichever partner has cleaner bureau history.
Points can be pooled within some programs (Aeroplan Family Sharing, Avios Household
Pooling) but **card→loyalty transfers are strictly same-person** across issuers.
P3 persona explicitly out of v1 (`00-vision.md`). `[COMMUNITY]`

## 5. Velocity & Bureau Management

`[ENGINE]`

- Cap ~2–3 new cards / 6 months overall. `[COMMUNITY]`
- Alternate issuers pulling Equifax vs TransUnion to keep both bureaus clean
  (BMO→TU in ON, RBC/Scotia pulls `[VERIFY]`).
- Respect hard gates: RBC 1/90, MBNA 5/6 TU inquiries, Amex biz 90-day spacing.
- Model inquiry decay so "mortgage mode" (doc 04) can project score recovery.

## 6. Offer Hygiene & Tracking Discipline

`[ENGINE]` — this is Churney's bread and butter.

Community best practices that map 1:1 to app features:

1. Apply via referral/rebate links (GCR etc.) for stacked value → referral-thread
   integration later `[CONTENT]`
2. Log apply date, approval date, MSR deadline, AF date, bonus status → `user_cards`
   + application event log (spec 06 §3)
3. Sock-drawer discipline: meet MSR, then lock the card aside → low-utilization
   nudges `[CONTENT]`
4. Watch statement dates for bonus posting (co-brand points post at statement close)
   → expected-posting predictions `[ENGINE]`
5. Elevated-offer calendar: CIBC back-to-school/BF/RRSP-season windows; wait weeks
   for elevated offers rather than applying at base → offer-history table `[ENGINE]`
6. Exit strategy before earning: know target redemption + award windows before
   collecting points → goal-linked planning (rotation planner, spec 05) `[ENGINE]`

## 7. First-Card Recommendations (community consensus)

`[CONTENT]`

- **Amex Cobalt** — best ongoing earn ($750/mo MSR), transferable MR, beginner-friendly
- **Scotiabank Gold Amex** — FYF potential, no FX fees, strong dining/grocery
- **TD/CIBC Aeroplan Infinite** — classic WB targets (subject to Aeroplan tier rules)
- Later: Amex Platinum, premium co-brands

## Sources

- ChurningCanada wiki — Starter Guide, Spending Offers page index, RHT page index: https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/getting-started
- getchurn.app — RBC product-switch cycle: https://getchurn.app/blog/canadian-churning-rules-by-issuer
- Fimaster — PS shift in 2026: https://fimaster.com.br/ca/credit-card-churning-canada/
- WOWA — MSR methods + manufactured-spending warning: https://wowa.ca/credit-card-churning-canada
- Ratehub — tracking-spreadsheet discipline: https://www.ratehub.ca/blog/credit-card-churning/
