import { sql } from "drizzle-orm";
import {
  char,
  customType,
  pgTable,
  text,
  timestamp,
  uuid,
} from "drizzle-orm/pg-core";
import { riskToleranceEnum, userRoleEnum } from "./enums";

const bytea = customType<{ data: Buffer; driverData: Buffer }>({
  dataType() {
    return "bytea";
  },
});

export const profiles = pgTable("profiles", {
  id: uuid("id").primaryKey(),
  displayName: text("display_name"),
  role: userRoleEnum("role").notNull().default("user"),
  defaultCurrency: char("default_currency", { length: 3 })
    .notNull()
    .default("CAD"),
  timezone: text("timezone").notNull().default("America/Toronto"),
  riskTolerance: riskToleranceEnum("risk_tolerance")
    .notNull()
    .default("balanced"),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const devices = pgTable("devices", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  userId: uuid("user_id")
    .notNull()
    .references(() => profiles.id, { onDelete: "cascade" }),
  label: text("label").notNull(),
  tokenHash: bytea("token_hash").notNull().unique(),
  scopes: text("scopes")
    .array()
    .notNull()
    .default(sql`'{write:transactions}'::text[]`),
  lastUsedAt: timestamp("last_used_at", { withTimezone: true }),
  revokedAt: timestamp("revoked_at", { withTimezone: true }),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});
