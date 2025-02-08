import numpy as np
from PlayerABC import Player
from State import State
from helpers import get_random_betting_distribution_for_state
from cpp_poker.cpp_poker import Oracle


class AllInPlayer(Player):
    title = "Ballsy"

    def __init__(self, name: str = "Rando"):
        super().__init__()
        self.name = name

    def play(self, state: State) -> int:
        call_bet = max(state.bet_in_game) - state.bet_in_game[state.current_player_i]
        max_bet = Oracle.get_max_bet_allowed(
            state.player_has_played,
            state.current_player_i,
            state.bet_in_stage,
            state.player_piles,
            state.player_is_active,
        )
        min_raise = call_bet + state.big_blind
        if max_bet < min_raise:
            return call_bet
        return max_bet

    def __repr__(self) -> str:
        return f"RandomPlayer('{self.name}')"
