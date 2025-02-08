import { z } from "zod";
import { apiClient } from ".";

export const lobbySchema = z.object({
  lobby_id: z.string(),
  started: z.boolean().optional(),
  players: z
    .array(
      z.union([
        z.string(),
        z.object({
          type: z.string(),
          bot_type: z.string(),
          bot_name: z.string(),
        }),
      ])
    )
    .optional(),
});
export type Lobby = z.infer<typeof lobbySchema>;

export const lobbiesListSchema = z.object({
  lobbies: z.array(lobbySchema),
});

export type LobbiesList = z.infer<typeof lobbiesListSchema>;

export const botOptionSchema = z.object({
  name: z.string(),
  type: z.string(),
});

export type BotOption = z.infer<typeof botOptionSchema>;

export async function listBotOptions(): Promise<BotOption[]> {
  const resp = await apiClient(`/bot-options`, {
    method: "GET",
  });
  const data = await resp.json();
  const parsed = z.array(botOptionSchema).parse(data);
  return parsed;
}

// GET /lobbies -> { "lobbies": [ { "lobby_id": "...", "started": false, "players": [...]} ] }
export async function listLobbies(): Promise<LobbiesList> {
  const resp = await apiClient(`/lobbies`, {
    method: "GET",
  });
  const data = await resp.json();
  // Validate with Zod
  const parsed = lobbiesListSchema.parse(data);
  return parsed;
}

// POST /lobbies -> { "lobby_id": "some_id" }
const createLobbyResponseSchema = z.object({
  lobby_id: z.string(),
});
export type CreateLobbyResponse = z.infer<typeof createLobbyResponseSchema>;

export async function createLobby(): Promise<CreateLobbyResponse> {
  const resp = await apiClient(`/lobbies`, { method: "POST" });
  const data = await resp.json();
  return createLobbyResponseSchema.parse(data);
}

export async function getLobbyDetail(lobbyId: string): Promise<Lobby> {
  const resp = await apiClient(`/lobbies/${lobbyId}`, {
    method: "GET",
  });
  const data = await resp.json();
  return lobbySchema.parse(data);
}

export async function joinLobby(lobbyId: string) {
  const resp = await apiClient(`/lobbies/${lobbyId}/join`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return resp.json(); // might be { result: "ok", error?: string }
}

export async function leaveLobby(lobbyId: string) {
  const resp = await apiClient(`/lobbies/${lobbyId}/leave`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return resp.json(); // might be { result: "ok", error?: string }
}

export async function addBot(
  lobbyId: string,
  botType: string,
  botName: string
) {
  const resp = await apiClient(
    `/lobbies/${lobbyId}/add_bot?bot_type=${botType}&bot_name=${botName}`,
    {
      method: "POST",
    }
  );
  return resp.json();
}

export async function startLobby(lobbyId: string) {
  const resp = await apiClient(`/lobbies/${lobbyId}/start`, {
    method: "POST",
  });
  return resp.json(); // e.g. { result: "game_started" }
}
