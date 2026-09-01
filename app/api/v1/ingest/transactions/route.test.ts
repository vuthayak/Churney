import { beforeEach, describe, expect, it, vi } from "vitest";
import { POST } from "@/app/api/v1/ingest/transactions/route";
import { resetIngestIdempotencyStore } from "@/lib/ingest/handler";

const validPayload = {
  idempotency_key: "550e8400-e29b-41d4-a716-446655440000",
  amount_minor: 485,
  currency: "CAD",
  occurred_at: "2026-08-22T14:31:02Z",
};

function makeRequest(
  body: unknown,
  token = "churney_dtk_spike_dev_only",
): Request {
  return new Request("http://localhost/api/v1/ingest/transactions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

describe("POST /api/v1/ingest/transactions", () => {
  beforeEach(() => {
    resetIngestIdempotencyStore();
    vi.stubEnv("INGEST_DEV_TOKEN", "churney_dtk_spike_dev_only");
  });

  it("rejects unauthorized requests", async () => {
    const response = await POST(makeRequest(validPayload, "wrong-token"));
    expect(response.status).toBe(401);
  });

  it("accepts valid ingest payloads", async () => {
    const response = await POST(makeRequest(validPayload));
    expect(response.status).toBe(201);

    const body = await response.json();
    expect(body.status).toBe("draft");
    expect(body.transaction_id).toBeTruthy();
  });

  it("replays idempotent ingest payloads", async () => {
    const first = await POST(makeRequest(validPayload));
    const second = await POST(makeRequest(validPayload));

    expect(first.status).toBe(201);
    expect(second.status).toBe(200);

    const firstBody = await first.json();
    const secondBody = await second.json();
    expect(secondBody.transaction_id).toBe(firstBody.transaction_id);
    expect(secondBody.idempotent_replay).toBe(true);
  });
});
