export const getSuit = (card: number) => {
  const suits = ["♠", "♣", "♦", "♥"];
  return suits[Math.floor(card / 13)];
};

export const getRank = (card: number) => {
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
