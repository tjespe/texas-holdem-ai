import { ContentCopy, Share as ShareIcon } from "@mui/icons-material";
import {
  Box,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  addBot,
  getLobbyDetail,
  joinLobby,
  leaveLobby,
  Lobby,
  startLobby,
} from "../../../api/lobbies";
import { useAuthContext } from "../../../contexts/AuthContext";
import { AddBotButton } from "./AddBotButton";
import { GameTable } from "../../../components/GameTable";

export function LobbyDetail() {
  const { username } = useAuthContext();
  const { lobbyId } = useParams<{ lobbyId: string }>();
  const navigate = useNavigate();

  const [lobby, setLobby] = useState<Lobby | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  const fetchLobby = useCallback(
    async function () {
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
    },
    [lobbyId]
  );

  // Fetch lobby details on mount or whenever lobbyId changes
  useEffect(() => {
    fetchLobby();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lobbyId]);

  // Join the lobby as the current user (if not already in players)
  const handleJoin = useCallback(
    async function () {
      if (!lobbyId) {
        setError("No lobby ID provided");
        return;
      }
      if (!username) {
        setError("You are not logged in");
        return;
      }
      try {
        setLoading(true);
        const resp = await joinLobby(lobbyId);
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
    },
    [fetchLobby, lobbyId, username]
  );

  useEffect(
    function autoLeaveLobbyOnPageLeave() {
      if (lobbyId) {
        return function autoLeaveLobby() {
          // Leave the lobby automatically when the user leaves the page if we auto-joined
          leaveLobby(lobbyId);
        };
      }
    },
    [lobbyId]
  );

  // Copy link to clipboard
  const handleCopy = useCallback(() => {
    const inviteLink = window.location.href;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(inviteLink).then(() => {
        setCopiedLink(true);
        setTimeout(() => setCopiedLink(false), 2000);
      });
    } else {
      // Fallback: Create a hidden textarea to copy manually
      const textArea = document.createElement("textarea");
      textArea.value = inviteLink;
      textArea.setAttribute("readonly", ""); // Prevent keyboard popup on mobile
      textArea.style.position = "absolute";
      textArea.style.left = "-9999px"; // Move it off-screen
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);

      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    }
  }, []);

  // Share via Web Share API (Mobile & AirDrop)
  const handleShare = useCallback(async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: "Join my Poker Game!",
          text: "Click the link to join my Texas Hold'em poker game.",
          url: window.location.href,
        });
      } catch (err) {
        console.error("Sharing failed:", err);
      }
    } else {
      // Fallback to clipboard if share isn't supported
      handleCopy();
    }
  }, [handleCopy]);

  if (!lobbyId) {
    return <Typography color="error">No lobby ID provided</Typography>;
  }

  // Add a bot to the lobby
  async function handleAddBot(botType: string) {
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
        // Refresh
        await fetchLobby();
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

  if (lobby.started && username && lobby.players?.includes(username)) {
    return <GameTable />;
  }

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
          <Stack direction="row" spacing={3}>
            <Tooltip title="Share with friends">
              <Button
                variant="outlined"
                color="primary"
                onClick={handleShare}
                startIcon={copiedLink ? <ContentCopy /> : <ShareIcon />}
              >
                {copiedLink ? "Link copied" : "Invite Friends"}
              </Button>
            </Tooltip>
            <AddBotButton onAddBot={handleAddBot} />
          </Stack>

          {!userAlreadyJoined ? (
            <Button variant="contained" onClick={handleJoin}>
              Join Lobby
            </Button>
          ) : (
            <Button variant="contained" onClick={handleStartGame}>
              Start Game
            </Button>
          )}
        </Stack>
      )}

      {/* If the lobby is started, show a button to go to the game table */}
      {lobby.started && (
        <Button variant="outlined" onClick={() => navigate(`/game/${lobbyId}`)}>
          Go to Game
        </Button>
      )}
    </Box>
  );
}
