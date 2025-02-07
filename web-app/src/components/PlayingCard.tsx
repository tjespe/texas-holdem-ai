import { Box } from "@mui/material";
import { getRank, getSuit } from "../lib/cards";

interface Props {
  card: number;
}

export function PlayingCard({ card }: Props) {
  return (
    <Box
      sx={{
        width: 50,
        height: 70,
        backgroundColor: "#fff",
        borderRadius: "10px",
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
  );
}
