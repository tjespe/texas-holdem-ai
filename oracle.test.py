from typing import Iterable
import unittest
from Card import Card
from PlayerABC import Player

import oracle


class MockPlayer(Player):
    def __init__(self, hand: Iterable[Card]):
        self.hand = hand

    def play(self, state):
        raise Exception("This method should not be called.")

    def __repr__(self) -> str:
        return f"MockPlayer({self.hand})"


class OracleTestCase(unittest.TestCase):
    def test_check_for_royal_flush(self):
        hand = {
            Card("10", "♥"),
            Card("J", "♥"),
            Card("Q", "♥"),
            Card("K", "♥"),
            Card("A", "♥"),
        }
        self.assertEqual(oracle.check_for_royal_flush(hand), (True, hand))
        hand = {
            Card("10", "♥"),
            Card("J", "♥"),
            Card("Q", "♥"),
            Card("K", "♥"),
            Card("9", "♥"),
        }
        self.assertEqual(oracle.check_for_royal_flush(hand), (False, None))

    def test_check_for_straight_flush(self):
        hand = {
            Card("10", "♥"),
            Card("J", "♥"),
            Card("Q", "♥"),
            Card("K", "♥"),
            Card("A", "♥"),
        }
        self.assertEqual(oracle.check_for_straight_flush(hand), (True, hand))
        hand = {
            Card("8", "♥"),
            Card("10", "♥"),
            Card("J", "♥"),
            Card("Q", "♥"),
            Card("K", "♥"),
        }
        self.assertEqual(oracle.check_for_straight_flush(hand), (False, None))

    def test_check_for_four_of_a_kind(self):
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("10", "♣"),
            Card("10", "♠"),
            Card("A", "♥"),
        }
        self.assertEqual(
            oracle.check_for_four_of_a_kind(hand),
            (
                True,
                {
                    Card("10", "♥"),
                    Card("10", "♦"),
                    Card("10", "♣"),
                    Card("10", "♠"),
                },
            ),
        )
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("10", "♣"),
            Card("J", "♠"),
            Card("A", "♥"),
        }
        self.assertEqual(oracle.check_for_four_of_a_kind(hand), (False, None))

    def test_check_for_full_house(self):
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("10", "♣"),
            Card("A", "♠"),
            Card("A", "♥"),
        }
        self.assertEqual(oracle.check_for_full_house(hand), (True, hand))
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("J", "♣"),
            Card("A", "♠"),
            Card("A", "♥"),
        }
        self.assertEqual(oracle.check_for_full_house(hand), (False, None))

    def test_check_for_flush(self):
        hand = {
            Card("10", "♥"),
            Card("J", "♥"),
            Card("Q", "♥"),
            Card("K", "♥"),
            Card("A", "♥"),
        }
        self.assertEqual(oracle.check_for_flush(hand), (True, hand))
        hand = {
            Card("10", "♥"),
            Card("J", "♥"),
            Card("Q", "♥"),
            Card("K", "♥"),
            Card("9", "♦"),
        }
        self.assertEqual(oracle.check_for_flush(hand), (False, None))

    def test_check_for_straight(self):
        hand = {
            Card("10", "♥"),
            Card("J", "♦"),
            Card("Q", "♣"),
            Card("K", "♠"),
            Card("A", "♥"),
        }
        self.assertEqual(oracle.check_for_straight(hand), (True, hand))
        hand = {
            Card("10", "♥"),
            Card("J", "♦"),
            Card("Q", "♣"),
            Card("K", "♠"),
            Card("8", "♥"),
        }
        self.assertEqual(oracle.check_for_straight(hand), (False, None))

    def test_check_for_three_of_a_kind(self):
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("10", "♣"),
            Card("A", "♠"),
            Card("K", "♥"),
        }
        self.assertEqual(
            oracle.check_for_three_of_a_kind(hand),
            (
                True,
                {
                    Card("10", "♥"),
                    Card("10", "♦"),
                    Card("10", "♣"),
                },
            ),
        )
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("J", "♣"),
            Card("A", "♠"),
            Card("K", "♥"),
        }
        self.assertEqual(oracle.check_for_three_of_a_kind(hand), (False, None))

    def test_check_for_two_pair(self):
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("J", "♣"),
            Card("J", "♠"),
            Card("K", "♥"),
        }
        self.assertEqual(
            oracle.check_for_two_pair(hand),
            (
                True,
                {
                    Card("10", "♥"),
                    Card("10", "♦"),
                    Card("J", "♣"),
                    Card("J", "♠"),
                },
            ),
        )
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("J", "♣"),
            Card("Q", "♠"),
            Card("K", "♥"),
        }
        self.assertEqual(oracle.check_for_two_pair(hand), (False, None))

    def test_check_for_one_pair(self):
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("J", "♣"),
            Card("Q", "♠"),
            Card("K", "♥"),
        }
        self.assertEqual(
            oracle.check_for_one_pair(hand), (True, {Card("10", "♥"), Card("10", "♦")})
        )
        hand = {
            Card("10", "♥"),
            Card("J", "♦"),
            Card("J", "♣"),
            Card("Q", "♠"),
            Card("K", "♥"),
        }
        self.assertEqual(
            oracle.check_for_one_pair(hand), (True, {Card("J", "♦"), Card("J", "♣")})
        )

    def test_check_for_full_house(self):
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("10", "♣"),
            Card("A", "♠"),
            Card("A", "♥"),
        }
        self.assertEqual(oracle.check_for_full_house(hand), (True, hand))
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("J", "♣"),
            Card("A", "♠"),
            Card("A", "♥"),
        }
        self.assertEqual(oracle.check_for_full_house(hand), (False, None))

    def test_get_n_high_cards(self):
        hand = {
            Card("10", "♥"),
            Card("J", "♦"),
            Card("Q", "♣"),
            Card("K", "♠"),
            Card("A", "♥"),
        }
        self.assertEqual(
            oracle.get_n_high_cards(hand, 3),
            [Card("A", "♥"), Card("K", "♠"), Card("Q", "♣")],
        )

    def test_get_n_high_ranks(self):
        hand = {
            Card("10", "♥"),
            Card("J", "♦"),
            Card("Q", "♣"),
            Card("K", "♠"),
            Card("A", "♥"),
        }
        self.assertEqual(
            oracle.get_n_high_ranks(hand, 3),
            [Card.get_rank("A"), Card.get_rank("K"), Card.get_rank("Q")],
        )

    def test_rank_hand(self):
        # Royal flush
        hand = {
            Card("10", "♥"),
            Card("J", "♥"),
            Card("Q", "♥"),
            Card("K", "♥"),
            Card("A", "♥"),
        }
        self.assertEqual(oracle.rank_hand(hand), [9])

        # Full house
        hand = {
            Card("10", "♥"),
            Card("10", "♦"),
            Card("10", "♣"),
            Card("A", "♥"),
            Card("A", "♦"),
        }
        self.assertEqual(
            oracle.rank_hand(hand), [6, Card.get_rank("10"), Card.get_rank("A")]
        )

    def test_tie_break_for_two_pair(self):
        player1 = MockPlayer(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("J", "♣"),
                Card("J", "♠"),
                Card("K", "♥"),
                Card("2", "♥"),
                Card("3", "♥"),
            }
        )
        player2 = MockPlayer(
            {
                Card("10", "♠"),
                Card("10", "♣"),
                Card("J", "♦"),
                Card("J", "♥"),
                Card("Q", "♦"),
                Card("2", "♥"),
                Card("3", "♥"),
            }
        )
        # Player 1 should win because of the high card (K > Q)
        self.assertEqual(oracle.find_winner({player1, player2}), {player1})

    def test_actual_tie_with_two_pairs(self):
        cards_on_table = {
            Card("A", "♥"),
            Card("K", "♦"),
        }
        player1 = MockPlayer(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("J", "♣"),
                Card("J", "♠"),
                Card("9", "♥"),
            }.union(cards_on_table)
        )
        player2 = MockPlayer(
            {
                Card("10", "♠"),
                Card("10", "♣"),
                Card("J", "♦"),
                Card("J", "♥"),
                Card("8", "♦"),
            }.union(cards_on_table)
        )
        # In this case, there is an actual tie, because only 5 cards should count for
        # each player, and the high card, from the table, is the same for both players.
        winner = oracle.find_winner({player1, player2})
        self.assertEqual(
            len(winner), 2, "Both players should win. Returned set was\n" + str(winner)
        )
        self.assertEqual(winner, {player1, player2})


if __name__ == "__main__":
    unittest.main()
