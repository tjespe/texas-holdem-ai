// src/components/LobbyList.tsx

import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import { listLobbies, createLobby, Lobby } from "../../api/lobbies";

interface LobbyListProps {
  username: string; // e.g. "alice"
}

export function LobbyList({ username }: LobbyListProps) {
  const [lobbies, setLobbies] = useState<Lobby[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();

  // Fetch lobbies on mount
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const { lobbies } = await listLobbies();
        setLobbies(lobbies);
      } catch (err) {
        console.error(err);
        setError("Failed to load lobbies.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // Create a new lobby
  async function handleCreateLobby() {
    try {
      setLoading(true);
      const { lobby_id } = await createLobby();
      // Option 1: Just add to local list
      setLobbies([...lobbies, { lobby_id }]);
      // Option 2 (common): navigate to the new lobby detail page
      // navigate(`/lobbies/${lobby_id}`);
    } catch (err) {
      setError("Failed to create a lobby.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  // (Optional) show a button to join or view a specific lobby
  function handleLobbyClick(lobbyId: string) {
    navigate(`/lobbies/${lobbyId}`);
  }

  return (
    <Box sx={{ maxWidth: 600, margin: "auto", textAlign: "center" }}>
      <Typography variant="h4" sx={{ mb: 2 }}>
        Lobbies
      </Typography>

      <Box sx={{ mb: 2 }}>
        <Button
          variant="contained"
          onClick={handleCreateLobby}
          disabled={loading}
        >
          Create New Lobby
        </Button>
      </Box>

      {loading && <CircularProgress />}
      {error && <Typography color="error">{error}</Typography>}

      <List>
        {lobbies.map((lobby) => {
          const startedStr = lobby.started ? "Started" : "Not Started";
          const playersArr = Array.isArray(lobby.players) ? lobby.players : [];
          const playerCount = playersArr.length;

          return (
            <ListItem
              key={lobby.lobby_id}
              onClick={() => handleLobbyClick(lobby.lobby_id)}
            >
              <ListItemText
                primary={`Lobby ID: ${lobby.lobby_id}`}
                secondary={`Status: ${startedStr} — Players: ${playerCount}`}
              />
            </ListItem>
          );
        })}
      </List>
    </Box>
  );
}
