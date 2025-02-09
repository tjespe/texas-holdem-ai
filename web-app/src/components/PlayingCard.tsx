import { Card } from "@mui/material";
import { getRank, getSuit } from "../lib/cards";

interface Props {
  card: number;
  width?: number;
}

export function PlayingCard({ card, width = 40 }: Props) {
  return (
    <Card
      sx={{
        width: width,
        height: (width * 7) / 5,
        borderRadius: "10px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: `min(${width / 1.3 + "px"}, 1.5rem)`,
        color: ["♠", "♣"].includes(getSuit(card)) ? "black" : "red",
        padding: 1,
        backgroundColor: "white",
      }}
    >
      {getRank(card)}
      {getSuit(card)}
    </Card>
  );
}
