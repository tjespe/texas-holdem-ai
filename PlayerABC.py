from abc import ABC, abstractmethod

import numpy as np

from State import State


class Player(ABC):
    @abstractmethod
    def play(self, state: State) -> int:
        """
        Given the current state of the game, return the amount of money to bet.
        0 is treated as check/call/fold depending on the context.
        """
