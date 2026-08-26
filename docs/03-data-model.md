# 03 — Data Model

> Postgres 15+ (Supabase) · Drizzle ORM · Money = integer minor units · All timestamps `timestamptz`

## 1. ERD (core)

```
users ──< devices                      issuers ──< cards ──< card_versions
              │                                     │        │
              └──< user_cards >─────────────────────┘        ├──< earn_rates >── categories
                        │                                   └──< offers
                        │                                        │
transactions ───────────┤                              programs ─┴─ (cards.program_id)
   │   │                                                  │
   │   └──< merchant_aliases? (via merchants)             ├──< program_excluded_categories >── categories
   │                                                      ├──< redemption_options
   └── merchants >── categories                           ├──< transfer_rates >── programs(to)
                                                          ├──< conversion_bonuses
rotation_plans ──< rotation_events >── offers             └──< program_valuations
churn_recommendations                                     fx_rates
churn_rules                                               audit_log / change_log / ingest_logs
```

## 2. Enums

```sql
CREATE TYPE user_role         AS ENUM ('user','editor','admin');
CREATE TYPE tx_source         AS ENUM ('ios_shortcut','manual','csv_import');
CREATE TYPE tx_status         AS ENUM ('draft','confirmed','ignored','merged');
CREATE TYPE card_network      AS ENUM ('amex','visa','mastercard');
CREATE TYPE reward_kind       AS ENUM ('points','cashback','bonus_dollars'); -- extends per program
CREATE TYPE offer_status      AS ENUM ('draft','in_review','published','retired');
CREATE TYPE bonus_status      AS ENUM ('rumored','confirmed','active','ending_soon','expired');
CREATE TYPE rotation_event_ty AS ENUM ('apply','product_switch','cancel','downgrade_no_fee','pause','convert_to_keeper');
CREATE TYPE event_state       AS ENUM ('planned','submitted','approved','rejected','completed');
CREATE TYPE bonus_lifecycle   AS ENUM ('pending','on_track','posted','forfeited','expired'); -- user_cards.bonus_status
CREATE TYPE card_role         AS ENUM ('auto','keeper','churner'); -- keeper = daily driver, never auto-exited
```

## 3. Identity & Devices

```sql
CREATE TABLE profiles (
  id            uuid PRIMARY KEY REFERENCES auth.users(id),
  display_name  text,
  role          user_role NOT NULL DEFAULT 'user',
  default_currency char(3) NOT NULL DEFAULT 'CAD',
  timezone      text NOT NULL DEFAULT 'America/Toronto',
  risk_tolerance text NOT NULL DEFAULT 'balanced' CHECK (risk_tolerance IN ('conservative','balanced','aggressive')),
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE devices (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  label        text NOT NULL,                 -- "Peter's iPhone"
  token_hash   bytea NOT NULL UNIQUE,         -- sha256; raw token shown once at creation
  scopes       text[] NOT NULL DEFAULT '{write:transactions}',
  last_used_at timestamptz,
  revoked_at   timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);
```

## 4. Curated Card Domain

```sql
CREATE TABLE issuers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text UNIQUE NOT NULL, name text NOT NULL,
  rules_note text
);

CREATE TABLE networks (
  id  card_network PRIMARY KEY,
  acceptance_notes text                       -- e.g., mastercard: "Costco Canada MC-only"
);

CREATE TABLE categories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text UNIQUE NOT NULL,                  -- 'grocery', 'dining', ...
  name text NOT NULL
);

CREATE TABLE programs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text UNIQUE NOT NULL,                  -- 'aeroplan', 'amex_mr', ...
  name text NOT NULL, issuer_id uuid REFERENCES issuers(id),
  reward_kind reward_kind NOT NULL,
  flexibility_score numeric CHECK (flexibility_score BETWEEN 0 AND 100)
);

-- Program-level earning exclusions (Spec 02 §3.4): categories that never earn
-- under this program regardless of card (e.g., government, utilities).
CREATE TABLE program_excluded_categories (
  program_id uuid NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  category_id uuid NOT NULL REFERENCES categories(id),
  source_url text, verified_at timestamptz,
  PRIMARY KEY (program_id, category_id)
);

CREATE TABLE cards (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text UNIQUE NOT NULL,                  -- 'amex-gold-personal'
  issuer_id uuid NOT NULL REFERENCES issuers(id),
  program_id uuid NOT NULL REFERENCES programs(id),
  network_id card_network NOT NULL,
  name text NOT NULL, status text NOT NULL DEFAULT 'live',  -- live|retired
  image_url text
);

-- Effective-dated terms: fee, income reqs, FX fee, interest
CREATE TABLE card_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
  valid_from date NOT NULL, valid_to date,    -- null = current
  annual_fee_minor integer NOT NULL,
  extra_card_fee_minor integer,
  fx_fee_pct numeric(4,2),                    -- typically 2.5 [VERIFY]
  income_req_personal integer, income_req_household integer,
  purchase_apr numeric(5,2), cash_apr numeric(5,2),
  source_url text NOT NULL, verified_at timestamptz NOT NULL,
  UNIQUE (card_id, valid_from)
);

-- Per-card earn structure
CREATE TABLE earn_rates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_version_id uuid NOT NULL REFERENCES card_versions(id) ON DELETE CASCADE,
  category_id uuid REFERENCES categories(id), -- null = base rate
  rate numeric(6,3) NOT NULL,                 -- multiplier (points) or pct/100 (cashback)
  kind reward_kind NOT NULL,
  cap_amount_minor integer,                   -- boosted-portion cap
  cap_period text CHECK (cap_period IN ('monthly','annual')),
  excluded bool NOT NULL DEFAULT false        -- category earns nothing
);

-- Time-boxed multipliers ("5x grocery Aug–Oct")
CREATE TABLE earn_promotions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid NOT NULL REFERENCES cards(id),
  category_id uuid NOT NULL REFERENCES categories(id),
  rate numeric(6,3) NOT NULL, stackable bool NOT NULL DEFAULT false,
  starts_on date NOT NULL, ends_on date,
  cap_amount_minor integer, cap_period text,
  source_url text, verified_at timestamptz
);

-- Welcome bonuses / public offers
CREATE TABLE offers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid NOT NULL REFERENCES cards(id),
  status offer_status NOT NULL DEFAULT 'draft',
  headline text NOT NULL,
  min_spend_minor integer, deadline_days integer, deadline_end_date date,
  reward_points bigint, reward_cashback_minor bigint,
  eligibility_notes text,                     -- "once per lifetime" echoes churn_rules
  first_year_free bool NOT NULL DEFAULT false,
  source_url text, verified_at timestamptz,
  published_at timestamptz, retired_at timestamptz
);
```

## 5. Program Intelligence (live dataset — Spec 04)

```sql
CREATE TABLE redemption_options (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  program_id uuid NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  kind text NOT NULL CHECK (kind IN ('fixed_travel','transfer_partner','statement_credit','gift_card','merchandise','experiences','pay_with_points')),
  cpp_min numeric(5,2), cpp_typical numeric(5,2), cpp_max numeric(5,2),
  example_redemption text, notes text,
  valid_from date NOT NULL DEFAULT CURRENT_DATE, valid_to date,
  source_url text, verified_at timestamptz
);

CREATE TABLE transfer_rates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  from_program_id uuid NOT NULL REFERENCES programs(id),
  to_program_id   uuid NOT NULL REFERENCES programs(id),
  ratio_num integer NOT NULL, ratio_den integer NOT NULL,   -- from:to
  min_transfer integer, annual_cap integer,
  valid_from date NOT NULL, valid_to date,
  source_url text, verified_at timestamptz,
  CHECK (from_program_id <> to_program_id),
  EXCLUDE USING gist (from_program_id WITH =, to_program_id WITH =, daterange(valid_from, valid_to) WITH &&)
);
CREATE INDEX ON transfer_rates (from_program_id) WHERE valid_to IS NULL;

CREATE TABLE conversion_bonuses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  transfer_rate_id uuid REFERENCES transfer_rates(id),
  from_program_id uuid NOT NULL REFERENCES programs(id),
  to_program_id   uuid NOT NULL REFERENCES programs(id),
  bonus_pct integer,                          -- additive form: +25% => 25
  bonus_ratio_num integer, bonus_ratio_den integer,  -- multiplicative form: transfer ratio boosted to num:den
                                              -- exactly one of the two forms required (CHECKs below)
  status bonus_status NOT NULL DEFAULT 'rumored',
  starts_on date, ends_on date NOT NULL,
  constraints_text text,
  source_url text, verified_at timestamptz,
  CHECK ((bonus_pct IS NOT NULL) <> (bonus_ratio_num IS NOT NULL)),
  CHECK ((bonus_ratio_num IS NOT NULL) = (bonus_ratio_den IS NOT NULL))
);
CREATE INDEX ON conversion_bonuses (status, ends_on);

CREATE TABLE program_valuations (             -- admin-curated cpp baselines
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  program_id uuid NOT NULL REFERENCES programs(id),
  context text NOT NULL,                      -- 'economy','business','hotels','cash_floor'
                                              -- cashback programs: single row, context='cash_floor', baseline_cpp=1.00 (Spec 02 §3.5)
  baseline_cpp numeric(5,2) NOT NULL,
  rationale text,
  valid_from date NOT NULL DEFAULT CURRENT_DATE, valid_to date
);

CREATE TABLE change_log (                     -- public-facing data changelog
  id bigserial PRIMARY KEY,
  entity text NOT NULL, entity_id uuid NOT NULL,
  diff jsonb NOT NULL, reason text,
  actor uuid REFERENCES profiles(id), created_at timestamptz NOT NULL DEFAULT now()
);
```

## 6. Merchants

```sql
CREATE TABLE merchants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  norm_name text NOT NULL,
  display_name text NOT NULL,
  brand_family text,                          -- 'loblaws'
  default_category_id uuid REFERENCES categories(id),
  accepted_networks card_network[] NOT NULL DEFAULT '{amex,visa,mastercard}',
  confidence_global numeric(3,2)
);
CREATE INDEX merchants_trgm ON merchants USING gist (norm_name gin_trgm_ops);

CREATE TABLE merchant_aliases (
  id bigserial PRIMARY KEY,
  merchant_id uuid REFERENCES merchants(id) ON DELETE CASCADE,
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,   -- null = global alias
  alias_norm text NOT NULL,
  UNIQUE (user_id, alias_norm)
);

CREATE TABLE pending_merchants (              -- unmatched ingest strings for ops review
  norm text PRIMARY KEY, occurrences int NOT NULL DEFAULT 1,
  last_seen_at timestamptz, llm_category_guess uuid REFERENCES categories(id)
);
```

## 7. Transactions & Rewards

```sql
CREATE TABLE transactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  user_card_id uuid REFERENCES user_cards(id),
  source tx_source NOT NULL,
  status tx_status NOT NULL DEFAULT 'draft',
  occurred_at timestamptz NOT NULL,
  merchant_raw text, merchant_id uuid REFERENCES merchants(id),
  category_override uuid REFERENCES categories(id),
  amount_minor integer NOT NULL, currency char(3) NOT NULL DEFAULT 'CAD',
  fx_rate numeric(12,8), fx_source text, fx_rate_date date,
  cad_amount_minor integer GENERATED ALWAYS AS
    (CASE WHEN currency='CAD' THEN amount_minor
          ELSE round(amount_minor * fx_rate) END) STORED,
  dedupe_key text,
  idempotency_key text,                       -- shortcut payloads
  engine_version int NOT NULL DEFAULT 0,
  earned_points bigint, earned_cashback_minor bigint,
  value_cpp_snapshot numeric(5,2),
  breakdown jsonb,                            -- explainability trace
  best_wallet_alternative jsonb,              -- {user_card_id, would_earn_value}
  confidence numeric(3,2),
  imported_batch_id uuid,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX tx_idem ON transactions (user_id, idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE UNIQUE INDEX tx_dedupe ON transactions (user_id, dedupe_key) WHERE dedupe_key IS NOT NULL;
CREATE INDEX ON transactions (user_id, occurred_at DESC);
CREATE INDEX ON transactions (status) WHERE status = 'draft';

CREATE TABLE ingest_logs (                    -- raw payload retention for replay/debug (30d TTL)
  id bigserial PRIMARY KEY, device_id uuid REFERENCES devices(id),
  payload jsonb NOT NULL, result_code text, created_at timestamptz NOT NULL DEFAULT now()
);
```

## 8. Wallet & User History

```sql
CREATE TABLE user_cards (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  card_id uuid NOT NULL REFERENCES cards(id),
  nickname text,
  match_hint text UNIQUE,                     -- shortcut card_ref mapping
  opened_on date, closed_on date,
  role card_role NOT NULL DEFAULT 'auto',     -- 'keeper' = user-pinned daily driver (planner never schedules exit);
                                              -- 'churner' = user flags as rotation-only; 'auto' = optimizer decides
  bonus_status bonus_lifecycle NOT NULL DEFAULT 'pending',  -- welcome-bonus lifecycle (distinct from event_state)
  notes text
);

CREATE TABLE applications_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  card_id uuid NOT NULL REFERENCES cards(id), offer_id uuid REFERENCES offers(id),
  state event_state NOT NULL DEFAULT 'submitted',
  applied_on date NOT NULL, decided_on date,
  bonus_posted_on date
);

CREATE TABLE category_overrides (
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  merchant_id uuid REFERENCES merchants(id) ON DELETE CASCADE,
  category_id uuid REFERENCES categories(id),
  PRIMARY KEY (user_id, merchant_id)
);
```

## 9. Rotation & Churn

```sql
CREATE TABLE rotation_plans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  horizon_months int NOT NULL DEFAULT 24,
  daily_wallet jsonb,                         -- Spec 05 §4.4: {category_slug | 'base' → {user_card_id, monthly_value_minor}}
                                              -- stable daily-driver assignment; keeper cards never appear in rotation_events exits
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE rotation_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id uuid NOT NULL REFERENCES rotation_plans(id) ON DELETE CASCADE,
  seq int NOT NULL,
  event_type rotation_event_ty NOT NULL,
  state event_state NOT NULL DEFAULT 'planned',
  card_id uuid REFERENCES cards(id), offer_id uuid REFERENCES offers(id),
  target_date date,
  min_spend_progress_minor bigint DEFAULT 0,
  explanation jsonb                           -- optimizer trace snapshot
);

CREATE TABLE churn_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  issuer_id uuid REFERENCES issuers(id), card_id uuid REFERENCES cards(id),
  program_id uuid REFERENCES programs(id),    -- set for program-level rules (Aeroplan)
  rule_type text NOT NULL CHECK (rule_type IN (
    'lifetime_lockout',   -- bonus burned forever after earning (per product)
    'program_lockout',    -- loyalty-program-level cap, e.g. Aeroplan one-bonus-per-tier-lifetime
    'cycle_window',       -- reapply cooldown before next bonus
    'concurrent_limit',   -- velocity: max cards/apps per window
    'inquiry_limit',      -- hard inquiry-count gate at a bureau (MBNA 5/6)
    'pull_policy',        -- which bureau is pulled; sensitivity notes
    'switch_vs_new')),    -- whether a product switch earns a WB
  params jsonb NOT NULL,                      -- {"months":12} etc.
  confidence text CHECK (confidence IN ('verified','community','heuristic')),
  source_url text, verified_at timestamptz,
  active bool NOT NULL DEFAULT true
);

CREATE TABLE churn_recommendations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  generated_at timestamptz NOT NULL DEFAULT now(),
  items jsonb NOT NULL                        -- Spec 06 §6 shape, full ranked list
);
```

## 10. FX & System

```sql
CREATE TABLE fx_rates (
  rate_date date NOT NULL,
  pair text NOT NULL,                         -- 'USD/CAD'
  rate numeric(12,8) NOT NULL,
  source text NOT NULL,                       -- boc_valet | exchangerate_host | manual
  fetched_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (rate_date, pair)
);
```

RLS (Supabase): enable on all user-owned tables (`profiles`, `devices`, `user_cards`, `transactions`, `applications_log`, `category_overrides`, `rotation_*`, `churn_recommendations`) with `USING (auth.uid() = user_id)`; curated tables read-only to `anon`/`authenticated` via grants, writes restricted to admin/editor roles in service-layer + policies.

Views:

```sql
CREATE VIEW monthly_spend_by_category AS
SELECT t.user_id, date_trunc('month', t.occurred_at) m,
       COALESCE(t.category_override, m.default_category_id) cat,  -- NULL cat = unmatched merchant
       SUM(cad_amount_minor) spend
FROM transactions t
LEFT JOIN merchants m ON m.id = t.merchant_id   -- LEFT JOIN: keep txns with no resolved merchant
WHERE status='confirmed' GROUP BY 1,2,3;

-- user_card × category → currently-applicable rate (Spec 05 daily-wallet math input).
-- Resolution mirrors Spec 02 §3.4: active promotion > category rate > base rate,
-- against the current card_version. Cap ledgers apply downstream at solve time.
CREATE VIEW wallet_effective_rates AS
SELECT uc.id AS user_card_id,
       c.id AS category_id,
       COALESCE(ep.rate, er_cat.rate, er_base.rate) AS effective_rate,
       COALESCE(ep.kind, er_cat.kind, er_base.kind) AS kind,
       CURRENT_DATE AS as_of
FROM user_cards uc
JOIN cards cd ON cd.id = uc.card_id AND cd.status = 'live'
CROSS JOIN categories c
LEFT JOIN LATERAL (
  SELECT rate, kind FROM earn_promotions p
  WHERE p.card_id = cd.id AND p.category_id = c.id
    AND p.starts_on <= CURRENT_DATE AND (p.ends_on IS NULL OR p.ends_on >= CURRENT_DATE)
  ORDER BY p.rate DESC LIMIT 1
) ep ON true
LEFT JOIN LATERAL (
  SELECT er.rate, er.kind FROM earn_rates er
  JOIN card_versions cv ON cv.id = er.card_version_id
  WHERE cv.card_id = cd.id AND cv.valid_to IS NULL AND er.category_id = c.id
    AND er.excluded = false
) er_cat ON true
LEFT JOIN LATERAL (
  SELECT er.rate, er.kind FROM earn_rates er
  JOIN card_versions cv ON cv.id = er.card_version_id
  WHERE cv.card_id = cd.id AND cv.valid_to IS NULL AND er.category_id IS NULL
) er_base ON true;
```

## 11. Seeding Checklist

1. Categories taxonomy v1 → 2. Issuers/networks → 3. Programs → 4. ~25 launch cards × versions/rates/offers `[VERIFY]` each → 5. Transfer matrix + valuations → 6. Top-200 merchants + aliases → 7. BoC FX backfill 24mo.

Churn rules seed: [`db/seeds/churn_rules.sql`](../db/seeds/churn_rules.sql) (requires issuers + `aeroplan` program seeded first; sourced from [research/02-issuer-rules-canada.md](./research/02-issuer-rules-canada.md) §4).
