import { sql } from "drizzle-orm";
import {
  date,
  pgTable,
  primaryKey,
  text,
  uuid,
} from "drizzle-orm/pg-core";
import { bonusLifecycleEnum, cardRoleEnum, eventStateEnum } from "./enums";
import { cards, offers } from "./curated";
import { categories } from "./curated";
import { merchants } from "./merchants";
import { profiles } from "./identity";

export const userCards = pgTable("user_cards", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  userId: uuid("user_id")
    .notNull()
    .references(() => profiles.id, { onDelete: "cascade" }),
  cardId: uuid("card_id")
    .notNull()
    .references(() => cards.id),
  nickname: text("nickname"),
  matchHint: text("match_hint").unique(),
  openedOn: date("opened_on"),
  closedOn: date("closed_on"),
  role: cardRoleEnum("role").notNull().default("auto"),
  bonusStatus: bonusLifecycleEnum("bonus_status").notNull().default("pending"),
  notes: text("notes"),
});

export const applicationsLog = pgTable("applications_log", {
  id: uuid("id")
    .primaryKey()
    .default(sql`gen_random_uuid()`),
  userId: uuid("user_id")
    .notNull()
    .references(() => profiles.id, { onDelete: "cascade" }),
  cardId: uuid("card_id")
    .notNull()
    .references(() => cards.id),
  offerId: uuid("offer_id").references(() => offers.id),
  state: eventStateEnum("state").notNull().default("submitted"),
  appliedOn: date("applied_on").notNull(),
  decidedOn: date("decided_on"),
  bonusPostedOn: date("bonus_posted_on"),
});

export const categoryOverrides = pgTable(
  "category_overrides",
  {
    userId: uuid("user_id")
      .references(() => profiles.id, { onDelete: "cascade" }),
    merchantId: uuid("merchant_id")
      .references(() => merchants.id, { onDelete: "cascade" }),
    categoryId: uuid("category_id").references(() => categories.id),
  },
  (table) => [primaryKey({ columns: [table.userId, table.merchantId] })],
);
