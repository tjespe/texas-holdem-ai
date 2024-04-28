import pandas as pd
from typing import Literal, Tuple, Union
import numpy as np
from typing import Tuple
import numpy as np
from tabulate import tabulate

from cpp_poker.cpp_poker import TerminalColors, Card


class State:
    # The public cards on the table
    public_cards: Tuple[int]

    # The amount of money each player has
    player_piles: Tuple[int]

    # The index of the player whose turn it is
    current_player_i: int

    # The bets from each player since the last deal
    current_bets: Tuple[int]

    # The amount of money each player has bet in the current round
    bet_in_round: Tuple[int]

    # Whether or not each player has had a turn in the current round
    player_has_played: Tuple[bool]

    # Players who have folded
    player_is_folded: Tuple[bool]

    # The player who made the first bet in the current round (under the gun-player)
    _first_better_i: int

    # The big blind amount
    big_blind: int

    # Number of players (for vectorization)
    n_players: int

    def __init__(
        self,
        public_cards: Tuple[int],
        player_piles: Tuple[int],
        current_player_i: int,
        current_bets: Tuple[int],
        bet_in_round: Tuple[int],
        player_has_played: Tuple[bool],
        folded_players: Tuple[bool],
        first_better_i: int,
        big_blind: int,
    ):
        self.public_cards = public_cards
        self.player_piles = player_piles
        self.current_player_i = current_player_i
        self.current_bets = current_bets
        self.bet_in_round = bet_in_round
        self.player_has_played = player_has_played
        self.player_is_folded = folded_players
        self._first_better_i = first_better_i
        self.n_players = len(player_piles)
        self.big_blind = big_blind
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
            and self.player_is_folded == other.folded_players
            and self.first_better_i == other.first_better_i
        )

    StageType = Union[
        Literal["preflop"],
        Literal["flop"],
        Literal["turn"],
        Literal["river"],
        Literal["terminal"],
    ]

    @property
    def stage(self) -> StageType:
        if self.is_terminal:
            return "terminal"
        if len(self.public_cards) == 0:
            return "preflop"
        if len(self.public_cards) == 3:
            return "flop"
        if len(self.public_cards) == 4:
            return "turn"
        if len(self.public_cards) == 5:
            return "river"
        raise ValueError("Invalid number of public cards")

    @property
    def pot(self):
        return sum(self.bet_in_round)
    
    @property
    def game_size(self):
        return sum(self.player_piles) + self.pot

    @property
    def previous_player_i(self):
        i = (self.current_player_i - 1) % self.n_players
        while not self.player_is_active[i]:
            i = (i - 1) % self.n_players
        return i

    @property
    def next_player(self):
        i = (self.current_player_i + 1) % self.n_players
        while not self.player_is_active[i]:
            i = (i + 1) % self.n_players
        return i

    @property
    def first_better_i(self):
        i = self._first_better_i
        while not self.player_is_active[i]:
            i = (i + 1) % self.n_players
        return i

    @property
    def is_terminal(self):
        player_is_active = ~np.array(self.player_is_folded)
        if np.sum(player_is_active) == 1:
            # Only one player left, no more decisions to be made
            return True
        if self.all_players_are_done and len(self.public_cards) == 5:
            # All players have played and all cards are on the table
            return True
        return False

    @property
    def player_is_active(self):
        return ~np.array(self.player_is_folded)

    @property
    def all_players_are_done(self):
        """
        Checks if the table is ready for more cards.
        This is the case when all players have had their turn, and the bets of the non-folded players are equal.
        """
        return (
            np.all(np.array(self.player_has_played)[self.player_is_active])
            and len(set(np.array(self.current_bets)[self.player_is_active])) == 1
        )

    @property
    def small_blind(self):
        return self.big_blind // 2

    def get_cli_repr(self):
        cards = (
            Card.get_cli_repr_for_cards(self.public_cards)
            if self.public_cards
            else "No cards"
        )
        player_status = pd.DataFrame(
            {
                "Player": [
                    (
                        TerminalColors.FOLDED
                        if self.player_is_folded[i]
                        else TerminalColors.DEFAULT
                    )
                    + str(i)
                    + ("*" if i == self.current_player_i else "")
                    for i in range(self.n_players)
                ],
                "Pile": self.player_piles,
                "Bet this round": self.bet_in_round,
                "Bet since last deal": self.current_bets,
                "Folded": self.player_is_folded,
            }
        ).set_index("Player")
        player_status_string = tabulate(player_status, headers="keys", tablefmt="psql")
        return f"""
Pot: {self.pot}
Table:
{cards}

{player_status_string}{TerminalColors.DEFAULT}
* = Current player
"""
