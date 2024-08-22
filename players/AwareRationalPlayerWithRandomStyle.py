import numpy as np
from PlayerABC import Player
from State import State
from players.AwareRationalPlayer import AwareRationalPlayer

stats_file = open("stats/player_style_stats.csv", "a")


class AwareRationalPlayerWithRandomStyle(Player):
    def __init__(self, name="Chrism", switch_freq=0.1):
        self.name = name
        self.switch_freq = switch_freq
        self.player = AwareRationalPlayer(
            self.name,
            randomness=np.random.uniform(0, 1),
            aggression_sensitivity=np.random.uniform(0, 2),
        )
        self.rounds_played = 0
        self.rel_pile_at_beginning = None

    def modify_player(self, rel_pile):
        win = rel_pile - self.rel_pile_at_beginning
        stats_file.write(
            ",".join(
                str(n)
                for n in [
                    self.player.randomness,
                    self.player.aggression_sensitivity,
                    self.rounds_played,
                    win,
                    win / (self.rounds_played or 1),
                ]
            )
            + "\n"
        )
        self.player.randomness = np.random.uniform(0, 1)
        self.player.aggression_sensitivity = np.random.uniform(0, 2)
        self.rel_pile_at_beginning = rel_pile

    def play(self, state: State) -> int:
        rel_pile = state.player_piles[state.current_player_i] / state.big_blind
        if self.rounds_played == 0:
            self.rel_pile_at_beginning = rel_pile
        if np.random.rand() < self.switch_freq:
            self.modify_player(rel_pile)
        self.player.hand = self.hand
        self.player.index = self.index
        return self.player.play(state)

    def observe_bet(self, from_state: State, bet: int):
        return self.player.observe_bet(from_state, bet)

    def round_over(self, state: State):
        self.rounds_played += 1
        return self.player.round_over(state)
