import pandas as pd
from typing import Tuple
import numpy as np
from typing import Tuple
import numpy as np

from Card import Card


class State:
    # The public cards on the table
    public_cards: Tuple[int]

    # The amount of money each player has
    player_piles: Tuple[int]

    # The total amount of money in the pot
    pot: int

    # The index of the player whose turn it is
    current_player_i: int

    # The bets from each player since the last deal
    current_bets: Tuple[int]

    # Whether or not each player has had a turn in the current round
    player_has_played: Tuple[bool]

    # Players who have folded
    folded_players: Tuple[bool]

    # The player who made the first bet in the current round (under the gun-player)
    first_better_i: int

    # Number of players (for vectorization)
    n_players: int

    def __init__(
        self,
        public_cards: Tuple[int],
        player_piles: Tuple[int],
        pot: int,
        current_player_i: int,
        current_bets: Tuple[int],
        player_has_played: Tuple[bool],
        folded_players: Tuple[bool],
        first_better_i: int,
    ):
        self.public_cards = public_cards
        self.player_piles = player_piles
        self.pot = pot
        self.current_player_i = current_player_i
        self.current_bets = current_bets
        self.player_has_played = player_has_played
        self.folded_players = folded_players
        self.first_better_i = first_better_i
        self.n_players = len(player_piles)
        assert len(folded_players) == len(player_piles)
        assert len(current_bets) <= len(player_piles)

    def __eq__(self, other):
        return (
            self.public_cards == other.public_cards
            and self.player_piles == other.player_piles
            and self.pot == other.pot
            and self.current_player_i == other.current_player_i
            and self.current_bets == other.current_bets
            and self.player_has_played == other.player_has_played
            and self.folded_players == other.folded_players
            and self.first_better_i == other.first_better_i
        )

    @property
    def next_player(self):
        return (self.current_player_i + 1) % len(self.player_piles)

    def to_array(self):
        if len(self.player_piles) > 9:
            raise ValueError("Too many players")
        if len(self.public_cards) > 5:
            raise ValueError("Too many public cards")
        arr = np.full(
            # Max. 5 public cards
            5
            # Max 9 players
            + 9
            # Pot
            + 1
            # Current player index
            + 1
            # Current bets
            + 9
            # Folded players
            + 9
            # First better index
            + 1
            # Number of players
            + 1,
            np.nan,
        )
        arr[: len(self.public_cards)] = self.public_cards
        arr[5 : 5 + len(self.player_piles)] = self.player_piles
        arr[5 + 9] = self.pot
        arr[5 + 9 + 1] = self.current_player_i
        arr[5 + 9 + 1 + 1 : 5 + 9 + 1 + 1 + len(self.current_bets)] = self.current_bets
        arr[5 + 9 + 1 + 1 + 9 : 5 + 9 + 1 + 1 + 9 + len(self.folded_players)] = (
            self.folded_players
        )
        arr[5 + 9 + 1 + 1 + 9 + 9] = self.first_better_i
        arr[5 + 9 + 1 + 1 + 9 + 9 + 1] = self.n_players
        return arr

    @classmethod
    def from_array(cls, arr):
        n_players = int(arr[5 + 9 + 1 + 1 + 9 + 9 + 1])
        public_cards = tuple(arr[:5])
        player_piles = tuple(arr[5 : 5 + n_players])
        pot = int(arr[5 + 9])
        current_player_i = int(arr[5 + 9 + 1])
        first_better_i = int(arr[5 + 9 + 1 + 1 + 9 + 9])
        num_bets_placed = (current_player_i - first_better_i) % n_players
        current_bets = arr[5 + 9 + 1 + 1 : 5 + 9 + 1 + 1 + num_bets_placed]
        current_bets = tuple(np.where(np.isnan(current_bets), None, current_bets))
        folded_players = tuple(arr[5 + 9 + 1 + 1 + 9 : 5 + 9 + 1 + 1 + 9 + n_players])
        return cls(
            public_cards=public_cards,
            player_piles=player_piles,
            pot=pot,
            current_player_i=current_player_i,
            current_bets=current_bets,
            folded_players=folded_players,
            first_better_i=first_better_i,
        )

    @classmethod
    def generate_root_state(
        cls, n_players: int, pile_size: int = 100, first_better_i: int = 0
    ):
        return cls(
            public_cards=(),
            player_piles=tuple(pile_size for _ in range(n_players)),
            pot=0,
            current_player_i=first_better_i,
            current_bets=tuple(0 for _ in range(n_players)),
            folded_players=tuple(False for _ in range(n_players)),
            first_better_i=first_better_i,
            player_has_played=tuple(False for _ in range(n_players)),
        )

    def get_cli_repr(self):
        cards = "\n".join(
            [
                " ".join(parts)
                for parts in zip(
                    *[
                        Card.from_index(c).get_cli_repr().split("\n")
                        for c in self.public_cards
                    ]
                )
            ]
        )
        player_status = pd.DataFrame(
            {
                "Player": range(self.n_players),
                "Pile": self.player_piles,
                "Bet": self.current_bets,
                "Played": self.player_has_played,
                "Folded": self.folded_players,
            }
        ).set_index("Player")
        return f"""
Pot: {self.pot}
Table: {cards}

{player_status}

* = Current player
"""
