from abc import ABC, abstractmethod
from typing import Union

import numpy as np

from State import State


class Player(ABC):
    hand: Union[tuple[int, int], None]

    @abstractmethod
    def play(self, state: State) -> int:
        """
        Given the current state of the game, return the amount of money to bet.
        0 is treated as check/call/fold depending on the context.
        """
