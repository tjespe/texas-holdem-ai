import { z } from "zod";

export const loginResponseSchema = z.union([
  z.object({
    result: z.literal("ok"),
    token: z.string(),
  }),
  z.object({
    error: z.string(),
  }),
]);

// Then derive the TS type from this schema:
export type LoginResponse = z.infer<typeof loginResponseSchema>;
