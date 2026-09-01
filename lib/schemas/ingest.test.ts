import { describe, expect, it } from "vitest";
import { ingestTransactionSchema } from "@/lib/schemas/ingest";

const validPayload = {
  idempotency_key: "550e8400-e29b-41d4-a716-446655440000",
  amount_minor: 485,
  currency: "CAD",
  occurred_at: "2026-08-22T14:31:02Z",
  merchant: "TIM HORTONS #4421",
};

describe("ingestTransactionSchema", () => {
  it("accepts a valid payload", () => {
    const result = ingestTransactionSchema.safeParse(validPayload);
    expect(result.success).toBe(true);
  });

  it("rejects missing idempotency_key", () => {
    const rest = { ...validPayload };
    delete (rest as Partial<typeof validPayload>).idempotency_key;
    const result = ingestTransactionSchema.safeParse(rest);
    expect(result.success).toBe(false);
  });

  it("rejects non-integer amount_minor", () => {
    const result = ingestTransactionSchema.safeParse({
      ...validPayload,
      amount_minor: 4.85,
    });
    expect(result.success).toBe(false);
  });
});
