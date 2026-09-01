import { z } from "zod";

export const ingestCardRefSchema = z.object({
  match_hint: z.string().min(1),
});

export const ingestClientMetaSchema = z.object({
  shortcut_version: z.string().optional(),
  locale: z.string().optional(),
});

export const ingestTransactionSchema = z.object({
  idempotency_key: z.string().uuid(),
  device_token: z.string().optional(),
  card_ref: ingestCardRefSchema.optional(),
  merchant: z.string().nullable().optional(),
  amount_minor: z.number().int(),
  currency: z.string().length(3),
  occurred_at: z.string().datetime(),
  client_meta: ingestClientMetaSchema.optional(),
});

export type IngestTransactionPayload = z.infer<typeof ingestTransactionSchema>;

export const ingestSuccessResponseSchema = z.object({
  transaction_id: z.string().uuid(),
  status: z.literal("draft"),
  idempotent_replay: z.boolean().optional(),
});

export type IngestSuccessResponse = z.infer<typeof ingestSuccessResponseSchema>;
