import { beforeEach, describe, expect, it } from "vitest";
import {
  handleIngestTransaction,
  resetIngestIdempotencyStore,
  verifyIngestBearerToken,
} from "@/lib/ingest/handler";

const validPayload = {
  idempotency_key: "550e8400-e29b-41d4-a716-446655440000",
  amount_minor: 485,
  currency: "CAD",
  occurred_at: "2026-08-22T14:31:02Z",
};

describe("verifyIngestBearerToken", () => {
  it("accepts a matching bearer token", () => {
    expect(
      verifyIngestBearerToken(
        "Bearer churney_dtk_spike_dev_only",
        "churney_dtk_spike_dev_only",
      ),
    ).toBe(true);
  });

  it("rejects missing authorization", () => {
    expect(verifyIngestBearerToken(null, "churney_dtk_spike_dev_only")).toBe(
      false,
    );
  });
});

describe("handleIngestTransaction", () => {
  beforeEach(() => {
    resetIngestIdempotencyStore();
  });

  it("creates a draft transaction", () => {
    const result = handleIngestTransaction(validPayload);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.status).toBe(201);
      expect(result.body.status).toBe("draft");
      expect(result.body.transaction_id).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
      );
    }
  });

  it("returns validation errors for invalid payloads", () => {
    const result = handleIngestTransaction({ amount_minor: 100 });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.status).toBe(400);
      expect(result.body.error.code).toBe("validation_error");
    }
  });

  it("replays idempotent requests", () => {
    const first = handleIngestTransaction(validPayload);
    const second = handleIngestTransaction(validPayload);

    expect(first.ok).toBe(true);
    expect(second.ok).toBe(true);

    if (first.ok && second.ok) {
      expect(second.status).toBe(200);
      expect(second.body.idempotent_replay).toBe(true);
      expect(second.body.transaction_id).toBe(first.body.transaction_id);
    }
  });
});
