import { useState } from "react";
import {
  Box,
  Button,
  Stack,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
} from "@mui/material";
import { useParams } from "react-router-dom";
import { useWebSocket } from "../hooks/useWebSocket";
import { GameState, Player } from "../schemas/messages";

const WS_BASE_URL = import.meta.env.VITE_WS_URL;

const getSuit = (card: number) => {
  const suits = ["♠", "♣", "♦", "♥"];
  return suits[Math.floor(card / 13)];
};

const getRank = (card: number) => {
  const ranks = [
    "A",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
  ];
  return ranks[card % 13];
};

export const GameTable: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [betInput, setBetInput] = useState("");
  const [ourTurn, setOurTurn] = useState(false);
  const [players, setPlayers] = useState<Player[]>([]);
  const [hand, setHand] = useState<number[]>([]);
  const { lobbyId } = useParams();
  const [turn, setTurn] = useState(0);
  const [allHands, setAllHands] = useState<
    (number[] | null | undefined)[] | undefined
  >(undefined);

  const wsUrl = `${WS_BASE_URL}/lobbies/${lobbyId}?token=${localStorage.token}`;
  const { sendMessage } = useWebSocket(wsUrl, (msg) => {
    switch (msg.type) {
      case "PLAY_REQUEST":
        setGameState(msg.state);
        setHand(msg.hand);
        setOurTurn(true);
        break;
      case "OBSERVE_BET":
        setGameState(msg.state);
        setOurTurn(false);
        setTurn(() => {
          let nextPlayer = msg.player_index + 1;
          while (msg.state.player_is_folded[nextPlayer]) {
            nextPlayer = (nextPlayer + 1) % players.length;
          }
          return nextPlayer;
        });
        break;
      case "ROUND_OVER":
        setGameState(msg.state);
        setOurTurn(false);
        break;
      case "GET_TO_KNOW_EACH_OTHER":
        setPlayers(msg.players);
        break;
      case "SHOWDOWN":
        setGameState(msg.state);
        setAllHands(msg.all_hands);
        break;
      default:
        console.log("Unknown message type:", msg);
    }
  });

  const handleBet = (betAmount: number) => {
    sendMessage({ type: "USER_BET", bet: betAmount });
    setOurTurn(false);
    setBetInput("");
    setTurn((turn + 1) % players.length);
  };

  const highestBet = Math.max(...(gameState?.bet_in_game || [0]));
  const ourBet = gameState?.bet_in_game[turn] || 0;
  const callAmount = highestBet - ourBet;
  const minRaise = highestBet + (gameState?.big_blind || 0);

  return (
    <Stack
      spacing={2}
      sx={{ maxWidth: "800px", margin: "auto", textAlign: "center", py: 2 }}
    >
      <Typography variant="h4">Poker Table</Typography>

      {/* Players arranged in a table layout */}
      <Grid container justifyContent="center" spacing={2}>
        {players.map((player, index) => (
          <Grid key={player.index} item xs={4}>
            <Card
              sx={{
                backgroundColor: gameState?.player_is_folded[player.index]
                  ? "#444"
                  : "#222",
                border:
                  turn === player.index ? "2px solid gold" : "1px solid #666",
                textAlign: "center",
              }}
            >
              <CardContent>
                <Typography fontWeight="bold">{player.name}</Typography>
                <Typography variant="body2">
                  Stack: {gameState?.player_piles[player.index]} chips
                </Typography>
                <Typography variant="body2">
                  Bet: {gameState?.bet_in_game[player.index]}
                </Typography>
                {gameState?.player_is_folded[player.index] && (
                  <Typography color="error">Folded</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Table cards */}
      <Stack direction="row" justifyContent="center" spacing={1} sx={{ py: 2 }}>
        {gameState?.public_cards.map((card, index) => (
          <Box
            key={index}
            sx={{
              width: 50,
              height: 70,
              backgroundColor: "#fff",
              borderRadius: 2,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.5rem",
              color: ["♠", "♣"].includes(getSuit(card)) ? "black" : "red",
            }}
          >
            {getRank(card)}
            {getSuit(card)}
          </Box>
        ))}
      </Stack>

      {/* Your hand */}
      {ourTurn && (
        <Stack>
          <Typography variant="h6">Your Hand</Typography>
          <Stack direction="row" justifyContent="center" spacing={1}>
            {hand.map((card, index) => (
              <Box
                key={index}
                sx={{
                  width: 50,
                  height: 70,
                  backgroundColor: "#fff",
                  borderRadius: 2,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "1.5rem",
                  color: ["♠", "♣"].includes(getSuit(card)) ? "black" : "red",
                }}
              >
                {getRank(card)}
                {getSuit(card)}
              </Box>
            ))}
          </Stack>
        </Stack>
      )}

      {/* Betting Controls */}
      {ourTurn && (
        <Stack spacing={1}>
          <Typography variant="h6">Your Move</Typography>
          <Stack direction="row" justifyContent="center" spacing={2}>
            {/* Check / Fold */}
            <Button variant="outlined" onClick={() => handleBet(0)}>
              {callAmount === 0 ? "Check" : "Fold"}
            </Button>

            {/* Call (if available) */}
            {callAmount > 0 && (
              <Button
                variant="contained"
                color="primary"
                onClick={() => handleBet(callAmount)}
              >
                Call ({callAmount})
              </Button>
            )}

            {/* Raise */}
            <TextField
              label="Raise"
              type="number"
              value={betInput}
              onChange={(e) => setBetInput(e.target.value)}
              sx={{ width: "100px" }}
            />
            <Button
              variant="contained"
              color="secondary"
              onClick={() => handleBet(parseInt(betInput, 10))}
              disabled={parseInt(betInput, 10) < minRaise}
            >
              Raise
            </Button>
          </Stack>
        </Stack>
      )}

      {/* Showdown hands */}
      {allHands && (
        <Stack>
          <Typography variant="h6">Showdown!</Typography>
          {allHands.map((hand, idx) => (
            <Stack key={idx}>
              <Typography fontWeight="bold">
                {players[idx].name}'s Hand:
              </Typography>
              <Stack direction="row" justifyContent="center" spacing={1}>
                {hand?.map((card, i) => (
                  <Box
                    key={i}
                    sx={{
                      width: 50,
                      height: 70,
                      backgroundColor: "#fff",
                      textAlign: "center",
                    }}
                  >
                    {getRank(card)}
                    {getSuit(card)}
                  </Box>
                ))}
              </Stack>
            </Stack>
          ))}
        </Stack>
      )}
    </Stack>
  );
};
