-- churn_rules seed — Canadian issuer/program welcome-bonus eligibility rules
-- Source: docs/research/02-issuer-rules-canada.md §4 (compiled 2026-08-22)
--
-- Prerequisites: issuers seeded with slugs below; programs seeded with 'aeroplan'.
-- All rows are [VERIFY]-gated: confidence 'community'/'heuristic' rows must be
-- re-verified against issuer T&Cs before gating user-facing decisions (Spec 06 §8:
-- stale rules >90d degrade to advisory-only).
-- Idempotent: every row carries params->'seed' = 'churn_rules_v1'; the DELETE
-- guard below removes prior v1 rows before inserting.

BEGIN;

DELETE FROM churn_rules WHERE params @> '{"seed": "churn_rules_v1"}';

INSERT INTO churn_rules (issuer_id, card_id, program_id, rule_type, params, confidence, source_url, verified_at)
VALUES
-- ── American Express Canada ────────────────────────────────────────────────
-- WB once per lifetime per product ("have or have had this Card")
((SELECT id FROM issuers WHERE slug = 'amex_ca'),
 NULL, NULL, 'lifetime_lockout',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'scope', 'per_product',
   'note', 'Per product, not per family: holding Gold does not block Platinum bonus',
   'possible_reset_after_years', 3,
   'reset_reliable', false),
 'verified',
 'https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/application-rules',
 now()),

-- Business Gold / Business Platinum: 90-day duplicate rejection
((SELECT id FROM issuers WHERE slug = 'amex_ca'),
 NULL, NULL, 'concurrent_limit',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'product_slugs', jsonb_build_array('amex-business-gold', 'amex-business-platinum'),
   'min_days_between_apps', 90,
   'behavior', 'auto_reject_duplicate'),
 'community',
 'https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/application-rules',
 now()),

-- Pop-up jail risk profile (advisory heuristic, not a hard gate)
((SELECT id FROM issuers WHERE slug = 'amex_ca'),
 NULL, NULL, 'concurrent_limit',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'kind', 'popup_jail_risk',
   'triggers', jsonb_build_array('rapid_open_close', 'low_organic_spend'),
   'recovery', 'months_of_organic_spend',
   'advisory_only', true),
 'heuristic',
 'https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/application-rules',
 now()),

-- ── RBC ────────────────────────────────────────────────────────────────────
-- 1/90 rule: one approved application per rolling 90 days, firmly enforced
((SELECT id FROM issuers WHERE slug = 'rbc'),
 NULL, NULL, 'cycle_window',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'months', 3,
   'trigger', 'last_approval',
   'scope', 'any_new_application',
   'enforcement', 'firm_auto_reject'),
 'community',
 'https://princeoftravel.com/guides/credit-card-rules-how-often-can-you-apply/',
 now()),

-- RBC product switches can trigger WB eligibility (ION -> Avion VI cycle)
((SELECT id FROM issuers WHERE slug = 'rbc'),
 NULL, NULL, 'switch_vs_new',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'switch_earns_bonus', true,
   'documented_cycle', jsonb_build_array('rbc-ion', 'rbc-avion-vi', 'rbc-ba-vi', 'rbc-westjet-we'),
   'cycle_repeat_months', 21),
 'heuristic',
 'https://getchurn.app/blog/canadian-churning-rules-by-issuer',
 now()),

-- ── TD ─────────────────────────────────────────────────────────────────────
-- Aeroplan Visa family: eligible if last application for same product >12mo ago
((SELECT id FROM issuers WHERE slug = 'td'),
 NULL, NULL, 'cycle_window',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'months', 12,
   'trigger', 'last_application',
   'scope', 'same_product',
   'family', 'aeroplan_visa',
   'ineligibility_effect', 'forfeits_first_purchase_bonus_portion_only'),
 'community',
 'https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/application-rules',
 now()),

-- First Class Travel family: eligible if last activation/closure >12mo ago
((SELECT id FROM issuers WHERE slug = 'td'),
 NULL, NULL, 'cycle_window',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'months', 12,
   'trigger', 'last_activation_or_closure',
   'scope', 'same_product',
   'family', 'first_class_travel'),
 'community',
 'https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/application-rules',
 now()),

-- ── Scotiabank ─────────────────────────────────────────────────────────────
-- No WB if existing Scotia consumer cardholder or held one in prior 24 months
((SELECT id FROM issuers WHERE slug = 'scotia'),
 NULL, NULL, 'cycle_window',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'months', 24,
   'trigger', 'held_or_current_cardholder',
   'scope', 'any_consumer_card',
   'enforcement', 'partial_system_may_not_block_csr_will_not_help'),
 'community',
 'https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/application-rules',
 now()),

-- ── BMO ────────────────────────────────────────────────────────────────────
-- Velocity sensitivity: declines reported after >2 BMO apps in 12 months
((SELECT id FROM issuers WHERE slug = 'bmo'),
 NULL, NULL, 'concurrent_limit',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'max_apps', 2,
   'window_months', 12,
   'enforcement', 'unpublished_decline_pattern'),
 'heuristic',
 'https://getchurn.app/blog/canadian-churning-rules-by-issuer',
 now()),

-- BMO pull policy: TransUnion most provinces; Equifax QC + some Atlantic
((SELECT id FROM issuers WHERE slug = 'bmo'),
 NULL, NULL, 'pull_policy',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'bureau_default', 'transunion',
   'bureau_exceptions', jsonb_build_array('qc', 'atlantic_provinces_partial'),
   'exception_bureau', 'equifax'),
 'heuristic',
 'https://getchurn.app/blog/canadian-churning-rules-by-issuer',
 now()),

-- ── MBNA ───────────────────────────────────────────────────────────────────
-- 5/6 rule: rejects at 5+ TransUnion inquiries in past 6 months (incl. current app)
((SELECT id FROM issuers WHERE slug = 'mbna'),
 NULL, NULL, 'inquiry_limit',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'bureau', 'transunion',
   'max_inquiries_allowed', 4,
   'window_months', 6,
   'counts_current_application', true,
   'counts_failed_applications', true,
   'existing_holder_bypass', 'split_credit_from_existing_mbna_card'),
 'community',
 'https://princeoftravel.com/guides/credit-card-rules-how-often-can-you-apply/',
 now()),

((SELECT id FROM issuers WHERE slug = 'mbna'),
 NULL, NULL, 'pull_policy',
 jsonb_build_object('seed', 'churn_rules_v1', 'bureau', 'transunion'),
 'community',
 'https://princeoftravel.com/guides/credit-card-rules-how-often-can-you-apply/',
 now()),

-- ── HSBC (legacy — RBC acquisition closed early 2024) ─────────────────────
-- No WB if held World Elite MC within prior 12mo; no WB via switching
-- NOTE: lineup winding down; row kept inactive for historical modeling.
((SELECT id FROM issuers WHERE slug = 'hsbc'),
 NULL, NULL, 'cycle_window',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'months', 12,
   'trigger', 'prior_holder',
   'scope', 'world_elite_mc',
   'no_bonus_via_switch', true),
 'community',
 'https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/application-rules',
 now()),

-- ── National Bank ──────────────────────────────────────────────────────────
-- No WB if any NBC cardholder in last 24 months (wiki-annotated: enforced)
((SELECT id FROM issuers WHERE slug = 'nbc'),
 NULL, NULL, 'cycle_window',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'months', 24,
   'trigger', 'prior_or_current_cardholder',
   'scope', 'any_nbc_card',
   'enforcement', 'enforced_per_community_wiki'),
 'community',
 'https://sites.google.com/view/churningcanadaexclusiveoffers/guides-and-rules/application-rules',
 now()),

-- ── Aeroplan program-level overlay ─────────────────────────────────────────
-- One New Card Bonus per card-tier lifetime, regardless of issuer (T&C Dec 2022).
-- Precedent: Oct 2024 clawbacks ~10k pts x ~17k members. Blocks same-tier co-brand
-- bonuses even where the issuer itself would grant one. See research doc 03.
(NULL,
 NULL,
 (SELECT id FROM programs WHERE slug = 'aeroplan'),
 'program_lockout',
 jsonb_build_object(
   'seed', 'churn_rules_v1',
   'tiers', jsonb_build_array('entry', 'core', 'premium', 'core_small_business', 'premium_small_business'),
   'bonuses_per_tier_lifetime', 1,
   'regardless_of_issuer', true,
   'clawback_risk', true,
   'precedent', 'oct_2024_clawbacks_10k_pts_x_17k_members',
   'holding_multiple_same_tier_may_violate_tnc', true),
 'verified',
 'https://blog.rewardscanada.ca/credit-cards/aeroplan-clawing-back-points/',
 now());

-- Deactivate the legacy HSBC row (RBC acquisition closed early 2024)
UPDATE churn_rules SET active = false
WHERE params @> '{"seed": "churn_rules_v1"}'
  AND issuer_id = (SELECT id FROM issuers WHERE slug = 'hsbc');

COMMIT;
