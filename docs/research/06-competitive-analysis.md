# 06 — Competitive Analysis

> Churney is positioned as the **Canadian, better version of travelmaxx.app**.
> This doc analyzes TravelMaxx and adjacent tools; feeds `00-vision.md` positioning
> and roadmap decisions. Compiled 2026-08-22.

## 1. TravelMaxx (primary benchmark)

**What it is:** "the agent for credit card maxxing" — an agent-first subscription
platform for US points enthusiasts. ~$1.7K MRR as of mid-2026 per TrustMRR.

### Feature inventory

| Feature | Detail | Churney relevance |
|---|---|---|
| **Award flight search** | Searches 28 airline programs incl. Aeroplan via CLI (Python/PyPI) + MCP server; results include points price, surcharges, stops, equipment, availability, a "roame_score"; proxies Roame credentials server-side | Adopt concept: award-search is the redemption-side killer feature. Canada-first version would start with Aeroplan + Avios + Flying Blue depth |
| **Alerts** | Route alerts (`SFO NRT BUSINESS ≤75K`), discovery feed | Directly adopt — alert UX for award availability |
| **AI consultant ("Scammeroo")** | Chat agent for niche situations, churning/manufactured-spend education | Adopt pattern with our compliance guardrails: educational agent, no MS advice, no manufactured-spend coaching |
| **Status matches/fast-tracks** | Automatic status-match discovery between programs | Lower priority for Canadians (fewer elite-status levers); revisit post-v1 |
| **Points marketplace** | Trade points across programs via browser agents (e.g., UR → AA miles) | **Skip** — T&C-violating gray market; conflicts with Churney trust positioning |
| **CLI + MCP interfaces** | Full API surface exposed as CLI and MCP tools | Strongly adopt direction: MCP makes the product programmable and AI-agent-native |
| **Community/forum + posts** | Forum, news posts, subscriptions | Later phase |

### Where Churney beats it (Canada-specific)

1. **Canadian program depth** — TravelMaxx is US-centric; no issuer-rule modeling,
   no Scene+/TD Rewards/Aventura/BMO Rewards, no Canadian WB tracking.
2. **Spend capture** — TravelMaxx has no transaction layer at all; Churney's iOS
   Wallet capture (spec 01) enables MSR-progress tracking that TravelMaxx can't do.
3. **Churn engine** — no equivalent of spec 06's eligibility/cycle-window/timing
   engine exists anywhere in the US tooling either.
4. **Compliance posture** — TravelMaxx leans into gray-area ("Scammeroo",
   marketplace); Churney's trust/education positioning is deliberately cleaner and
   affiliate-compatible long-term.

### What to copy

- Agent-first UX (chat + proactive agents), MCP/CLI surfaces, alert model,
  subscription pricing shape.

## 2. Adjacent Competitors

| Tool | Model | Strengths | Gaps Churney exploits |
|---|---|---|---|
| **MaxRewards** (US) | Card management app; bank-linked; 900+ card structured DB; card-linked offers; browser ext | Deepest all-in-one US wallet manager | US-only; no churn engine; requires bank credentials (Churney vision excludes open banking v1) |
| **MaxWorth** (US) | Benefit tracker + 6 specialized AI agents (spending optimizer, travel planner, retention expert, etc.) | Agent taxonomy worth studying; benefit-expiry alerts; portfolio dashboard | US-only; no spend capture; no Canadian issuers/programs |
| **Thrifty Traveler Card Tracker** (US) | Manual perk check-off tracker, 100+ cards, family support | Zero-credential privacy model (no card numbers/logins) — validates Churney's Shortcut-capture approach over bank linking | Manual; no rewards math; US-only |
| **AwardWallet** | Loyalty balance tracking, 40+ programs | Program coverage breadth | No spend capture, weak Canada, no churning logic |
| **CardPointers** | Offer/credit alerts | Alert cadence discipline | Amex-offer-centric, US-first |
| **Ratehub / creditcardGenius / GreedyRates** (CA) | Affiliate comparison sites | Canadian card data, SEO reach | Static marketing sites; zero personalization against real spend; no tracking; stale program data |
| **r/churningcanada spreadsheets** | Community templates | Free, community-trusted | Manual; no automation/freshness |

## 3. Strategic Takeaways

1. **The wedge is unchanged by TravelMaxx:** nobody (US or CA) combines spend capture
   + reward math + Canadian churn eligibility. TravelMaxx validates demand for the
   "maxxing agent" category but doesn't occupy the tracking/trust layer.
2. **MCP/CLI should be on the roadmap** (post-iOS traction): exposes Churney's rule
   engine and program DB to power users and third-party agents — cheap distribution
   among exactly the P1 persona.
3. **Agent taxonomy borrow:** MaxWorth's six-agent split (spend optimizer / travel
   planner / retention / transfer bonuses) maps cleanly onto Churney's specs 02–06;
   consider naming future features along those lines.
4. **Do not follow TravelMaxx into** points marketplaces or manufactured-spend
   cheerleading — trust and compliance are structural advantages against both
   incumbents (affiliate bias) and upstarts (gray-market risk).
5. **Award search later:** when Churney adds redemption-side tooling, partner-or-build
   decision needed (Roame-style aggregator vs. first-party Aeroplan search).

## Sources

- TravelMaxx homepage/features/CLI docs: https://travelmaxx.app/, https://pypi.org/project/travelmaxx/
- TrustMRR revenue datapoint: https://trustmrr.com/startup/travelmaxx
- MaxRewards: https://maxrewards.com/
- MaxWorth: https://maxworth.app/app/
- Thrifty Traveler Card Tracker: https://cardtracker.thriftytraveler.com/
