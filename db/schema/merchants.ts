import { sql } from "drizzle-orm";
import {
  bigint,
  integer,
  numeric,
  pgTable,
  text,
  timestamp,
  unique,
  uuid,
} from "drizzle-orm/pg-core";
import { cardNetworkEnum } from "./enums";
import { categories } from "./curated";
import { profiles } from "./identity";

export const merchants = pgTable("merchants", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  normName: text("norm_name").notNull(),
  displayName: text("display_name").notNull(),
  brandFamily: text("brand_family"),
  defaultCategoryId: uuid("default_category_id").references(() => categories.id),
  acceptedNetworks: cardNetworkEnum("accepted_networks")
    .array()
    .notNull()
    .default(sql`'{amex,visa,mastercard}'::card_network[]`),
  confidenceGlobal: numeric("confidence_global", { precision: 3, scale: 2 }),
});

export const merchantAliases = pgTable(
  "merchant_aliases",
  {
    id: bigint("id", { mode: "number" }).primaryKey().generatedAlwaysAsIdentity(),
    merchantId: uuid("merchant_id").references(() => merchants.id, {
      onDelete: "cascade",
    }),
    userId: uuid("user_id").references(() => profiles.id, {
      onDelete: "cascade",
    }),
    aliasNorm: text("alias_norm").notNull(),
  },
  (table) => [
    unique("merchant_aliases_user_id_alias_norm_unique").on(
      table.userId,
      table.aliasNorm,
    ),
  ],
);

export const pendingMerchants = pgTable("pending_merchants", {
  norm: text("norm").primaryKey(),
  occurrences: integer("occurrences").notNull().default(1),
  lastSeenAt: timestamp("last_seen_at", { withTimezone: true }),
  llmCategoryGuess: uuid("llm_category_guess").references(() => categories.id),
});
