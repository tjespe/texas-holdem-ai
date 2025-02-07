import { useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
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

const WS_BASE_URL = import.meta.env.VITE_WS_URL;

export function useWebSocket(
  onMessage: (msg: ReturnType<typeof serverMessageSchema.parse>) => void
) {
  const socketRef = useRef<WebSocket | null>(null);
  const { lobbyId } = useParams<{ lobbyId: string }>();
  const wsUrl = `${WS_BASE_URL}/games/${lobbyId}?token=${localStorage.token}`;

  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected to ", wsUrl);
    };

    ws.onmessage = (event) => {
      console.log("WebSocket message received:", event.data);

      try {
        const data = JSON.parse(event.data);
        // Validate
        const parsed = serverMessageSchema.parse(data);
        onMessage(parsed);
      } catch (error) {
        console.error("WS parse/validation error:", error);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
    };

    return () => {
      ws.close();
    };
  }, [onMessage, wsUrl]);

  function sendMessage(message: unknown) {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message));
    }
  }

  return { sendMessage };
}
