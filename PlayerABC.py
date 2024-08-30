from abc import ABC, abstractmethod
from typing import Union

import numpy as np

from State import State


class Player(ABC):
    hand: Union[tuple[int, int], None]
    name: str
    index: int

    @abstractmethod
    def play(self, state: State) -> int:
        """
        Given the current state of the game, return the amount of money to bet.
        0 is treated as check/call/fold depending on the context.
        """

    def observe_bet(self, from_state: State, bet: int):
        """
        This method allows the player to observe what other players are doing.
        Every time the state changes, the game manager will call this method
        for every player.
        """
        # By default, do nothing
        pass

    def round_over(self, state: State):
        """
        This method is called when the round is over, in case the player wants
        to do something, e.g. clean up state variables.
        """
        # By default, do nothing
        pass

    def cheat(self, hands: list[tuple[int, int]]):
        """
        This method allows the player to look at the other players' hands.
        """
        # By default, do nothing
        pass
