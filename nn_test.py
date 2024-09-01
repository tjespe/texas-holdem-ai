import unittest

import numpy as np
from State import State
from nn.run_nn_model import estimate_value_vector
from StateNode import StateNode
from cpp_poker.cpp_poker import Card, Hand, CardCollection


class TestNN(unittest.TestCase):
    def test_straight_flush_on_river(self):
        table = CardCollection(
            [
                Card("4", "♣"),
                Card("7", "♣"),
                Card("Q", "♥"),
                Card("K", "♥"),
                Card("A", "♥"),
            ]
        )
        node = StateNode(
            state=State(
                public_cards=[c.to_index() for c in table],
                player_piles=(100, 100),
                current_player_i=0,
                bet_in_stage=(0, 0),
                bet_in_game=(120, 120),
                player_has_played=(False, False),
                player_is_folded=(False, False),
                first_better_i=0,
                big_blind=2,
            ),
        )
        # Assume uniform range for P1
        p1_range = np.ones(len(Hand.COMBINATIONS))
        # Assume P2 only has low cards and no pairs
        p2_range = np.zeros(len(Hand.COMBINATIONS))
        for h, hand in enumerate(Hand.COMBINATIONS):
            for card in hand:
                if card.rank < 10 and card.rank not in (7, 4):
                    p2_range[h] = 1
                for table_card in table:
                    if table_card.rank == card.rank:
                        p2_range[h] = 0
        # Normalize ranges
        p1_range /= p1_range.sum()
        p2_range /= p2_range.sum()
        assert np.isclose(p1_range.sum(), 1), "P1 range did not sum to 1: %s" % p1_range
        assert np.isclose(p2_range.sum(), 1), "P2 range did not sum to 1: %s" % p2_range
        ranges = [p1_range, p2_range]
        result = estimate_value_vector(node, ranges, perspective=0)

        # Find 10 best hands
        best_hands = np.argsort(result)[::-1][:10]
        print("Best hands:")
        for h in best_hands:
            print(Hand(h).get_cards().str(), result[h])

        # Find 10 worst hands
        worst_hands = np.argsort(result)[:10]
        print("Worst hands:")
        for h in worst_hands:
            print(Hand(h).get_cards().str(), result[h])

        # Check value of straight flush hand
        straight_flush_hand: int = None
        for h, hand in enumerate(Hand.COMBINATIONS):
            if hand == CardCollection([Card("10", "♥"), Card("J", "♥")]):
                straight_flush_hand = h
                break
        assert straight_flush_hand is not None
        hand_value = result[straight_flush_hand]
        assert hand_value > 0, (
            "Straight flush hand value was below zero, i.e. not predicted to win: %s"
            % hand_value
        )


if __name__ == "__main__":
    unittest.main()
