from typing import Iterable


class Card:
    SUITS = ["♥", "♦", "♣", "♠"]
    VALUES = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

    def __init__(self, rank: int, suit: int):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return Card.SUITS[self.suit] + " " + Card.VALUES[self.rank]

    def get_cli_repr(self):
        return """
┌───────┐
│{}     │
│       │
│   {}  │
│       │
│     {}│
└───────┘""".format(
            Card.VALUES[self.rank].ljust(2),
            Card.SUITS[self.suit].ljust(2),
            Card.VALUES[self.rank].rjust(2),
        )

    @classmethod
    def from_index(cls, i):
        suit = i // 13
        rank = i % 13
        return cls(rank, suit)

    @classmethod
    def get_cli_repr_for_cards(cls, cards: Iterable[int]):
        return "\n".join(
            [
                " ".join(parts)
                for parts in zip(
                    *[Card.from_index(c).get_cli_repr().split("\n") for c in cards]
                )
            ]
        )


if __name__ == "__main__":
    # Example: card 0 is the 2 of hearts
    print(Card.from_index(0))
    print(Card.from_index(0).get_cli_repr())
