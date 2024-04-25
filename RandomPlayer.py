import numpy as np
from PlayerABC import Player
from State import State
import oracle


class RandomPlayer(Player):
    def __init__(self, name: str = "Rando"):
        super().__init__()
        self.name = name

    def get_distribution(self, state: State):
        """
        Generate a general uninformed distribution for betting.
        """
        current_player_i = state.current_player_i
        current_bet = state.current_bets[current_player_i]
        player_pile = state.player_piles[current_player_i]
        call_bet = max(state.current_bets) - current_bet
        all_in_bet = player_pile
        max_allowed_bet = oracle.get_max_bet_allowed(
            state.player_has_played,
            current_player_i,
            state.current_bets,
            state.player_piles,
            state.player_is_active,
        )
        max_bet = min(max_allowed_bet, all_in_bet)
        distribution = np.ones(max_bet + 1)
        # Make higher bets less likely
        likelihood_decay = 0.5  # Higher values make higher bets less likely
        distribution = distribution / (
            (np.arange(distribution.shape[0]) + 1) * likelihood_decay
        )
        # Ensure illegal raises are not made
        distribution[call_bet + 1 : call_bet + 1 + state.big_blind] = 0
        # Ensure too low bets are not made
        distribution[:call_bet] = 0
        # Add a chance of folding
        distribution[0] = 1
        # Add a chance of calling
        if call_bet < distribution.shape[0]:
            distribution[call_bet] = 1
        # Ensure sum of distribution is 1
        distribution = distribution / np.sum(distribution)
        # Plotting for debugging
        # plt.plot(
        #     distribution,
        #     label=f"Player {current_player_i}, {len(state.public_cards)} cards",
        # )
        return distribution

    def play(self, state: State) -> int:
        distribution = self.get_distribution(state)
        return np.random.choice(len(distribution), p=distribution)

    def __repr__(self) -> str:
        return f"RandomPlayer('{self.name}')"
