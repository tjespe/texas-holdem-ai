import numpy as np
from cpp_poker.cpp_poker import CardCollection, CheatSheet, Oracle
from PlayerABC import Player
from helpers import get_random_betting_distribution


class RationalPlayer(Player):
    """
    This player never bets more than what is rational in terms of expected value,
    assuming that the other players are rational as well (which is not a good
    assumption in practice).
    """

    def __init__(self, name: str = "Rasmus"):
        super().__init__()
        self.name = name

    def play(self, state) -> int:
        current_player_i = state.current_player_i
        if state.player_is_folded[current_player_i]:
            return 0
        current_bet = state.bet_in_stage[current_player_i]
        call_bet = max(state.bet_in_stage) - current_bet
        winning_prob = CheatSheet.get_winning_probability(
            CardCollection(self.hand),
            CardCollection(state.public_cards),
            state.player_is_active.sum(),
        )
        rational_max = winning_prob * state.pot
        avg_forced_loss = (state.big_blind + state.small_blind) / state.n_players
        rational_max += avg_forced_loss
        if call_bet > rational_max:
            return 0

        max_allowed_bet = Oracle.get_max_bet_allowed(
            state.player_has_played,
            state.current_player_i,
            state.bet_in_stage,
            state.player_piles,
            state.player_is_active,
        )
        max_bet = min(int(rational_max), max_allowed_bet)

        # Return random int between call_bet and rational_max
        distribution = get_random_betting_distribution(
            call_bet, max_bet, state.big_blind, always_add_fold_chance=False
        )
        return np.random.choice(len(distribution), p=distribution)
