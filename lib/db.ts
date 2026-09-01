import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "@/db/schema";

let client: ReturnType<typeof postgres> | null = null;
let db: ReturnType<typeof drizzle<typeof schema>> | null = null;

export function getDb() {
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    return null;
  }

  if (!client) {
    client = postgres(databaseUrl, { prepare: false });
    db = drizzle(client, { schema });
  }

  return db;
}

export type Database = NonNullable<ReturnType<typeof getDb>>;
