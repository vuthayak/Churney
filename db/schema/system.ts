import {
  bigint,
  date,
  jsonb,
  numeric,
  pgTable,
  primaryKey,
  text,
  timestamp,
  uuid,
} from "drizzle-orm/pg-core";
import { profiles } from "./identity";

export const fxRates = pgTable(
  "fx_rates",
  {
    rateDate: date("rate_date").notNull(),
    pair: text("pair").notNull(),
    rate: numeric("rate", { precision: 12, scale: 8 }).notNull(),
    source: text("source").notNull(),
    fetchedAt: timestamp("fetched_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [primaryKey({ columns: [table.rateDate, table.pair] })],
);

export const changeLog = pgTable("change_log", {
  id: bigint("id", { mode: "number" }).primaryKey().generatedAlwaysAsIdentity(),
  entity: text("entity").notNull(),
  entityId: uuid("entity_id").notNull(),
  diff: jsonb("diff").notNull(),
  reason: text("reason"),
  actor: uuid("actor").references(() => profiles.id),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});
