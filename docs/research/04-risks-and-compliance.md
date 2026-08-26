# 04 — Risks & Compliance

> Feeds Spec 06 §8 (Compliance & Trust) and product principles. Also defines what
> Churney will *not* surface. Confidence legend: see [README](./README.md).
> Compiled 2026-08-22.

## 1. Credit Score Mechanics (Canada)

Canadian scores (Equifax/TransUnion, 300–900) decompose as `[COMMUNITY — consistent
across sources]`:

| Factor | Weight | Churning effect |
|---|---|---|
| Payment history | 35% | Neutral/positive if always paid in full |
| Utilization ratio | 30% | Often *improves* — new accounts raise total credit lines |
| Length of history | 15% | Degrades with new accounts; closing oldest cards hurts most; closing a 12-month-old card is negligible if total credit stays high |
| Credit mix / type | 10% | Minor churn effect |
| Hard inquiries | 10% | −5–10 pts each, temporary; fall off after ~2–3 years (2 yrs per some sources, 3 per others `[VERIFY]`) |

Community-reported outcome: disciplined churners maintain **720–780+**. `[COMMUNITY]`

## 2. Financial Risks

`[COMMUNITY]`

1. **Interest destroys returns.** Carrying a balance at ~20% APR erases any bonus.
   The r/churningcanada starter guide literally tells indebted readers to stop
   reading and pay off balances first. Churney should detect revolving-balance
   signals and suppress churning recommendations for those users.
2. **MSR failure.** Miss the threshold by even $1 → bonus forfeited, fee still owed;
   on Amex products the lifetime lockout burns the product permanently ("no second
   chance" per wiki).
3. **Fee leakage.** Forgetting cancellation timing → year-2 AF posts ($120–$799).
   This is a core Churney alert (principle: "never lose a bonus").
4. **Forfeited rewards at closure.** Some currencies void unredeemed points when a
   card closes — engine must check redemption-before-cancellation.
5. **Overspend temptation.** MSRs can induce spending users wouldn't otherwise do.

## 3. Institutional Risks

`[COMMUNITY]`

- **Blacklisting:** issuers decline future applications from visible churners
  (velocity patterns, zero revolving balance + many inquiries is an ML-flaggable
  profile per 2026-era reporting).
- **Account closures & clawbacks:** Amex's "RAT"-style abuse review (US analog);
  Aeroplan's Oct 2024 retroactive clawbacks (~17K members, see doc 03) prove
  loyalty programs will reach back into your balance.
- **"Amexiled":** banned from future Amex bonuses/approvals after aggressive open/
  close behavior; pop-up jail as the softer precursor.
- **Mortgage risk:** lenders scrutinize recent credit-seeking; community guidance is
  to stop churning ~12 months before a mortgage application. Churney should offer a
  "mortgage mode" that freezes recommendations and models inquiry decay.
- **Program-side enforcement is growing:** once-per-lifetime clauses, AI-driven
  approval screening, and program-level (not just issuer-level) clawbacks define the
  post-"golden age" environment. The era of flipping the same card every 6 months is
  over; precision and eligibility-tracking is the game now — which is precisely
  Churney's value proposition.

## 4. The "Never Call the Bank" Norm — and what it means for Churney

r/churningcanada maintains an explicit **Calling Policy**: `[COMMUNITY]`

> Do NOT call the financial institution about missing bonuses you were ineligible
> for. Enforcement of WB T&Cs is partial and inconsistent; calling surfaces edge
> cases, triggering crackdowns, policy tightening, retroactive clawbacks, or
> blacklisting — harming the entire hobby ("domino effect").

Product implications:

- Churney copy must never coach users to dispute ineligibility with banks.
- Eligibility warnings must be framed as *"you may not receive the bonus"* pre-apply,
  never *"call to ask why."*
- This norm also explains why community-sourced rule data (doc 02) is the best
  available signal: nobody pressure-tests rules by asking banks.

## 5. Compliance Guardrails for Churney

Extends `00-vision.md` principles #5 and Spec 06 §8:

| Topic | Position |
|---|---|
| Advice framing | Educational information only; disclaimers on every recommendation surface; not financial advice `[OFFICIAL — our policy]` |
| Manufactured spending | **Never recommended, never discussed in-app content.** Banned from r/churningcanada discussion entirely (tragedy-of-commons); issuers treat it as account-closure territory `[COMMUNITY]` |
| Legitimate MSR acceleration | OK to surface generically: gift cards, bill-pay services (Plastiq/Paysimply/Chexy), prepaid insurance/taxes — informational, compliance-reviewed copy `[COMMUNITY]` |
| Referral economics | Future affiliate links clearly labeled, visually distinct, excluded from default ranking sort (no dark patterns) |
| Multiplayer/spouse strategies | Present as household-planning education; P3 persona explicitly out of v1 |
| Rule data integrity | Every gating rule row carries `source_url`, `last_verified_at`, `confidence`; stale (>90d) rules degrade to advisory-only |
| US-card content | Out of scope v1 (vision non-goal); document exists in KB for later phases |

## Sources

- ChurningCanada wiki — Calling Policy reference + Application Rules annotations: https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/application-rules
- ChurningCanada wiki — Starter Guide FAQ: https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/getting-started
- WOWA — crackdowns/amexiled/manufactured-spending warnings: https://wowa.ca/credit-card-churning-canada
- creditcardGenius — risks and issuer bans: https://creditcardgenius.ca/blog/credit-card-churning-canada
- Debt.ca — suitability analysis: https://www.debt.ca/blog/credit-card-churning-should-you-do-it
- Fimaster — 2026 anti-gaming environment (AI approvals, once-per-lifetime spread): https://fimaster.com.br/ca/credit-card-churning-canada/
- PointsBinder — credit score impact detail: https://pointsbinder.com/blog/credit-card-churning-canada-beginners-guide
