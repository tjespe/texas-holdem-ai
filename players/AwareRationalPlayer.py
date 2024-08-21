import math
import numpy as np
from State import State
from cpp_poker.cpp_poker import CardCollection, CheatSheet
from PlayerABC import Player
from helpers import get_random_betting_distribution


class AwareRationalPlayer(Player):
    """
    Similar to RationalPlayer, but bases winning probability on a combination of
    cards and bets from other players.
    """

    def __init__(self, name: str = "Rasmus"):
        super().__init__()
        self.name = name
        self.raises_per_player = None
        self.implied_winning_probs = None

    def _ensure_vars_initialized(self, n_players):
        if self.raises_per_player is None:
            # Start with a small number (1) to avoid division by zero
            self.raises_per_player = np.ones(n_players)
        if self.implied_winning_probs is None:
            self.implied_winning_probs = np.full(n_players, fill_value=np.nan)

    def observe_bet(self, from_state: State, bet: int):
        self._ensure_vars_initialized(from_state.n_players)
        player_i = from_state.current_player_i
        call_bet = max(from_state.bet_in_stage) - from_state.bet_in_stage[player_i]
        if bet > call_bet:
            self.raises_per_player[player_i] += call_bet - bet
        implied_winning_prob = bet / from_state.pot
        if self.implied_winning_probs[player_i]:
            self.implied_winning_probs[player_i] = 0
        self.implied_winning_probs[player_i] = max(
            self.implied_winning_probs[player_i], implied_winning_prob
        )

    def get_winning_prob_based_on_raises(self, state: State):
        # Simple model assuming a 1-1 relationship between raises and winning probability
        self._ensure_vars_initialized(state.n_players)
        winning_probs = self.raises_per_player / self.raises_per_player.sum()
        return winning_probs[state.current_player_i]

    def get_implied_winning_prob(self, state: State):
        self._ensure_vars_initialized(state.n_players)
        winning_probs = self.implied_winning_probs / np.nansum(
            self.implied_winning_probs
        )
        return winning_probs[state.current_player_i]

    def play(self, state) -> int:
        current_player_i = state.current_player_i
        if state.player_is_folded[current_player_i]:
            return 0
        current_bet = state.bet_in_stage[current_player_i]
        call_bet = max(state.bet_in_stage) - current_bet
        card_winning_prob = CheatSheet.get_winning_probability(
            CardCollection(self.hand),
            CardCollection(state.public_cards),
            state.player_is_active.sum(),
        )
        raise_based_winning_prob = self.get_winning_prob_based_on_raises(state)
        implied_winning_prob = self.get_implied_winning_prob(state)
        winning_prob = np.nanmean(
            [card_winning_prob, raise_based_winning_prob, implied_winning_prob]
        )
        rational_max = winning_prob * state.pot
        avg_forced_loss = (state.big_blind + state.small_blind) / state.n_players
        rational_max += avg_forced_loss
        if call_bet > rational_max:
            return 0

        if math.isinf(rational_max):
            # Don't know why this happens, but it does
            rational_max = 0

        # Return random int between call_bet and rational_max
        distribution = get_random_betting_distribution(
            call_bet, int(rational_max), state.big_blind, always_add_fold_chance=False
        )
        return np.random.choice(len(distribution), p=distribution)
