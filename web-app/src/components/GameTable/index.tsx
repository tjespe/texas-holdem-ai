import {
  Box,
  Button,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuthContext } from "../../contexts/AuthContext";
import {
  GameState,
  Player,
  ShowDownHand,
  useGameWebSocket,
} from "../../hooks/useGameWebSocket";
import { PlayingCard } from "../PlayingCard";
import { PlayerOnTable } from "./PlayerOnTable";
import { PlayerOutsideTable } from "./PlayerOutsideTable";
import { CoinStack } from "./CoinStack";
import { PlayerResult } from "./PlayerResult";

export const GameTable: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [betInput, setBetInput] = useState("");
  const [ourTurn, setOurTurn] = useState(false);
  const [players, setPlayers] = useState<Player[]>([]);
  const [hand, setHand] = useState<number[] | null>(null);
  const [allHands, setAllHands] = useState<(ShowDownHand | null)[] | undefined>(
    undefined
  );
  const [winners, setWinners] = useState<number[] | undefined>();
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
          setGetReadyRequested(false);
          setAllHands(undefined);
          setWinners(undefined);
          break;
        case "OBSERVE_BET":
          setGameState(msg.state);
          setGetReadyRequested(false);
          setOurTurn(false);
          setError(null);
          setAllHands(undefined);
          setWinners(undefined);
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
    [ourIndex, sendMessage]
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

  const opponents = useMemo(() => {
    const afterUs = players.slice(ourIndex + 1);
    const beforeUs = players.slice(0, ourIndex);
    return [...afterUs, ...beforeUs];
  }, [players, ourIndex]);

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
        if (getReadyRequested) {
          ready();
        }
      };
      window.addEventListener("keypress", listener);
      return () => window.removeEventListener("keypress", listener);
    },
    [ourTurn, callAmount, handleBet, getReadyRequested, ready]
  );

  if (!gameState) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Stack
      spacing={2}
      sx={{ maxWidth: "800px", margin: "auto", textAlign: "center", py: 2 }}
    >
      {error && <Typography color="error">{error}</Typography>}
      {/* Poker table with public cards and pot */}
      <Stack direction="row" width="100%" justifyContent="center">
        <Stack direction="column" width="100%" maxWidth={600} spacing={1}>
          <Stack direction="row" justifyContent="space-evenly" width="100%">
            {opponents.map((player) => (
              <PlayerOutsideTable
                key={player.index}
                player={player}
                gameState={gameState}
                maxWidth="100%"
                minWidth={0}
                width={100 / opponents.length + "%"}
              />
            ))}
          </Stack>
          <Stack direction="row" width="100%" justifyContent="space-evenly">
            {opponents.map((player) => (
              <PlayerResult
                key={player.index}
                player={player}
                gameState={gameState}
                showdownWinners={winners}
              />
            ))}
          </Stack>
          <Box
            bgcolor="primary.main"
            width="100%"
            sx={{
              borderRadius: "20px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.5)",
              margin: "auto",
            }}
            maxWidth="100%"
            pt={2}
            pb={2}
          >
            <Stack
              direction="column"
              alignItems="center"
              spacing={2}
              width="100%"
            >
              <Stack direction="row" justifyContent="space-evenly" width="100%">
                {opponents.map((player) => (
                  <PlayerOnTable
                    key={player.index}
                    player={player}
                    gameState={gameState}
                    hand={allHands?.[player.index]}
                  />
                ))}
              </Stack>
              <Stack direction="row" spacing={1} sx={{ py: 1 }}>
                <Stack direction="column" pr={2}>
                  <Typography variant="h6">Pot</Typography>
                  <CoinStack large chips={gameState.pot} />
                </Stack>
                {gameState?.public_cards.map((card) => (
                  <PlayingCard card={card} key={card} />
                ))}
              </Stack>
              <Stack direction="row" justifyContent="center" width="100%">
                <PlayerOnTable
                  player={players[ourIndex]}
                  gameState={gameState}
                  // No need to display the hand here since it's shown below
                  hand={null}
                />
              </Stack>
            </Stack>
          </Box>
        </Stack>
      </Stack>

      {/* Your hand and stack */}
      <Stack direction="row" justifyContent="center" spacing={4}>
        {hand && (
          <Stack>
            <Typography variant="h6">Your Hand</Typography>
            <Stack direction="row" justifyContent="center" spacing={1}>
              {hand.map((card) => (
                <PlayingCard width={30} card={card} key={card} />
              ))}
            </Stack>
            {allHands?.[ourIndex] && (
              <Typography variant="body2">{allHands[ourIndex].rank}</Typography>
            )}
          </Stack>
        )}
        <Stack>
          <Typography variant="h6">Your Stack</Typography>
          <CoinStack large chips={gameState.player_piles[ourIndex]} />
        </Stack>
      </Stack>

      {/* Our result */}
      {gameState?.is_terminal && (
        <Stack>
          {winners ? (
            winners.includes(ourIndex) ? (
              <Typography variant="h6">You Won!</Typography>
            ) : (
              <Typography variant="h6">You Lost!</Typography>
            )
          ) : gameState.player_is_folded[ourIndex] ? (
            <Typography variant="h6">You Folded</Typography>
          ) : (
            <Typography variant="h6">You Won!</Typography>
          )}
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
            <Tooltip title="Press any key to continue">
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
