import numpy as np
from cpp_poker.cpp_poker import CardCollection, CheatSheet, Oracle
from PlayerABC import Player
from helpers import get_random_betting_distribution


log_file = open("stats/CheatingPlayer.log", "a")


def debug_print(*args, **kwargs):
    # print(*args, **kwargs)
    print(*args, **kwargs, file=log_file, flush=True)


def combine_probabilities(probs: list[float], player_i: int) -> float:
    """
    Combine probabilities of winning for all players except player_i.
    """
    # Map each probability into the probability that they win and no opponents
    # win, then sum them up
    debug_print("Probs:", probs)
    mapped_probs = [
        # Probability of player i winning
        probs[i]
        # Probability of no other player winning
        * np.prod(1 - np.array([p for j, p in enumerate(probs) if i != j]))
        for i in range(len(probs))
    ]
    debug_print("Mapped probs:", mapped_probs)
    mapped_probs = np.array(mapped_probs) / np.sum(mapped_probs)
    debug_print("Mapped probs normalized:", mapped_probs)
    return mapped_probs[player_i]


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
        debug_print("Own hand:", CardCollection(self.hand).str())
        if state.stage == "river":
            winners = Oracle.find_winner(
                CardCollection(state.public_cards),
                [CardCollection(hand) for hand in self.all_hands],
                state.player_is_active,
            )
            debug_print("Winners:", winners)
            winning_prob = (1 if current_player_i in winners else 0) / len(winners)
        else:
            winning_prob = combine_probabilities(winner_probs, current_player_i)
        debug_print("Cheating winning prob:", winning_prob)
        rational_max = winning_prob * state.pot
        debug_print("Rational max:", rational_max)
        avg_forced_loss = (state.big_blind + state.small_blind) / state.n_players
        rational_max += avg_forced_loss
        debug_print("Rational max with forced loss:", rational_max)
        if call_bet > rational_max:
            # If the other player was irrational, join based on winning chance
            pot_before_bet = state.pot - call_bet
            if call_bet > pot_before_bet:
                debug_print(
                    "Call bet is higher than pot before bet, evaluating whether to call"
                )
                if np.random.rand() < winning_prob:
                    debug_print("Calling")
                    return call_bet
            debug_print("Folding")
            return 0

        max_allowed_bet = Oracle.get_max_bet_allowed(
            state.player_has_played,
            state.current_player_i,
            state.bet_in_stage,
            state.player_piles,
            state.player_is_active,
        )
        debug_print("Max allowed bet:", max_allowed_bet)
        max_bet = min(int(rational_max), max_allowed_bet)
        debug_print("Max bet:", max_bet)

        # Return random int between call_bet and rational_max
        distribution = get_random_betting_distribution(
            call_bet,
            max_bet,
            state.big_blind,
            always_add_fold_chance=False,
            likelihood_decay=0.1 - 0.09 * len(state.public_cards) / 5,
        )
        for i, d in enumerate(distribution):
            debug_print(f"Bet: {i}, prob: {d}")
        return np.random.choice(len(distribution), p=distribution)


if __name__ == "__main__":
    print("Testing combine_probabilities")
    for case in [[0.3, 0.7], [0.45, 0.55], [0.9, 0.5], [0.99, 0.5]]:
        print("\n\nCase:", case)
        print("Combined prob:", combine_probabilities(case, 1))
