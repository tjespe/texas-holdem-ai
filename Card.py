from typing import Iterable, Union


class Card:
    SUITS = ["♥", "♦", "♣", "♠"]
    VALUES = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

    def __init__(self, rank: Union[int, str], suit: Union[int, str]):
        if isinstance(rank, str):
            rank = Card.VALUES.index(rank)
        if isinstance(suit, str):
            suit = Card.SUITS.index(suit)
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return Card.SUITS[self.suit] + " " + Card.VALUES[self.rank]

    def __repr__(self) -> str:
        return f"Card({self.rank}, {self.suit})"

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

    def to_index(self):
        return self.suit * 13 + self.rank

    @classmethod
    def get_rank(cls, value: str):
        return cls.VALUES.index(value)

    @classmethod
    def get_cli_repr_for_cards(cls, cards: Iterable[Union[int, "Card"]]):
        return "\n".join(
            [
                " ".join(parts)
                for parts in zip(
                    *[
                        (c if isinstance(c, Card) else Card.from_index(c))
                        .get_cli_repr()
                        .split("\n")
                        for c in cards
                    ]
                )
            ]
        )

    def __hash__(self) -> int:
        return self.to_index()

    def __gt__(self, other):
        return self.rank > other.rank

    def __lt__(self, other):
        return self.rank < other.rank

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Card):
            return False
        return self.rank == value.rank and self.suit == value.suit


if __name__ == "__main__":
    # Example: card 0 is the 2 of hearts
    print(Card.from_index(0))
    print(Card.from_index(0).get_cli_repr())
    # Example 2: card 51 is the ace of spades
    print(Card.from_index(51))
    print(Card.from_index(51).get_cli_repr())
