import { sql } from "drizzle-orm";
import {
  boolean,
  date,
  integer,
  jsonb,
  pgTable,
  text,
  timestamp,
  uuid,
} from "drizzle-orm/pg-core";
import {
  churnConfidenceEnum,
  churnRuleTypeEnum,
  eventStateEnum,
  rotationEventTypeEnum,
} from "./enums";
import { cards, offers } from "./curated";
import { issuers, programs } from "./curated";
import { profiles } from "./identity";

export const rotationPlans = pgTable("rotation_plans", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  userId: uuid("user_id")
    .notNull()
    .references(() => profiles.id, { onDelete: "cascade" }),
  horizonMonths: integer("horizon_months").notNull().default(24),
  dailyWallet: jsonb("daily_wallet"),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const rotationEvents = pgTable("rotation_events", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  planId: uuid("plan_id")
    .notNull()
    .references(() => rotationPlans.id, { onDelete: "cascade" }),
  seq: integer("seq").notNull(),
  eventType: rotationEventTypeEnum("event_type").notNull(),
  state: eventStateEnum("state").notNull().default("planned"),
  cardId: uuid("card_id").references(() => cards.id),
  offerId: uuid("offer_id").references(() => offers.id),
  targetDate: date("target_date"),
  minSpendProgressMinor: integer("min_spend_progress_minor").default(0),
  explanation: jsonb("explanation"),
});

export const churnRules = pgTable("churn_rules", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  issuerId: uuid("issuer_id").references(() => issuers.id),
  cardId: uuid("card_id").references(() => cards.id),
  programId: uuid("program_id").references(() => programs.id),
  ruleType: churnRuleTypeEnum("rule_type").notNull(),
  params: jsonb("params").notNull(),
  confidence: churnConfidenceEnum("confidence"),
  sourceUrl: text("source_url"),
  verifiedAt: timestamp("verified_at", { withTimezone: true }),
  active: boolean("active").notNull().default(true),
});

export const churnRecommendations = pgTable("churn_recommendations", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  userId: uuid("user_id")
    .notNull()
    .references(() => profiles.id, { onDelete: "cascade" }),
  generatedAt: timestamp("generated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
  items: jsonb("items").notNull(),
});
