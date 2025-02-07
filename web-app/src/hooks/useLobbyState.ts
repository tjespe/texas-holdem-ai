import { useEffect, useRef, useState } from "react";
import { z } from "zod";
import { getLobbyDetail, Lobby, lobbySchema } from "../api/lobbies";
import { useParams } from "react-router-dom";

export const lobbyMessageSchema = z.discriminatedUnion("type", [
  lobbySchema.extend({
    type: z.literal("LOBBY_UPDATE"),
  }),
]);

export type LobbyMessage = z.infer<typeof lobbyMessageSchema>;

export function useLobbyState() {
  const [lobby, setLobby] = useState<Lobby | null>(null);
  const { lobbyId } = useParams<{ lobbyId: string }>();
  const socketRef = useRef<WebSocket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(
    function fetchLobbyOnPageLoad() {
      if (!lobbyId) {
        setError("No lobby ID provided");
        return;
      }
      try {
        setLoading(true);
        setError(null);
        getLobbyDetail(lobbyId).then(setLobby);
      } catch (err) {
        console.error(err);
        setError("Failed to load lobby details");
      } finally {
        setLoading(false);
      }
    },
    [lobbyId]
  );

  useEffect(() => {
    const ws = new WebSocket(
      `${import.meta.env.VITE_WS_URL}/lobbies/${lobbyId}?token=${
        localStorage.token
      }`
    );
    socketRef.current = ws;

    ws.onopen = () => {
      console.log("Connected to Lobby WebSocket:", lobbyId);
    };

    ws.onmessage = (event) => {
      console.log("Lobby WebSocket message received:", event.data);

      try {
        const data = JSON.parse(event.data);
        const parsed = lobbyMessageSchema.parse(data);

        // Update state when a message is received
        if (parsed.type === "LOBBY_UPDATE") {
          setLobby(parsed);
        }
      } catch (error) {
        console.error("Lobby WS parse/validation error:", error);
      }
    };

    ws.onclose = () => {
      console.log("Lobby WebSocket closed:", lobbyId);
    };

    return () => {
      console.log("Closing Lobby WebSocket on purpose:", lobbyId);

      ws.close();
    };
  }, [lobbyId]);

  if (error) {
    return {
      lobby: null,
      loading: false,
      error,
    };
  }

  if (loading) {
    return {
      lobby: null,
      loading: true,
      error: null,
    };
  }

  return {
    lobby,
    loading: false,
    error: null,
  };
}
