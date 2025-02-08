import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useRef, useState } from "react";
import { useAuthContext } from "../../contexts/AuthContext";
import { ShowDownHand, useGameWebSocket } from "../../hooks/useGameWebSocket";
import { GameState, Player } from "../../schemas/messages";
import { PlayingCard } from "../PlayingCard";

export const GameTable: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [betInput, setBetInput] = useState("");
  const [ourTurn, setOurTurn] = useState(false);
  const [players, setPlayers] = useState<Player[]>([]);
  const [hand, setHand] = useState<number[]>([]);
  const [turn, setTurn] = useState(0);
  const [allHands, setAllHands] = useState<(ShowDownHand | null)[] | undefined>(
    undefined
  );
  const [winners, setWinners] = useState<number[] | undefined>([]);
  const { username } = useAuthContext();
  const ourIndex = players.findIndex((player) => player.name === username);
  const [error, setError] = useState<string | null>(null);
  const [getReadyRequested, setGetReadyRequested] = useState(false);
  const raiseInputRef = useRef<HTMLInputElement>(null);

  const { sendMessage } = useGameWebSocket(
    useCallback((msg) => {
      switch (msg.type) {
        case "PLAY_REQUEST":
          setGameState(msg.state);
          setHand(msg.hand);
          setOurTurn(true);
          setTurn(msg.state.current_player_i);
          setGetReadyRequested(false);
          break;
        case "OBSERVE_BET":
          setGameState(msg.state);
          setGetReadyRequested(false);
          setOurTurn(false);
          setTurn((prev) => {
            const numPlayers = msg.state.player_piles.length;
            let nextPlayer = (msg.player_index + 1) % numPlayers;
            while (msg.state.player_is_folded[nextPlayer]) {
              nextPlayer = (nextPlayer + 1) % numPlayers;
            }
            if (Number.isNaN(nextPlayer)) {
              console.error("Next player is NaN", msg);
              return prev;
            }
            return nextPlayer;
          });
          setError(null);
          break;
        case "ROUND_OVER":
          setGameState(msg.state);
          setOurTurn(false);
          setError(null);
          break;
        case "GET_TO_KNOW_EACH_OTHER":
          setPlayers(msg.players);
          break;
        case "SHOWDOWN":
          setGameState(msg.state);
          setAllHands(msg.all_hands);
          setWinners(msg.winners);
          setError(null);
          break;
        case "BET_REJECTED":
          setOurTurn(true);
          setError(msg.reason);
          setGameState(msg.from_state);
          break;
        case "GET_READY":
          setGetReadyRequested(true);
          break;
        case "GAME_OVER":
          console.log("Game over", msg);
          break;
        default:
          console.log("Unknown message type:", msg);
      }
    }, [])
  );

  const handleBet = useCallback(
    (betAmount: number) => {
      console.log("Betting", betAmount);

      sendMessage({ type: "USER_BET", bet: betAmount });
      setOurTurn(false);
      setBetInput("");
      const nextPlayer = (turn + 1) % players.length;
      if (!Number.isNaN(nextPlayer)) {
        setTurn(nextPlayer);
      }
      setGameState(
        (prev) =>
          prev && {
            ...prev,
            bet_in_stage: prev?.bet_in_stage.map((bet, i) =>
              i === ourIndex ? bet + betAmount : bet
            ),
            bet_in_game: prev?.bet_in_game.map((bet, i) =>
              i === ourIndex ? bet + betAmount : bet
            ),
            player_piles: prev?.player_piles.map((pile, i) =>
              i === ourIndex ? pile - betAmount : pile
            ),
          }
      );
    },
    [ourIndex, players.length, sendMessage, turn]
  );

  const ready = useCallback(() => {
    sendMessage({ type: "READY" });
    setGetReadyRequested(false);
  }, [sendMessage]);

  const handleRaise = (raiseTo: number) => {
    if (!gameState) return;
    handleBet(raiseTo - gameState.bet_in_stage[ourIndex]);
  };

  const highestBet = Math.max(...(gameState?.bet_in_stage || [0]));
  const ourBet = gameState?.bet_in_stage[ourIndex] || 0;

  const callAmount = highestBet - ourBet;
  const minRaise = highestBet + (gameState?.big_blind || 0);

  useEffect(
    function keyListener() {
      const listener = (e: KeyboardEvent) => {
        if (ourTurn) {
          switch (e.key.toLowerCase()) {
            case "c":
              // This can be either a call or a check, depending on if callAmount is 0 or not
              handleBet(callAmount);
              break;
            case "f":
              // Fold (only possible if callAmount is > 0)
              if (callAmount > 0) {
                handleBet(0);
              }
              break;
            default:
              break;
          }
          // Check if a number key was pressed
          if (e.key >= "0" && e.key <= "9") {
            // Set focus on the input field
            raiseInputRef.current?.focus();
          }
        }
        if (getReadyRequested && e.key === "Enter") {
          ready();
        }
      };
      window.addEventListener("keypress", listener);
      return () => window.removeEventListener("keypress", listener);
    },
    [ourTurn, callAmount, handleBet, getReadyRequested, ready]
  );

  return (
    <Stack
      spacing={2}
      sx={{ maxWidth: "800px", margin: "auto", textAlign: "center", py: 2 }}
    >
      {gameState?.is_terminal && (
        <Typography variant="h4">Round Over!</Typography>
      )}
      {error && <Typography color="error">{error}</Typography>}
      {/* Players positioned around the table */}
      <Grid container justifyContent="center" alignItems="center" spacing={2}>
        {players.map((player) => {
          const folded = gameState?.player_is_folded[player.index];
          const stack = gameState?.player_piles[player.index];
          const bet = gameState?.bet_in_stage[player.index];
          const hand = allHands && allHands[player.index];
          return (
            <Grid key={player.index} item sx={{ position: "relative" }}>
              <Card
                sx={{
                  border:
                    !gameState?.is_terminal && turn === player.index
                      ? "2px solid gold"
                      : "",
                  textAlign: "center",
                  padding: "4px",
                  position: "relative",
                }}
              >
                {folded && (
                  <Box
                    sx={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      backgroundColor: "rgba(0, 0, 0, 0.5)",
                      color: "white",
                      padding: "2px",
                      borderRadius: "0 0 4px 0",
                      width: "100%",
                      height: "100%",
                    }}
                    justifyContent="center"
                    alignContent="center"
                  >
                    <Typography
                      sx={{
                        transform: "rotate(-30deg)",
                        textShadow: "1px 1px 2px black",
                      }}
                      variant="h5"
                      color="error"
                    >
                      {stack !== undefined && stack < gameState.big_blind
                        ? "Bust"
                        : "Folded"}
                    </Typography>
                  </Box>
                )}
                <CardContent>
                  <Typography fontWeight="bold">{player.name}</Typography>
                  <Typography variant="body2">Stack: {stack} chips</Typography>
                  <Typography variant="body2">
                    Bet in {gameState?.stage}: {bet}
                  </Typography>
                  {gameState?.is_terminal && hand && (
                    <Stack direction="column" spacing={1}>
                      <Stack
                        direction="row"
                        spacing={1}
                        justifyContent="center"
                      >
                        {hand.cards?.map((card) => (
                          <PlayingCard card={card} key={card} />
                        ))}
                      </Stack>
                      <Typography variant="caption">{hand.rank}</Typography>
                      <Typography variant="h6">
                        {winners?.includes(player.index) ? "Winner!" : "Loser"}
                      </Typography>
                    </Stack>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Poker table with public cards and pot */}
      <Stack direction="row" width="100%">
        <Box
          height={150}
          maxWidth={500}
          width="100%"
          bgcolor="primary.main"
          sx={{
            borderRadius: "20px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.5)",
            margin: "auto",
          }}
        >
          <Typography variant="h6" color="white">
            Pot: {gameState?.pot} chips
          </Typography>
          <Stack direction="row" spacing={1} sx={{ py: 1 }}>
            {gameState?.public_cards.map((card) => (
              <PlayingCard card={card} key={card} />
            ))}
          </Stack>
        </Box>
      </Stack>

      {/* Your hand */}
      {ourTurn && !gameState?.is_terminal && (
        <Stack>
          <Typography variant="h6">Your Hand</Typography>
          <Stack direction="row" justifyContent="center" spacing={1}>
            {hand.map((card) => (
              <PlayingCard card={card} key={card} />
            ))}
          </Stack>
        </Stack>
      )}

      {/* Betting Controls */}
      {ourTurn && !gameState?.is_terminal && (
        <Stack spacing={1}>
          <Typography variant="h6">Your Move</Typography>
          <Stack direction="row" justifyContent="center" spacing={2}>
            {/* Check */}
            {callAmount === 0 ? (
              <Tooltip title="Check (C)">
                <Button variant="contained" onClick={() => handleBet(0)}>
                  Check
                </Button>
              </Tooltip>
            ) : (
              <Tooltip title="Fold (F)">
                <Button
                  variant="outlined"
                  onClick={() => handleBet(0)}
                  color="error"
                >
                  Fold
                </Button>
              </Tooltip>
            )}

            {/* Call (if available) */}
            {callAmount > 0 && (
              <Tooltip title="Call (C)">
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => handleBet(callAmount)}
                >
                  Call {highestBet}
                  {gameState && gameState.bet_in_stage[ourIndex] > 0 && (
                    <Typography variant="body2" pl={1}>
                      (+{callAmount})
                    </Typography>
                  )}
                </Button>
              </Tooltip>
            )}

            {/* Raise */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
              }}
            >
              <Stack direction="row" justifyContent="center" spacing={2}>
                <TextField
                  label="Raise to"
                  type="number"
                  value={betInput}
                  onChange={(e) => setBetInput(e.target.value)}
                  sx={{ width: "100px" }}
                  inputRef={raiseInputRef}
                />
                <Button
                  variant="contained"
                  color="secondary"
                  onClick={() => handleRaise(parseInt(betInput, 10))}
                  disabled={!betInput || parseInt(betInput, 10) < minRaise}
                  type="submit"
                >
                  Raise
                </Button>
              </Stack>
            </form>
          </Stack>
        </Stack>
      )}

      {getReadyRequested && (
        <Stack>
          <Stack direction="row" justifyContent="center" spacing={1}>
            <Tooltip title="Continue to next round (Enter)">
              <Button
                variant="contained"
                color="primary"
                onClick={() => ready()}
              >
                Continue
              </Button>
            </Tooltip>
          </Stack>
        </Stack>
      )}
    </Stack>
  );
};
