# Spec 01 — Spend Tracking

> Status: draft · Phase 1 · **Highest-priority spec** — capture quality gates everything downstream
> Depends on: architecture ingest API, FX service, data model (`transactions`, `devices`, `fx_rates`)

## 1. Summary

Capture credit card spend at the moment it happens using the **iOS Shortcuts Transaction trigger** (fires on Apple Wallet card taps; exposes card, merchant, amount as shortcut input), backed by manual quick-add and CSV import for non-Apple-Pay spend. Foreign-currency transactions convert to CAD at market rate effective at transaction time.

**Coverage reality:** Apple Wallet taps only. Online purchases, physical-card swipes, and bill payments are NOT captured by iOS — manual/CSV paths are first-class features, and an "uncaptured spend" estimator quantifies gaps.

## 2. Capture Sources

Priority order: `ios_shortcut` > `manual` > `csv_import`. All converge on `transactions` with `source` + `status`.

### 2.1 iOS Shortcut capture (primary)

**Trigger:** Shortcuts → Automation → Transaction ("When I tap" any/all Wallet cards) → Run Immediately.

**Payload contract — `POST /api/v1/ingest/transactions`:**

```jsonc
{
  "idempotency_key": "uuid-v4-generated-per-run",   // required
  "device_token": "churney_dtk_...",                // Bearer auth instead; token also in body fallback
  "card_ref": {                                     // which card was tapped
    "match_hint": "amex_gold",                      // user-assigned label per card in shortcut config
  },
  "merchant": "TIM HORTONS #4421",                  // from transaction input; may be null/empty on some taps
  "amount_minor": 485,
  "currency": "CAD",
  "occurred_at": "2026-08-22T14:31:02Z",            // automation run time ≈ tap time
  "client_meta": {
    "shortcut_version": "1.0.0",
    "locale": "en_CA"
  }
}
```

Shortcut template behavior (we distribute a `.plist`/iCloud link template):
- Generates UUID idempotency key per run
- Maps each of the user's cards to a `match_hint` chosen during setup wizard
- Handles empty merchant (sends `null`; server flags for review)
- Retries once on network failure; queues nothing offline (documented limitation: offline taps are lost → mitigated by weekly reconciliation nudge)

**Server processing:**
1. Auth via device token (`devices` table, scoped `write:transactions`, revocable in settings)
2. Idempotency check (unique index) — duplicate returns original 200
3. Resolve `card_ref.match_hint` → user's `user_card`
4. Create transaction `status=draft` unless auto-confirm eligible (§4)
5. Async handoff to reward engine

**Reliability notes (known Apple issues):**
- Trigger can time out when Wallet receives delayed transaction data (FB16379100): mitigation = daily digest email listing expected-but-unseen activity based on user's typical patterns + easy manual add.
- Automation runs require "Run Immediately" enabled; setup wizard enforces/checks this with screenshots.
- Amount sign: Wallet reports positive amounts; refunds appear as separate negative-capable entries if issuer pushes them — normalize sign conventions server-side.

### 2.2 Manual quick-add
- `/spend` inline composer: amount, card picker (recent-first), merchant autocomplete (user's history first, then global merchants), date/time defaults now, currency selector with live rate preview.
- Target: ≤3 taps for repeat merchant (smart default = last used card+merchant combo).
- Mobile PWA optimized; share-sheet target later.

### 2.3 CSV import
- Per-issuer column mapping presets (Amex CA, TD, RBC, CIBC, Scotiabank, BMO `[VERIFY]` headers per export format); generic mapper UI otherwise.
- Pipeline: upload → parse → column map → row preview → dedupe vs existing txns (§5) → import as `source=csv_import, status=confirmed`.
- Imports can backfill months; cap 10k rows/file v1.

## 3. Multi-Currency Handling

Wallet reports amount in the **charged currency** (e.g., USD purchase on CAD card shows USD).

On ingest:
1. If `currency == user.default_currency (CAD)` → store as-is.
2. Else fetch market rate **for that date** (see §6) → store:

```
amount_minor        = original amount in original currency
currency            = original currency
fx_rate             = market mid-rate → CAD (decimal, e.g. 1.3702)
fx_source           = boc_valet | exchangerate_host | openexchangerates | manual
fx_rate_date        = rate's observation date
cad_amount_minor    = round(amount × fx_rate)
```

Display rules:
- Primary display: CAD equivalent.
- Detail view shows original + rate line: "US$35.00 × 1.3702 (BoC, 2026-08-21) = C$47.96".
- **Issuer FX fee is modeled separately**: cards carry `fx_fee_pct` (typically 2.5% `[VERIFY]`); actual cost shown as `cad_amount × (1 + fx_fee)` in cost contexts (compare/reward math uses base conversion to keep rewards consistent with issuer statement amounts).
- Weekend/holiday: use last published BoC rate (observation date displayed honestly).

## 4. Draft Review & Auto-Confirmation

| Condition | Status |
|---|---|
| Merchant matched ≥0.9 confidence AND no duplicate suspicion AND card known | `confirmed` (auto) |
| Everything else (unknown merchant, missing merchant, low confidence, new device) | `draft` |

Draft queue UX:
- Swipe actions: Confirm ✓ / Edit / Ignore ✕
- Bulk: confirm-all-from-known-brand
- Drafts excluded from stats/min-spend until confirmed; banner shows pending count
- Auto-expire drafts after 30d → `ignored` (with warning notification at 25d)

## 5. Deduplication

Threat model: shortcut double-fire, manual re-add of auto-captured txn, overlapping CSV imports.

Rules (checked in order):
1. `idempotency_key` exact hit → no-op
2. Same `(user, card, cad_amount ± [0..2] cents or same raw amount+currency, occurred_at within 90s)` → mark suspected-duplicate → draft with merge suggestion
3. Cross-source: CSV row matching existing `ios_shortcut`/`manual` confirmed txn (same date ±1d, same amount) → skip by default (report skipped count), user override available
4. Fuzzy window configurable per user in settings

## 6. FX Rate Service

| Aspect | Decision |
|---|---|
| Primary source | Bank of Canada Valet API (free, official noon rates, ~100+ currencies vs CAD) |
| Backup | exchangerate.host or OpenExchangeRates (paid tier) |
| Sync | Daily job stores all needed pairs into `fx_rates` (date, base=CAD, pair, rate, source); on-demand fetch for missing historical dates |
| Staleness policy | If today's rate unpublished (weekend/holiday), walk back to latest observation; record its date |
| Manual override | User may edit rate on a specific transaction (audit-trailed) |

## 7. Uncaptured Spend Estimation

Goal: honest coverage metric, drives manual-entry habit without nagging.

- Baseline monthly spend per category estimated from CSV imports + confirmed captures.
- Coverage % = captured volume ÷ baseline volume per calendar month.
- Dashboard widget: "You captured ~68% of usual spend in July" + top gap categories (e.g., recurring bills never captured → suggest CSV import or exclusions list where user declares categories they don't want tracked).
- Exclusions list suppresses nagging for deliberately untracked flows.

## 8. Privacy & Security

- We never see PANs — Apple exposes card *identity* only via user-configured hints; no card numbers in payload.
- Transport: HTTPS + bearer token; tokens rotatable; per-device last-used-at tracking shown in settings.
- Merchant/location strings are PII-lite: stored per-user, aggregated anonymously (k-anonymity ≥ 50) before promoting aliases globally.

## 9. Telemetry (own-product)

Funnel events: shortcut_installed → first_payload → first_confirm; capture failure reasons; retry counts. Alerting on ingest error-rate spikes (new iOS release regressions).

## 10. Acceptance Criteria

1. End-to-end fixture: simulated payloads across 5 currencies incl. weekend date → correct CAD conversions with correct observation dates.
2. Idempotent replay of identical payloads produces exactly one transaction.
3. Dedupe fixtures: double-fire, manual re-add, overlapping CSV — each handled per §5.
4. Shortcut template installs on current iOS via deep link in <2 min following in-app guide (tested on device, documented screenshots).
5. Draft queue bulk ops + auto-expire behave per §4.
6. Load: 50 rps sustained ingest p95 < 150ms ack (enrichment async).
