import { sql } from "drizzle-orm";
import {
  boolean,
  date,
  integer,
  numeric,
  pgTable,
  primaryKey,
  text,
  timestamp,
  unique,
  uuid,
} from "drizzle-orm/pg-core";
import {
  bonusStatusEnum,
  capPeriodEnum,
  cardNetworkEnum,
  offerStatusEnum,
  redemptionKindEnum,
  rewardKindEnum,
} from "./enums";

export const issuers = pgTable("issuers", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  slug: text("slug").notNull().unique(),
  name: text("name").notNull(),
  rulesNote: text("rules_note"),
});

export const networks = pgTable("networks", {
  id: cardNetworkEnum("id").primaryKey(),
  acceptanceNotes: text("acceptance_notes"),
});

export const categories = pgTable("categories", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  slug: text("slug").notNull().unique(),
  name: text("name").notNull(),
});

export const programs = pgTable("programs", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  slug: text("slug").notNull().unique(),
  name: text("name").notNull(),
  issuerId: uuid("issuer_id").references(() => issuers.id),
  rewardKind: rewardKindEnum("reward_kind").notNull(),
  flexibilityScore: numeric("flexibility_score", { precision: 5, scale: 2 }),
});

export const programExcludedCategories = pgTable(
  "program_excluded_categories",
  {
    programId: uuid("program_id")
      .notNull()
      .references(() => programs.id, { onDelete: "cascade" }),
    categoryId: uuid("category_id")
      .notNull()
      .references(() => categories.id),
    sourceUrl: text("source_url"),
    verifiedAt: timestamp("verified_at", { withTimezone: true }),
  },
  (table) => [primaryKey({ columns: [table.programId, table.categoryId] })],
);

export const cards = pgTable("cards", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  slug: text("slug").notNull().unique(),
  issuerId: uuid("issuer_id")
    .notNull()
    .references(() => issuers.id),
  programId: uuid("program_id")
    .notNull()
    .references(() => programs.id),
  networkId: cardNetworkEnum("network_id").notNull(),
  name: text("name").notNull(),
  status: text("status").notNull().default("live"),
  imageUrl: text("image_url"),
});

export const cardVersions = pgTable(
  "card_versions",
  {
    id: uuid("id")
      .primaryKey()
      .default(sql`gen_random_uuid()`),
    cardId: uuid("card_id")
      .notNull()
      .references(() => cards.id, { onDelete: "cascade" }),
    validFrom: date("valid_from").notNull(),
    validTo: date("valid_to"),
    annualFeeMinor: integer("annual_fee_minor").notNull(),
    extraCardFeeMinor: integer("extra_card_fee_minor"),
    fxFeePct: numeric("fx_fee_pct", { precision: 4, scale: 2 }),
    incomeReqPersonal: integer("income_req_personal"),
    incomeReqHousehold: integer("income_req_household"),
    purchaseApr: numeric("purchase_apr", { precision: 5, scale: 2 }),
    cashApr: numeric("cash_apr", { precision: 5, scale: 2 }),
    sourceUrl: text("source_url").notNull(),
    verifiedAt: timestamp("verified_at", { withTimezone: true }).notNull(),
  },
  (table) => [
    unique("card_versions_card_id_valid_from_unique").on(
      table.cardId,
      table.validFrom,
    ),
  ],
);

export const earnRates = pgTable("earn_rates", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  cardVersionId: uuid("card_version_id")
    .notNull()
    .references(() => cardVersions.id, { onDelete: "cascade" }),
  categoryId: uuid("category_id").references(() => categories.id),
  rate: numeric("rate", { precision: 6, scale: 3 }).notNull(),
  kind: rewardKindEnum("kind").notNull(),
  capAmountMinor: integer("cap_amount_minor"),
  capPeriod: capPeriodEnum("cap_period"),
  excluded: boolean("excluded").notNull().default(false),
});

export const earnPromotions = pgTable("earn_promotions", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  cardId: uuid("card_id")
    .notNull()
    .references(() => cards.id),
  categoryId: uuid("category_id")
    .notNull()
    .references(() => categories.id),
  rate: numeric("rate", { precision: 6, scale: 3 }).notNull(),
  stackable: boolean("stackable").notNull().default(false),
  startsOn: date("starts_on").notNull(),
  endsOn: date("ends_on"),
  capAmountMinor: integer("cap_amount_minor"),
  capPeriod: capPeriodEnum("cap_period"),
  sourceUrl: text("source_url"),
  verifiedAt: timestamp("verified_at", { withTimezone: true }),
});

export const offers = pgTable("offers", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  cardId: uuid("card_id")
    .notNull()
    .references(() => cards.id),
  status: offerStatusEnum("status").notNull().default("draft"),
  headline: text("headline").notNull(),
  minSpendMinor: integer("min_spend_minor"),
  deadlineDays: integer("deadline_days"),
  deadlineEndDate: date("deadline_end_date"),
  rewardPoints: integer("reward_points"),
  rewardCashbackMinor: integer("reward_cashback_minor"),
  eligibilityNotes: text("eligibility_notes"),
  firstYearFree: boolean("first_year_free").notNull().default(false),
  sourceUrl: text("source_url"),
  verifiedAt: timestamp("verified_at", { withTimezone: true }),
  publishedAt: timestamp("published_at", { withTimezone: true }),
  retiredAt: timestamp("retired_at", { withTimezone: true }),
});

export const redemptionOptions = pgTable("redemption_options", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  programId: uuid("program_id")
    .notNull()
    .references(() => programs.id, { onDelete: "cascade" }),
  kind: redemptionKindEnum("kind").notNull(),
  cppMin: numeric("cpp_min", { precision: 5, scale: 2 }),
  cppTypical: numeric("cpp_typical", { precision: 5, scale: 2 }),
  cppMax: numeric("cpp_max", { precision: 5, scale: 2 }),
  exampleRedemption: text("example_redemption"),
  notes: text("notes"),
  validFrom: date("valid_from").notNull().default(sql`CURRENT_DATE`),
  validTo: date("valid_to"),
  sourceUrl: text("source_url"),
  verifiedAt: timestamp("verified_at", { withTimezone: true }),
});

export const transferRates = pgTable("transfer_rates", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  fromProgramId: uuid("from_program_id")
    .notNull()
    .references(() => programs.id),
  toProgramId: uuid("to_program_id")
    .notNull()
    .references(() => programs.id),
  ratioNum: integer("ratio_num").notNull(),
  ratioDen: integer("ratio_den").notNull(),
  minTransfer: integer("min_transfer"),
  annualCap: integer("annual_cap"),
  validFrom: date("valid_from").notNull(),
  validTo: date("valid_to"),
  sourceUrl: text("source_url"),
  verifiedAt: timestamp("verified_at", { withTimezone: true }),
});

export const conversionBonuses = pgTable("conversion_bonuses", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  transferRateId: uuid("transfer_rate_id").references(() => transferRates.id),
  fromProgramId: uuid("from_program_id")
    .notNull()
    .references(() => programs.id),
  toProgramId: uuid("to_program_id")
    .notNull()
    .references(() => programs.id),
  bonusPct: integer("bonus_pct"),
  bonusRatioNum: integer("bonus_ratio_num"),
  bonusRatioDen: integer("bonus_ratio_den"),
  status: bonusStatusEnum("status").notNull().default("rumored"),
  startsOn: date("starts_on"),
  endsOn: date("ends_on").notNull(),
  constraintsText: text("constraints_text"),
  sourceUrl: text("source_url"),
  verifiedAt: timestamp("verified_at", { withTimezone: true }),
});

export const programValuations = pgTable("program_valuations", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  programId: uuid("program_id")
    .notNull()
    .references(() => programs.id),
  context: text("context").notNull(),
  baselineCpp: numeric("baseline_cpp", { precision: 5, scale: 2 }).notNull(),
  rationale: text("rationale"),
  validFrom: date("valid_from").notNull().default(sql`CURRENT_DATE`),
  validTo: date("valid_to"),
});
