// src/schemas/messages.ts
import { z } from "zod";

export const serverMessageSchema = z.object({
  type: z.string(),
  bet: z.number().optional(),
  state: z.any().optional(),
});

export type ServerMessage = z.infer<typeof serverMessageSchema>;
