import { NextResponse } from "next/server";
import {
  handleIngestTransaction,
  verifyIngestBearerToken,
} from "@/lib/ingest/handler";
import { getDb } from "@/lib/db";
import { ingestLogs } from "@/db/schema";

export async function POST(request: Request) {
  const expectedToken = process.env.INGEST_DEV_TOKEN;
  if (
    !verifyIngestBearerToken(request.headers.get("authorization"), expectedToken)
  ) {
    return NextResponse.json(
      {
        error: {
          code: "unauthorized",
          message: "Invalid or missing bearer token",
        },
      },
      { status: 401 },
    );
  }

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "invalid_json",
          message: "Request body must be valid JSON",
        },
      },
      { status: 400 },
    );
  }

  const result = handleIngestTransaction(
    payload,
    request.headers.get("Idempotency-Key"),
  );

  if (result.ok) {
    const db = getDb();
    if (db) {
      try {
        await db.insert(ingestLogs).values({
          payload,
          resultCode: String(result.status),
        });
      } catch {
        // Best-effort logging when DATABASE_URL is configured but unavailable.
      }
    }

    return NextResponse.json(result.body, { status: result.status });
  }

  return NextResponse.json(result.body, { status: result.status });
}
