import numpy as np
from PlayerABC import Player
from State import State
from helpers import get_random_betting_distribution_for_state

class RandomPlayer(Player):
    def __init__(self, name: str = "Rando"):
        super().__init__()
        self.name = name

    def get_distribution(self, state: State):
        """
        Generate a general uninformed distribution for betting.
        """
        return get_random_betting_distribution_for_state(state)

    def play(self, state: State) -> int:
        distribution = self.get_distribution(state)
        return np.random.choice(len(distribution), p=distribution)

    def __repr__(self) -> str:
        return f"RandomPlayer('{self.name}')"
