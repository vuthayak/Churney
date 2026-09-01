import { sql } from "drizzle-orm";
import {
  bigint,
  char,
  date,
  integer,
  jsonb,
  numeric,
  pgTable,
  text,
  timestamp,
  uuid,
} from "drizzle-orm/pg-core";
import { txSourceEnum, txStatusEnum } from "./enums";
import { categories } from "./curated";
import { devices, profiles } from "./identity";
import { merchants } from "./merchants";
import { userCards } from "./wallet";

export const transactions = pgTable("transactions", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  userId: uuid("user_id")
    .notNull()
    .references(() => profiles.id, { onDelete: "cascade" }),
  userCardId: uuid("user_card_id").references(() => userCards.id),
  source: txSourceEnum("source").notNull(),
  status: txStatusEnum("status").notNull().default("draft"),
  occurredAt: timestamp("occurred_at", { withTimezone: true }).notNull(),
  merchantRaw: text("merchant_raw"),
  merchantId: uuid("merchant_id").references(() => merchants.id),
  categoryOverride: uuid("category_override").references(() => categories.id),
  amountMinor: integer("amount_minor").notNull(),
  currency: char("currency", { length: 3 }).notNull().default("CAD"),
  fxRate: numeric("fx_rate", { precision: 12, scale: 8 }),
  fxSource: text("fx_source"),
  fxRateDate: date("fx_rate_date"),
  cadAmountMinor: integer("cad_amount_minor").generatedAlwaysAs(
    sql`CASE WHEN currency = 'CAD' THEN amount_minor ELSE round(amount_minor * fx_rate) END`,
  ),
  dedupeKey: text("dedupe_key"),
  idempotencyKey: text("idempotency_key"),
  engineVersion: integer("engine_version").notNull().default(0),
  earnedPoints: bigint("earned_points", { mode: "number" }),
  earnedCashbackMinor: bigint("earned_cashback_minor", { mode: "number" }),
  valueCppSnapshot: numeric("value_cpp_snapshot", { precision: 5, scale: 2 }),
  breakdown: jsonb("breakdown"),
  bestWalletAlternative: jsonb("best_wallet_alternative"),
  confidence: numeric("confidence", { precision: 3, scale: 2 }),
  importedBatchId: uuid("imported_batch_id"),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const ingestLogs = pgTable("ingest_logs", {
  id: bigint("id", { mode: "number" }).primaryKey().generatedAlwaysAsIdentity(),
  deviceId: uuid("device_id").references(() => devices.id),
  payload: jsonb("payload").notNull(),
  resultCode: text("result_code"),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});
