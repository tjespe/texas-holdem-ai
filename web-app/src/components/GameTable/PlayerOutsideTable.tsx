import { Stack, Tooltip, Typography } from "@mui/material";
import { GameState, Player } from "../../hooks/useGameWebSocket";
import { CoinStack } from "./CoinStack";
import { TooltipIfTruncated } from "../TooltipIfTruncated";
import { ComponentProps } from "react";

interface Props extends ComponentProps<typeof Stack> {
  gameState: GameState;
  player: Player;
}

export const PlayerOutsideTable: React.FC<Props> = ({
  player,
  gameState,
  ...props
}) => {
  const folded = gameState.player_is_folded[player.index];
  const turn = gameState.current_player_i;
  const stack = gameState.player_piles[player.index];

  return (
    <Stack
      {...props}
      direction="column"
      alignItems="center"
      sx={{
        ...props.sx,
        opacity: folded ? 0.5 : 1,
        color:
          !gameState.is_terminal && player.index === turn ? "gold" : "inherit",
        flexShrink: 1,
        flexGrow: 0,
      }}
      pl={2}
      pr={2}
    >
      <Tooltip title={`${player.name} has ${stack} in their stack`}>
        <CoinStack chips={stack} />
      </Tooltip>
      <Typography
        variant="body1"
        sx={{
          textWrap: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
        maxWidth="100%"
      >
        <TooltipIfTruncated>{player.name}</TooltipIfTruncated>
      </Typography>
    </Stack>
  );
};
