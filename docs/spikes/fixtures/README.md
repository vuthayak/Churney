# Phase 0.1 — Ingest payload fixtures

Synthetic payloads matching the contract in `docs/specs/01-spend-tracking.md` §2.1.
Use with the stub server for local testing:

```bash
curl -sS -X POST http://127.0.0.1:8787/api/v1/ingest/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer churney_dtk_spike_dev_only" \
  -d @docs/spikes/fixtures/cad-with-merchant.json
```

| File | Scenario |
|---|---|
| `cad-with-merchant.json` | Happy path: CAD tap with merchant |
| `empty-merchant.json` | `merchant: null` — should flag for draft review in Phase 1 |
| `fx-usd-amount.json` | Foreign currency (USD) charged amount |
| `fx-eur-amount.json` | Foreign currency (EUR) charged amount |
| `refund-negative-amount.json` | Refund / negative amount edge case |

Replace `idempotency_key` with a fresh UUID when replaying the same fixture.
