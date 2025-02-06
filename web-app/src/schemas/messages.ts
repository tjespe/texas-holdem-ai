// src/schemas/messages.ts
import { z } from "zod";

export const playerSchema = z.object({
  name: z.string(),
  index: z.number(),
  type: z.string(),
});

export type Player = z.infer<typeof playerSchema>;

const stateSchema = z.object({
  public_cards: z.array(z.number()),
  player_piles: z.array(z.number()),
  current_player_i: z.number(),
  bet_in_stage: z.array(z.number()),
  bet_in_game: z.array(z.number()),
  player_has_played: z.array(z.boolean()),
  player_is_folded: z.array(z.boolean()),
  big_blind: z.number(),
  pot: z.number(),
  stage: z.string(),
  sub_stage: z.string(),
  is_terminal: z.boolean(),
  all_players_are_done: z.boolean(),
});

export type GameState = z.infer<typeof stateSchema>;

export const serverMessageSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("PLAY_REQUEST"),
    state: stateSchema,
    hand: z.array(z.number()).length(2),
  }),
  z.object({
    type: z.literal("GET_TO_KNOW_EACH_OTHER"),
    players: z.array(playerSchema),
  }),
  z.object({
    type: z.literal("OBSERVE_BET"),
    player_index: z.number(),
    bet: z.number(),
    state: stateSchema,
    was_blind: z.boolean(),
  }),
  z.object({
    type: z.literal("ROUND_OVER"),
    state: stateSchema,
  }),
  z.object({
    type: z.literal("SHOWDOWN"),
    state: stateSchema,
    all_hands: z.array(z.array(z.number()).length(2).nullable()),
  }),
]);

export type ServerMessage = z.infer<typeof serverMessageSchema>;
