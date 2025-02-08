from typing import Union
import numpy as np
from State import State
from cpp_poker.cpp_poker import CardCollection, CheatSheet, Oracle
from PlayerABC import Player
from helpers import get_random_betting_distribution
from hidden_state_model.helpers import get_observer_with_all_data
from hidden_state_model.observer import Observer


log_file = open("stats/ProbRegPlayer.log", "a")


def debug_print(*args, **kwargs):
    print(*args, **kwargs)
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


class ProbRegPlayer(Player):
    """
    Player that regresses the opponent's winning probability based on historical data.
    """

    title = "Regressor"
    bluff_prob: float
    rel_weight_player_in_reg: float
    called_bluff: bool
    is_bluffing: bool
    observer: Observer
    player_names: Union[list[str], None]
    player_types: Union[list[str], None]
    player_probs: Union[np.ndarray, None]

    def __init__(
        self, name: str = "Regine", bluff_prob=0.08, rel_weight_player_in_reg=2
    ):
        super().__init__()
        self.name = name
        self.bluff_prob = bluff_prob
        self.called_bluff = False
        self.is_bluffing = False
        self.player_names = None
        self.observer = get_observer_with_all_data()
        self.player_probs = None
        self.rel_weight_player_in_reg = rel_weight_player_in_reg

    def get_to_know_each_other(self, players: list[Player]):
        self.player_names = [p.name for p in players]
        self.player_types = [p.__class__.__name__ for p in players]
        self.player_probs = np.ones(len(self.player_names)) / len(self.player_names)

    def round_over(self, state: State, prev_state: State):
        self.called_bluff = False
        self.is_bluffing = False
        self.player_probs = np.array(state.player_is_active) / np.sum(
            state.player_is_active
        )

    def observe_bet(self, from_state: State, bet: int, was_blind=False):
        player_i = from_state.current_player_i
        if player_i == self.index:
            return
        if was_blind:
            return
        player_name = self.player_names[player_i]
        player_type = self.player_types[player_i]
        print("Observing bet from", player_name, "of", bet)
        self.observer.observe_action(
            from_state,
            player_name,
            player_type,
            bet,
            [n for n in self.player_names if n != player_name],
            None,
        )
        self.player_probs[player_i] = self.observer.predictor.predict(
            "prob", from_state.id, player_name, self.rel_weight_player_in_reg
        )

    def showdown(self, state: State, all_hands: list[Union[tuple[int, int], None]]):
        for i, hand in enumerate(all_hands):
            if hand is None:
                continue
            if i == self.index:
                continue
            relevant_states = []
            s = state
            while s is not None:
                if s.current_player_i == i:
                    relevant_states.append(s)
                s = s.prev_state
            self.observer.retrofill_hand_stats(relevant_states, hand)

    def play(self, state) -> int:
        current_player_i = state.current_player_i
        if state.player_is_folded[current_player_i]:
            return 0
        current_bet = state.bet_in_stage[current_player_i]
        call_bet = max(state.bet_in_stage) - current_bet
        self.player_probs[self.index] = CheatSheet.get_winning_probability(
            CardCollection(self.hand),
            CardCollection(state.public_cards),
            state.player_is_active.sum(),
        )
        debug_print("Own hand:", CardCollection(self.hand).str())
        winning_prob = combine_probabilities(self.player_probs, current_player_i)
        debug_print("Combined winning prob:", winning_prob)
        if self.is_bluffing or np.random.rand() < self.bluff_prob:
            self.is_bluffing = True
            winning_prob *= 2
            winning_prob = min(1, winning_prob)
            debug_print("Bluffing, so increasing winning prob to", winning_prob)
        rational_max = winning_prob * state.pot
        debug_print("Rational max:", rational_max)
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
            likelihood_decay=0.5 - 0.3 * len(state.public_cards) / 5,
        )
        for i, d in enumerate(distribution):
            debug_print(f"Bet: {i}, prob: {d}")
        return np.random.choice(len(distribution), p=distribution)


if __name__ == "__main__":
    print("Testing combine_probabilities")
    for case in [[0.3, 0.7], [0.45, 0.55], [0.9, 0.5], [0.99, 0.5]]:
        print("\n\nCase:", case)
        print("Combined prob:", combine_probabilities(case, 1))
