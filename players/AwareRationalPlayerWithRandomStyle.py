import numpy as np
from PlayerABC import Player
from State import State
from players.AwareRationalPlayer import AwareRationalPlayer

param_stats_file = open("stats/player_style_stats.csv", "a")
switch_stats_file = open("stats/switch_stats.csv", "a")

RANDO_BOUNDS = (0.0, 1.0)
AGG_SENSITIVITY_BOUNDS = (0, 2.0)


class AwareRationalPlayerWithRandomStyle(Player):
    def __init__(self, name="Chrism", switch_freq=0.1):
        self.name = name
        self.switch_freq = switch_freq
        self.player = AwareRationalPlayer(
            self.name,
            randomness=np.random.uniform(*RANDO_BOUNDS),
            aggression_sensitivity=np.random.uniform(*AGG_SENSITIVITY_BOUNDS),
        )
        self.rounds_played_since_switch = None
        self.rel_pile_at_last_switch = None
        self.rel_pile_at_round_start = None

    def modify_player(self, rel_pile):
        win = rel_pile - self.rel_pile_at_last_switch
        param_stats_file.write(
            ",".join(
                str(n)
                for n in [
                    self.player.randomness,
                    self.player.aggression_sensitivity,
                    self.rounds_played_since_switch,
                    win,
                    win / (self.rounds_played_since_switch or 1),
                ]
            )
            + "\n"
        )
        self.player.randomness = np.random.uniform(*RANDO_BOUNDS)
        self.player.aggression_sensitivity = np.random.uniform(*AGG_SENSITIVITY_BOUNDS)
        self.rel_pile_at_last_switch = rel_pile
        self.rounds_played_since_switch = 0

    def _ensure_stat_vars_initialized(self, state: State):
        if self.rounds_played_since_switch is None:
            rel_pile = state.player_piles[self.index] / state.big_blind
            self.rounds_played_since_switch = 0
            self.rel_pile_at_last_switch = rel_pile
            self.rel_pile_at_round_start = rel_pile

    def play(self, state: State) -> int:
        rel_pile = state.player_piles[self.index] / state.big_blind
        self._ensure_stat_vars_initialized(state)
        if np.random.rand() < self.switch_freq:
            self.modify_player(rel_pile)
        self.player.hand = self.hand
        self.player.index = self.index
        return self.player.play(state)

    def observe_bet(self, from_state: State, bet: int):
        return self.player.observe_bet(from_state, bet)

    def round_over(self, new_state: State):
        new_rel_pile = new_state.player_piles[self.index] / new_state.big_blind
        rel_pile_change = new_rel_pile - self.rel_pile_at_round_start
        if rel_pile_change:
            switch_stats_file.write(
                ",".join(
                    str(n) for n in [rel_pile_change, self.rounds_played_since_switch]
                )
                + "\n"
            )
        self.rel_pile_at_round_start = new_rel_pile
        self.rounds_played_since_switch += 1
        return self.player.round_over(new_state)
