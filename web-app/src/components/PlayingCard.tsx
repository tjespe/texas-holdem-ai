import { Card } from "@mui/material";
import { getRank, getSuit } from "../lib/cards";

interface Props {
  card: number;
}

export function PlayingCard({ card }: Props) {
  return (
    <Card
      sx={{
        width: 50,
        height: 70,
        borderRadius: "10px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "1.5rem",
        color: ["♠", "♣"].includes(getSuit(card)) ? "black" : "red",
        padding: 1,
      }}
    >
      {getRank(card)}
      {getSuit(card)}
    </Card>
  );
}
