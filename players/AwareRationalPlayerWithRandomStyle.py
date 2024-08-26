import numpy as np
from PlayerABC import Player
from State import State
from players.AwareRationalPlayer import AwareRationalPlayer


class AwareRationalPlayerWithRandomStyle(Player):
    def __init__(self, name="Chrism", switch_freq=0.1):
        self.name = name
        self.switch_freq = switch_freq
        self.player = AwareRationalPlayer(
            self.name,
            randomness=np.random.uniform(0, 1),
            aggression_sensitivity=np.random.uniform(0, 2),
        )

    def modify_player(self):
        self.player.randomness = np.random.uniform(0, 1)
        self.player.aggression_sensitivity = np.random.uniform(0, 2)

    def play(self, state: State) -> int:
        if np.random.rand() < self.switch_freq:
            self.modify_player()
        self.player.hand = self.hand
        self.player.index = self.index
        return self.player.play(state)

    def observe_bet(self, from_state: State, bet: int):
        return self.player.observe_bet(from_state, bet)

    def round_over(self, state: State):
        return self.player.round_over(state)
