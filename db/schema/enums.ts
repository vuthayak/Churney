import { pgEnum } from "drizzle-orm/pg-core";

export const userRoleEnum = pgEnum("user_role", ["user", "editor", "admin"]);

export const txSourceEnum = pgEnum("tx_source", [
  "ios_shortcut",
  "manual",
  "csv_import",
]);

export const txStatusEnum = pgEnum("tx_status", [
  "draft",
  "confirmed",
  "ignored",
  "merged",
]);

export const cardNetworkEnum = pgEnum("card_network", [
  "amex",
  "visa",
  "mastercard",
]);

export const rewardKindEnum = pgEnum("reward_kind", [
  "points",
  "cashback",
  "bonus_dollars",
]);

export const offerStatusEnum = pgEnum("offer_status", [
  "draft",
  "in_review",
  "published",
  "retired",
]);

export const bonusStatusEnum = pgEnum("bonus_status", [
  "rumored",
  "confirmed",
  "active",
  "ending_soon",
  "expired",
]);

export const rotationEventTypeEnum = pgEnum("rotation_event_ty", [
  "apply",
  "product_switch",
  "cancel",
  "downgrade_no_fee",
  "pause",
  "convert_to_keeper",
]);

export const eventStateEnum = pgEnum("event_state", [
  "planned",
  "submitted",
  "approved",
  "rejected",
  "completed",
]);

export const bonusLifecycleEnum = pgEnum("bonus_lifecycle", [
  "pending",
  "on_track",
  "posted",
  "forfeited",
  "expired",
]);

export const cardRoleEnum = pgEnum("card_role", ["auto", "keeper", "churner"]);

export const capPeriodEnum = pgEnum("cap_period", ["monthly", "annual"]);

export const riskToleranceEnum = pgEnum("risk_tolerance", [
  "conservative",
  "balanced",
  "aggressive",
]);

export const churnConfidenceEnum = pgEnum("churn_confidence", [
  "verified",
  "community",
  "heuristic",
]);

export const churnRuleTypeEnum = pgEnum("churn_rule_type", [
  "lifetime_lockout",
  "program_lockout",
  "cycle_window",
  "concurrent_limit",
  "inquiry_limit",
  "pull_policy",
  "switch_vs_new",
]);

export const redemptionKindEnum = pgEnum("redemption_kind", [
  "fixed_travel",
  "transfer_partner",
  "statement_credit",
  "gift_card",
  "merchandise",
  "experiences",
  "pay_with_points",
]);
