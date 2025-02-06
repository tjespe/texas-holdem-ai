// src/components/GameTable.tsx
import { Button, Stack, TextField } from "@mui/material";
import React, { useState } from "react";
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
        // Server says it's your turn
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
        // Initial state
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

  const handleBet = () => {
    const bet = parseInt(betInput, 10) || 0;
    sendMessage({ type: "USER_BET", bet });
    setOurTurn(false);
    setBetInput("");
    setTurn((turn + 1) % players.length);
  };

  console.log({ turn });

  return (
    <Stack
      spacing={2}
      sx={{ maxWidth: 600, margin: "auto", textAlign: "center" }}
    >
      <h2>Game Table</h2>
      <p>Stage: {gameState?.stage}</p>
      <p>Pot: {gameState?.pot}</p>
      <p>Players:</p>
      <ul>
        {players.map((player) => (
          <li
            key={player.index}
            style={{ fontWeight: turn === player.index ? "bold" : "normal" }}
          >
            {player.name} ({gameState?.player_piles[player.index]} chips)
          </li>
        ))}
      </ul>
      <p>Current bets:</p>
      <ul>
        {gameState?.bet_in_game.map((bet, idx) => (
          <li key={idx}>
            {players[idx].name}: {bet}
          </li>
        ))}
      </ul>
      {/* Display public cards, etc. */}
      {ourTurn && (
        <Stack>
          <Stack>
            <p>Your hand:</p>
            <ul>
              {hand.map((card) => (
                <li key={card}>
                  {getRank(card)}
                  {getSuit(card)}
                </li>
              ))}
            </ul>
          </Stack>
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
        </Stack>
      )}
      {allHands && (
        <Stack>
          <p>Showdown!</p>
          {allHands.map((hand, idx) => (
            <Stack key={idx}>
              <p>{players[idx].name}'s hand:</p>
              <ul>
                {hand?.map((card) => (
                  <li key={card}>
                    {getRank(card)}
                    {getSuit(card)}
                  </li>
                ))}
              </ul>
            </Stack>
          ))}
        </Stack>
      )}
    </Stack>
  );
};
