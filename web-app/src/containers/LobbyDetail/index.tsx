import {
  Box,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  addBot,
  getLobbyDetail,
  joinLobby,
  Lobby,
  startLobby,
} from "../../api/lobbies";

interface LobbyDetailProps {
  username: string;
}

export function LobbyDetail({ username }: LobbyDetailProps) {
  const { lobbyId } = useParams<{ lobbyId: string }>();
  const navigate = useNavigate();

  const [lobby, setLobby] = useState<Lobby | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Bot UI
  const [botType, setBotType] = useState("random");

  async function fetchLobby() {
    if (!lobbyId) {
      setError("No lobby ID provided");
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await getLobbyDetail(lobbyId);
      setLobby(data);
    } catch (err) {
      console.error(err);
      setError("Failed to load lobby details");
    } finally {
      setLoading(false);
    }
  }

  // Fetch lobby details on mount or whenever lobbyId changes
  useEffect(() => {
    fetchLobby();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lobbyId]);

  if (!lobbyId) {
    return <Typography color="error">No lobby ID provided</Typography>;
  }

  // Join the lobby as the current user (if not already in players)
  async function handleJoin() {
    if (!lobbyId) {
      setError("No lobby ID provided");
      return;
    }
    try {
      setLoading(true);
      const resp = await joinLobby(lobbyId, username);
      if (resp.error) {
        setError(resp.error);
      } else {
        // Refresh
        await fetchLobby();
      }
    } catch (err) {
      console.error(err);
      setError("Failed to join lobby");
    } finally {
      setLoading(false);
    }
  }

  // Add a bot to the lobby
  async function handleAddBot() {
    if (!lobbyId) {
      setError("No lobby ID provided");
      return;
    }
    try {
      setLoading(true);
      const resp = await addBot(lobbyId, botType);
      if (resp.error) {
        setError(resp.error);
      } else {
        // Refresh
        await fetchLobby();
      }
    } catch (err) {
      console.error(err);
      setError("Failed to add bot");
    } finally {
      setLoading(false);
    }
  }

  // Start the game
  async function handleStartGame() {
    if (!lobbyId) {
      setError("No lobby ID provided");
      return;
    }
    try {
      setLoading(true);
      const resp = await startLobby(lobbyId);
      if (resp.error) {
        setError(resp.error);
      } else {
        // The game started
        // Typically we navigate to the game screen
        // e.g. /game/:lobbyId/:username
        navigate(`/game/${lobbyId}/${username}`);
      }
    } catch (err) {
      console.error(err);
      setError("Failed to start the game");
    } finally {
      setLoading(false);
    }
  }

  // If we're loading or there's an error, show that
  if (loading) {
    return (
      <Box sx={{ textAlign: "center", mt: 2 }}>
        <CircularProgress />
      </Box>
    );
  }
  if (error) {
    return (
      <Box sx={{ textAlign: "center", mt: 2 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!lobby) {
    return null; // or some empty state
  }

  // Check if user is in the list
  const playerList = Array.isArray(lobby.players) ? lobby.players : [];
  const userAlreadyJoined = playerList.some(
    (p) => typeof p === "string" && p === username
  );

  return (
    <Box sx={{ maxWidth: 600, margin: "auto", textAlign: "center", mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Lobby: {lobbyId}
      </Typography>

      <Typography variant="subtitle1" gutterBottom>
        {lobby.started ? "Game Already Started" : "Waiting to Start"}
      </Typography>

      <List sx={{ mb: 2 }}>
        {playerList.map((p, idx) => {
          if (typeof p === "string") {
            return (
              <ListItem key={idx}>
                <ListItemText primary={p} secondary="Human Player" />
              </ListItem>
            );
          } else {
            // e.g. { type: "bot", bot_type: "random" }
            return (
              <ListItem key={idx}>
                <ListItemText
                  primary={p.bot_type.toUpperCase() + " Bot"}
                  secondary={`Type: ${p.type}`}
                />
              </ListItem>
            );
          }
        })}
      </List>

      {/* If game isn't started, show controls */}
      {!lobby.started && (
        <Stack spacing={2} direction="column" alignItems="center">
          {!userAlreadyJoined && (
            <Button variant="contained" onClick={handleJoin}>
              Join Lobby
            </Button>
          )}

          {/* Add Bot UI */}
          <Stack spacing={1} direction="row" alignItems="center">
            <Select
              value={botType}
              onChange={(e) => setBotType(e.target.value as string)}
              size="small"
            >
              <MenuItem value="random">Random</MenuItem>
              <MenuItem value="max_ev">Max EV</MenuItem>
              <MenuItem value="cheating">Cheating</MenuItem>
              {/* Add more as needed */}
            </Select>
            <Button variant="contained" onClick={handleAddBot}>
              Add Bot
            </Button>
          </Stack>

          <Button variant="contained" color="success" onClick={handleStartGame}>
            Start Game
          </Button>
        </Stack>
      )}

      {/* If the lobby is started, show a button to go to the game table */}
      {lobby.started && (
        <Button
          variant="outlined"
          onClick={() => navigate(`/game/${lobbyId}/${username}`)}
        >
          Go to Game
        </Button>
      )}
    </Box>
  );
}
