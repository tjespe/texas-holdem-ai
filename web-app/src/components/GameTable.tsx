// src/components/GameTable.tsx
import React, { useState } from "react";
import { Button, TextField, Stack } from "@mui/material";
import { useWebSocket } from "../hooks/useWebSocket";
import { useParams } from "react-router-dom";

interface GameState {
  pot?: number;
  public_cards?: number[];
  stage?: string;
  current_player_i?: number;
  // ... add other fields as needed
}

export const GameTable: React.FC = () => {
  const [gameState, setGameState] = useState<GameState>({});
  const [betInput, setBetInput] = useState("");
  const [ourTurn, setOurTurn] = useState(true);
  const { lobbyId } = useParams();

  const wsUrl = `ws://localhost:8000/ws/lobbies/${lobbyId}?token=${localStorage.token}`;
  const { sendMessage } = useWebSocket(wsUrl, (msg) => {
    switch (msg.type) {
      case "PLAY_REQUEST":
        // Server says it's your turn
        if (msg.state) setGameState(msg.state);
        setOurTurn(true);
        break;
      case "OBSERVE_BET":
        if (msg.state) setGameState(msg.state);
        break;
      case "ROUND_OVER":
        if (msg.state) setGameState(msg.state);
        alert("Round is over!");
        break;
      default:
        console.log("Unknown message type:", msg);
    }
  });

  const handleBet = () => {
    const bet = parseInt(betInput, 10) || 0;
    sendMessage({ type: "USER_BET", bet });
    setOurTurn(false);
    setBetInput("");
  };

  return (
    <Stack
      spacing={2}
      sx={{ maxWidth: 600, margin: "auto", textAlign: "center" }}
    >
      <h2>Game Table</h2>
      <p>Stage: {gameState.stage}</p>
      <p>Pot: {gameState.pot}</p>
      {/* Display public cards, etc. */}
      {ourTurn && (
        <Stack direction="row" spacing={1} justifyContent="center">
          <TextField
            label="Bet Amount"
            type="number"
            value={betInput}
            onChange={(e) => setBetInput(e.target.value)}
          />
          <Button variant="contained" onClick={handleBet}>
            Bet
          </Button>
        </Stack>
      )}
    </Stack>
  );
};
