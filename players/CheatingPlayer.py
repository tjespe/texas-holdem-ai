import numpy as np
from State import State
from cpp_poker.cpp_poker import CardCollection, CheatSheet, Oracle
from PlayerABC import Player
from helpers import get_random_betting_distribution


class CheatingPlayer(Player):
    """
    Player that looks at the other player's cards and bets accordingly.
    """

    all_hands = None

    def __init__(self, name: str = "Cleopatra"):
        super().__init__()
        self.name = name

    def cheat(self, hands: list[tuple[int, int]]):
        self.all_hands = hands

    def play(self, state) -> int:
        current_player_i = state.current_player_i
        if state.player_is_folded[current_player_i]:
            return 0
        current_bet = state.bet_in_stage[current_player_i]
        call_bet = max(state.bet_in_stage) - current_bet
        winner_probs = [
            CheatSheet.get_winning_probability(
                CardCollection(hand),
                CardCollection(state.public_cards),
                state.player_is_active.sum(),
                1000,
            )
            for hand in self.all_hands
        ]
        print("Own hand:", CardCollection(self.hand).str())
        if state.stage == "river":
            winners = Oracle.find_winner(
                CardCollection(state.public_cards),
                [CardCollection(hand) for hand in self.all_hands],
                state.player_is_active,
            )
            print("Winners:", winners)
            winning_prob = (1 if current_player_i in winners else 0) / len(winners)
        else:
            print("Winner probs:", winner_probs)
            print("Own winning prob:", winner_probs[current_player_i])
            print("Sum of winner probs:", sum(winner_probs))
            winning_prob = winner_probs[current_player_i] / sum(winner_probs)
        print("Cheating winning prob:", winning_prob)
        rational_max = winning_prob * state.pot
        print("Rational max:", rational_max)
        if call_bet > rational_max:
            print("Folding")
            return 0

        max_allowed_bet = Oracle.get_max_bet_allowed(
            state.player_has_played,
            state.current_player_i,
            state.bet_in_stage,
            state.player_piles,
            state.player_is_active,
        )
        print("Max allowed bet:", max_allowed_bet)
        max_bet = min(int(rational_max), max_allowed_bet)
        print("Max bet:", max_bet)

        # Return random int between call_bet and rational_max
        distribution = get_random_betting_distribution(
            call_bet,
            max_bet,
            state.big_blind,
            always_add_fold_chance=False,
            likelihood_decay=0.2 - 0.15 * len(state.public_cards) / 5,
        )
        for i, d in enumerate(distribution):
            print(f"Bet: {i}, prob: {d}")
        return np.random.choice(len(distribution), p=distribution)
