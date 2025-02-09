import { Box, Stack, Tooltip, Typography } from "@mui/material";
import { GameState, Player, ShowDownHand } from "../../hooks/useGameWebSocket";
import { CoinStack } from "./CoinStack";
import { PlayingCard } from "../PlayingCard";

interface Props {
  player: Player;
  gameState: GameState;
  hand: ShowDownHand | null | undefined;
}

export const PlayerOnTable: React.FC<Props> = ({ player, gameState, hand }) => {
  const bet = gameState.bet_in_stage[player.index];
  const folded = gameState.player_is_folded[player.index];
  const turn = gameState.current_player_i;
  console.log("PlayerOnTable", player.name, gameState, hand);

  return (
    <Stack
      width="100%"
      key={player.index}
      direction="column"
      justifyContent="center"
      sx={{
        opacity: folded ? 0.5 : 1,
        color:
          !gameState.is_terminal && player.index === turn ? "gold" : "inherit",
      }}
    >
      {!gameState.is_terminal && (
        <Tooltip title={`${player.name} has bet ${bet} in ${gameState.stage}`}>
          <Box>
            <CoinStack chips={bet} />
          </Box>
        </Tooltip>
      )}
      {hand && (
        <Stack direction="column" alignItems="center">
          <Typography variant="body2">{hand.rank}</Typography>
          <Stack direction="row" spacing={1}>
            {hand.cards.map((card) => (
              <PlayingCard width={20} card={card} key={card} />
            ))}
          </Stack>
        </Stack>
      )}
    </Stack>
  );
};
