import math
import numpy as np
from State import State
from cpp_poker.cpp_poker import CardCollection, CheatSheet, Oracle
from PlayerABC import Player
from helpers import get_random_betting_distribution
from players.RandomPlayer import RandomPlayer


def debug_print(*args, **kwargs):
    return
    print(*args, **kwargs)


class AwareRationalPlayer(Player):
    """
    Similar to RationalPlayer, but bases winning probability on a combination of
    cards and bets from other players.
    """

    def __init__(self, name: str = "Rasmus", randomness=0.1):
        super().__init__()
        self.name = name
        self.raises_per_player = None
        self.implied_winning_probs = None
        self.randomness = randomness

    def _ensure_vars_initialized(self, n_players):
        if self.raises_per_player is None:
            # Start with a small number (1) to avoid division by zero
            self.raises_per_player = np.ones(n_players)
        if self.implied_winning_probs is None:
            self.implied_winning_probs = np.full(n_players, fill_value=np.nan)

    def round_over(self, state: State):
        self.raises_per_player = None
        self.implied_winning_probs = None
        self._ensure_vars_initialized(state.n_players)

    def observe_bet(self, from_state: State, bet: int):
        self._ensure_vars_initialized(from_state.n_players)
        player_i = from_state.current_player_i
        call_bet = max(from_state.bet_in_stage) - from_state.bet_in_stage[player_i]
        if bet > call_bet:
            self.raises_per_player[player_i] += bet - call_bet
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
        debug_print(f"Raises per player: {self.raises_per_player}")
        debug_print(f"Raise based winning probs: {winning_probs}")
        return winning_probs[state.current_player_i]

    def get_implied_winning_prob(self, state: State):
        self._ensure_vars_initialized(state.n_players)
        winning_probs = self.implied_winning_probs / np.nansum(
            self.implied_winning_probs
        )
        return winning_probs[state.current_player_i]

    def evaluate_bluff_chance(self, self_i):
        # Attempt to calculate the chance that the other players are bluffing
        chances = []
        for player_i, implied_prob in enumerate(self.implied_winning_probs):
            if player_i == self_i:
                continue
            if np.isnan(implied_prob):
                continue
            debug_print(f"Player {player_i} has implied prob: {implied_prob}")
            # Cap probabilty at 130% to avoid too high bluff chances
            implied_prob = min(implied_prob, 1.3)
            # Estimate a 30% chance for bluff if the implied probability is 95%
            # and a 0% chance for bluff if the implied probability is 50%:
            bluff_chance = 0.67 * implied_prob - 0.33
            debug_print(f"Player {player_i} has implied prob: {implied_prob}")
            debug_print(f"Player {player_i} has bluff chance: {bluff_chance}")
            # Cap bluff chance at 0%
            bluff_chance = max(bluff_chance, 0)
            debug_print(f"Player {player_i} has bluff chance: {bluff_chance}")
            chances.append(bluff_chance)
        return np.nanmax(chances)

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
        winning_prob = np.nanmean([card_winning_prob, raise_based_winning_prob])
        # Cap winning prob at card based winning prob to avoid being fooled
        winning_prob = min(winning_prob, card_winning_prob)
        debug_print(f"Card based winning prob: {card_winning_prob}")
        debug_print(f"Raise based winning prob: {raise_based_winning_prob}")
        debug_print(f"Combined winning prob: {winning_prob}")
        rational_max = winning_prob * state.pot
        avg_forced_loss = (state.big_blind + state.small_blind) / state.n_players
        rational_max += avg_forced_loss
        if call_bet > rational_max:
            opponent_bluff_chance = self.evaluate_bluff_chance(current_player_i)
            debug_print(f"Opponent bluff chance: {opponent_bluff_chance}")
            # Randomize whether to call or fold based on bluff chance
            if np.random.rand() < opponent_bluff_chance:
                debug_print("Assuming bluff")
                return call_bet
            debug_print("Assuming rational")
            return 0

        if math.isinf(rational_max):
            # Don't know why this happens, but it does
            rational_max = 0

        max_allowed_bet = Oracle.get_max_bet_allowed(
            state.player_has_played,
            state.current_player_i,
            state.bet_in_stage,
            state.player_piles,
            state.player_is_active,
        )
        max_bet = min(int(rational_max), max_allowed_bet)
        # Randomize what to do based personal bluff inclination
        if np.random.rand() < self.randomness:
            max_bet = min(state.pot, max_allowed_bet)

        # Return random int between call_bet and rational_max
        distribution = get_random_betting_distribution(
            call_bet, max_bet, state.big_blind, always_add_fold_chance=False
        )
        for i, d in enumerate(distribution):
            debug_print(f"Bet: {i}, prob: {d}")
        return np.random.choice(len(distribution), p=distribution)
