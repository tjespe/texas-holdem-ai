import { Stack, Typography } from "@mui/material";
import { GameState, Player } from "../../hooks/useGameWebSocket";

interface Props {
  gameState: GameState;
  player: Player;
  showdownWinners: number[] | undefined;
}

export const PlayerResult: React.FC<Props> = ({
  player,
  gameState,
  showdownWinners,
}) => {
  const folded = gameState.player_is_folded[player.index];

  return (
    <Stack
      key={player.index}
      direction="column"
      alignItems="center"
      sx={{
        opacity: folded ? 0.5 : 1,
      }}
      spacing={1}
      minWidth={0}
      width="100%"
    >
      {showdownWinners ? (
        showdownWinners.includes(player.index) ? (
          <Typography variant="body1" fontWeight={800}>
            Winner!
          </Typography>
        ) : (
          <Typography variant="body1" fontWeight={800}>
            Loser!
          </Typography>
        )
      ) : null}
      {!showdownWinners &&
        gameState.is_terminal &&
        (gameState.player_is_folded[player.index] ? (
          <Typography variant="h6">Folded</Typography>
        ) : (
          <Typography variant="h6">Winner!</Typography>
        ))}
    </Stack>
  );
};
