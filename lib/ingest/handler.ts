import { randomUUID } from "node:crypto";
import {
  ingestSuccessResponseSchema,
  ingestTransactionSchema,
  type IngestSuccessResponse,
  type IngestTransactionPayload,
} from "@/lib/schemas/ingest";

export type IngestHandlerResult =
  | { ok: true; status: number; body: IngestSuccessResponse }
  | { ok: false; status: number; body: { error: { code: string; message: string; details?: unknown } } };

type StoredIngest = {
  transactionId: string;
  payload: IngestTransactionPayload;
};

const seenIdempotencyKeys = new Map<string, StoredIngest>();

export function resetIngestIdempotencyStore() {
  seenIdempotencyKeys.clear();
}

function badRequest(message: string, details?: unknown) {
  return {
    ok: false as const,
    status: 400,
    body: {
      error: {
        code: "validation_error",
        message,
        details,
      },
    },
  };
}

export function verifyIngestBearerToken(
  authorizationHeader: string | null,
  expectedToken: string | undefined,
): boolean {
  if (!expectedToken) {
    return false;
  }

  if (!authorizationHeader?.startsWith("Bearer ")) {
    return false;
  }

  const token = authorizationHeader.slice("Bearer ".length).trim();
  return token === expectedToken;
}

export function handleIngestTransaction(
  payload: unknown,
  idempotencyKeyFromHeader?: string | null,
): IngestHandlerResult {
  const parsed = ingestTransactionSchema.safeParse(payload);
  if (!parsed.success) {
    return badRequest("Invalid ingest payload", parsed.error.flatten());
  }

  const body = parsed.data;

  if (
    idempotencyKeyFromHeader &&
    idempotencyKeyFromHeader !== body.idempotency_key
  ) {
    return badRequest("Idempotency-Key header does not match body");
  }

  const existing = seenIdempotencyKeys.get(body.idempotency_key);
  if (existing) {
    return {
      ok: true,
      status: 200,
      body: ingestSuccessResponseSchema.parse({
        transaction_id: existing.transactionId,
        status: "draft",
        idempotent_replay: true,
      }),
    };
  }

  const transactionId = randomUUID();
  seenIdempotencyKeys.set(body.idempotency_key, {
    transactionId,
    payload: body,
  });

  return {
    ok: true,
    status: 201,
    body: ingestSuccessResponseSchema.parse({
      transaction_id: transactionId,
      status: "draft",
    }),
  };
}
