import numpy as np
from PlayerABC import Player
from State import State
from env_helpers import get_big_blind


class RandomPlayer(Player):
    def get_distribution(self, state: State):
        """
        Generate a general uninformed distribution for betting.
        """
        current_player_i = state.current_player_i
        current_bet = state.current_bets[current_player_i]
        player_pile = state.player_piles[current_player_i]
        if state.folded_players[current_player_i]:
            return 0
        call_bet = max(state.current_bets) - current_bet
        all_in_bet = player_pile
        distribution = np.ones(all_in_bet + 1)
        # Make higher bets less likely
        likelihood_decay = 0.5  # Higher values make higher bets less likely
        distribution = distribution / (
            (np.arange(distribution.shape[0]) + 1) * likelihood_decay
        )
        # Ensure illegal raises are not made
        distribution[call_bet + 1 : call_bet + 1 + get_big_blind()] = 0
        # Ensure too low bets are not made
        distribution[:call_bet] = 0
        # Add a chance of folding
        distribution[0] = 1
        # Add a chance of calling
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
