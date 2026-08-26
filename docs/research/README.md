# Churney — Research Knowledge Base

Domain research on Canadian credit card churning, rewards programs, and the competitive
landscape. This folder is the **source-of-truth reference** that feeds product specs,
the churn-engine rulebook (`docs/specs/06-churn-engine.md` §2), and program data
(`docs/specs/04-program-comparison.md`).

Compiled: 2026-08-22. Primary source: the r/churningcanada community wiki (accessed via
its official Google Sites mirror) plus corroborating industry sources.

## Document Map

| Doc | Purpose | Feeds into |
|---|---|---|
| [01-churning-fundamentals.md](./01-churning-fundamentals.md) | What churning is, bank economics, the churn cycle, earning hierarchy, reward taxonomy | Vision, product copy |
| [02-issuer-rules-canada.md](./02-issuer-rules-canada.md) | Per-issuer welcome-bonus eligibility & application rules | Spec 06 `churn_rules` seed |
| [03-programs-and-transfers.md](./03-programs-and-transfers.md) | Loyalty program rules (esp. Aeroplan), transferable currency matrices, award availability | Spec 04, Spec 06 |
| [04-risks-and-compliance.md](./04-risks-and-compliance.md) | Credit-score mechanics, clawbacks, blacklisting; Churney compliance guardrails | Spec 06 §8, principles |
| [05-tactics-playbook.md](./05-tactics-playbook.md) | Community tactics: product switching, MSR strategies, RHT, multiplayer | Spec 05/06 + content strategy |
| [06-competitive-analysis.md](./06-competitive-analysis.md) | TravelMaxx deep-dive and adjacent tools; Canada gap analysis | Vision positioning |

## Source-Quality Legend

Every factual claim in this KB carries a confidence tag:

| Tag | Meaning |
|---|---|
| `[OFFICIAL]` | From issuer T&Cs or loyalty program terms — citable to users |
| `[COMMUNITY]` | Widely-reproduced datapoints from r/churningcanada / RFD / blogs — reliable but unofficial, changes without notice |
| `[DATAPoint]` | Individual user report(s); directional only |
| `[VERIFY]` | Must be confirmed against issuer T&Cs before any user-facing use (per `docs/README.md` conventions). Rules that gate engine decisions default here |

## Key Sources

- r/churningcanada wiki mirror (Starter Guide, Application Rules, Calling Policy, US cards): https://sites.google.com/view/churningcanadaexclusiveoffers/
- Prince of Travel — "Credit Card Rules: How Often Can You Apply": https://princeoftravel.com/guides/credit-card-rules-how-often-can-you-apply/
- Rewards Canada — Aeroplan clawback reporting (Oct 2024): https://blog.rewardscanada.ca/credit-cards/aeroplan-clawing-back-points/
- Ratehub churning 101: https://www.ratehub.ca/blog/credit-card-churning/
- WOWA churning guide: https://wowa.ca/credit-card-churning-canada
- creditcardGenius churning analysis: https://creditcardgenius.ca/blog/credit-card-churning-canada
- PointsBinder beginner guide (2026): https://pointsbinder.com/blog/credit-card-churning-canada-beginners-guide
- Debt.ca churning overview: https://www.debt.ca/blog/credit-card-churning-should-you-do-it
- TravelMaxx: https://travelmaxx.app/

## Maintenance Notes

- Issuer rules and program terms change frequently and are enforced unevenly. Treat
  anything tagged `[COMMUNITY]` as a snapshot of community consensus at compile time.
- The ChurningCanada wiki's own Application Rules page is itself a curated summary with
  enforcement annotations ("enforced" / "partially enforced" / "YMMV") — those
  annotations are reproduced where available because they encode real enforcement
  behavior, not just written policy.
