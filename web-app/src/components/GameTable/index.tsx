import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useCallback, useState } from "react";
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
  const [terminalState, setTerminalState] = useState<GameState | null>();
  const [error, setError] = useState<string | null>(null);

  const { sendMessage } = useGameWebSocket(
    useCallback((msg) => {
      switch (msg.type) {
        case "PLAY_REQUEST":
          setGameState(msg.state);
          setHand(msg.hand);
          setOurTurn(true);
          break;
        case "OBSERVE_BET":
          setGameState(msg.state);
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
          break;
        case "ROUND_OVER":
          setGameState(msg.state);
          setTerminalState(msg.state);
          setOurTurn(false);
          break;
        case "GET_TO_KNOW_EACH_OTHER":
          setPlayers(msg.players);
          break;
        case "SHOWDOWN":
          setGameState(msg.state);
          setTerminalState(msg.state);
          setAllHands(msg.all_hands);
          setWinners(msg.winners);
          break;
        case "BET_REJECTED":
          setOurTurn(true);
          setError(msg.message);
          setGameState(msg.from_state);
          break;
        default:
          console.log("Unknown message type:", msg);
      }
    }, [])
  );

  const handleBet = (betAmount: number) => {
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
  };

  const handleRaise = (raiseTo: number) => {
    console.log("Raising to", raiseTo);
    handleBet(raiseTo - callAmount);
  };

  const highestBet = Math.max(...(gameState?.bet_in_stage || [0]));
  const ourBet = gameState?.bet_in_stage[ourIndex] || 0;

  const callAmount = highestBet - ourBet;
  const minRaise = highestBet + (gameState?.big_blind || 0);

  const displayState = terminalState?.is_terminal ? terminalState : gameState;

  console.log(turn);

  return (
    <Stack
      spacing={2}
      sx={{ maxWidth: "800px", margin: "auto", textAlign: "center", py: 2 }}
    >
      {displayState?.is_terminal && (
        <Typography variant="h4">Round Over!</Typography>
      )}
      {error && <Typography color="error">{error}</Typography>}
      {/* Players positioned around the table */}
      <Grid container justifyContent="center" alignItems="center" spacing={2}>
        {players.map((player) => {
          const folded = displayState?.player_is_folded[player.index];
          const stack = displayState?.player_piles[player.index];
          const bet = displayState?.bet_in_stage[player.index];
          const hand = allHands && allHands[player.index];
          return (
            <Grid key={player.index} item sx={{ position: "relative" }}>
              <Card
                sx={{
                  backgroundColor: folded ? "#444" : "#222",
                  border:
                    !terminalState && turn === player.index
                      ? "2px solid gold"
                      : "1px solid #666",
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
                      {stack !== undefined && stack < displayState.big_blind
                        ? "Bust"
                        : "Folded"}
                    </Typography>
                  </Box>
                )}
                <CardContent>
                  <Typography fontWeight="bold">{player.name}</Typography>
                  <Typography variant="body2">Stack: {stack} chips</Typography>
                  <Typography variant="body2">
                    Bet in {displayState?.stage}: {bet}
                  </Typography>
                  {terminalState && hand && (
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
            Pot: {displayState?.pot} chips
          </Typography>
          <Stack direction="row" spacing={1} sx={{ py: 1 }}>
            {displayState?.public_cards.map((card) => (
              <PlayingCard card={card} key={card} />
            ))}
          </Stack>
        </Box>
      </Stack>

      {/* Your hand */}
      {ourTurn && !displayState?.is_terminal && (
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
      {ourTurn && !displayState?.is_terminal && (
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
              onClick={() => handleRaise(parseInt(betInput, 10))}
              disabled={!betInput || parseInt(betInput, 10) < minRaise}
            >
              Raise
            </Button>
          </Stack>
        </Stack>
      )}

      {displayState?.is_terminal && (
        <Stack>
          <Stack direction="row" justifyContent="center" spacing={1}>
            <Button
              variant="contained"
              color="primary"
              onClick={() => setTerminalState(null)}
            >
              Continue
            </Button>
          </Stack>
        </Stack>
      )}
    </Stack>
  );
};
