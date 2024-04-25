from typing import Iterable
import unittest

import numpy as np
from Card import Card
from PlayerABC import Player

import oracle


class MockPlayer(Player):
    def __init__(self, hand: Iterable[Card]):
        self.hand = tuple(card.to_index() for card in hand)

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
        table = {
            Card("2", "♥"),
            Card("3", "♥"),
            Card("10", "♥"),
            Card("10", "♦"),
            Card("J", "♣"),
        }
        player1 = MockPlayer(
            {
                Card("J", "♠"),
                Card("K", "♥"),
            }
        )
        player2 = MockPlayer(
            {
                Card("J", "♥"),
                Card("Q", "♦"),
            }
        )
        # Player 1 should win because of the high card (K > Q)
        self.assertEqual(
            oracle.find_winner(
                [c.to_index() for c in table],
                [player1.hand, player2.hand],
                (True, True),
            ),
            {0},
        )

    def test_actual_tie_with_two_pairs(self):
        table = {
            Card("A", "♥"),
            Card("K", "♦"),
            Card("10", "♥"),
            Card("10", "♦"),
            Card("J", "♣"),
        }
        player1 = MockPlayer(
            {
                Card("J", "♠"),
                Card("9", "♥"),
            }
        )
        player2 = MockPlayer(
            {
                Card("J", "♥"),
                Card("8", "♦"),
            }
        )
        # In this case, there is an actual tie, because only 5 cards should count for
        # each player, and the high card, from the table, is the same for both players.
        winner = oracle.find_winner(
            [c.to_index() for c in table], [player1.hand, player2.hand], (True, True)
        )
        self.assertEqual(
            len(winner), 2, "Both players should win. Returned set was\n" + str(winner)
        )
        self.assertEqual(winner, {0, 1})

    def test_folded_player_can_not_win(self):
        table = {
            Card("2", "♥"),
            Card("3", "♥"),
            Card("10", "♥"),
            Card("10", "♦"),
            Card("J", "♣"),
        }
        player1 = MockPlayer(
            {
                Card("J", "♠"),
                Card("K", "♥"),
            }
        )
        player2 = MockPlayer(
            {
                Card("J", "♥"),
                Card("Q", "♦"),
            }
        )
        # Player 2 should win because player 1 has folded or is bust
        self.assertEqual(
            oracle.find_winner(
                [c.to_index() for c in table],
                [player1.hand, player2.hand],
                (False, True),
            ),
            {1},
        )

    def test_cannot_bet_more_than_smallest_stack(self):
        player_played = (True, False, False)
        current_player_i = 1
        current_bets = (10, 1, 2)
        player_piles = (200, 300, 30)
        player_is_active = (True, True, True)

        # It is not allowed to place a bet that cannot be matched by all other active players
        self.assertEqual(
            oracle.get_max_bet_allowed(
                player_played,
                current_player_i,
                current_bets,
                player_piles,
                player_is_active,
            ),
            31,
        )

    def test_can_bet_even_if_players_are_bust(self):
        player_played = (True, False, False)
        current_player_i = 1
        current_bets = (10, 0, 0)
        player_piles = (200, 300, 0)
        player_is_active = (True, True, False)

        # The bust players should not be considered when calculating the max bet
        self.assertEqual(
            oracle.get_max_bet_allowed(
                player_played,
                current_player_i,
                current_bets,
                player_piles,
                player_is_active,
            ),
            210,
        )

    def test_cannot_reraise(self):
        player_played = (True, True, False)
        current_player_i = 1
        current_bets = (10, 5, 2)
        player_piles = (200, 300, 30)
        player_is_active = (True, True, True)

        # It is not allowed to reraise
        self.assertEqual(
            oracle.get_max_bet_allowed(
                player_played,
                current_player_i,
                current_bets,
                player_piles,
                player_is_active,
            ),
            5,
        )

    def test_get_pre_flop_aces_win_prob(self):
        hand = (Card("A", "♦").to_index(), Card("A", "♠").to_index())
        self.assertAlmostEqual(oracle.get_winning_prob(hand, (), 2), 0.86, delta=0.01)

    def test_get_pre_flop_ace_king_unsuited_win_prob(self):
        hand = (Card("A", "♦").to_index(), Card("K", "♠").to_index())
        self.assertAlmostEqual(oracle.get_winning_prob(hand, (), 2), 0.65, delta=0.02)

    def test_suits_do_not_matter(self):
        # Two hands with the same cards but different suits should have the same win
        # probability
        hand1 = (Card("A", "♦").to_index(), Card("K", "♠").to_index())
        hand2 = (Card("A", "♦").to_index(), Card("K", "♥").to_index())
        table = [
            Card("2", "♦").to_index(),
            Card("3", "♦").to_index(),
            Card("4", "♦").to_index(),
        ]
        self.assertEqual(
            oracle._convert_cards_to_equiv_str(hand1, table),
            oracle._convert_cards_to_equiv_str(hand2, table),
        )


class TestPokerUtilityMatrix(unittest.TestCase):
    def setUp(self):
        # This is your "full deck" setup
        self.full_deck = set(range(52))

    def test_single_active_player(self):
        # Terminal state: Only one active player means they win automatically.
        table = (5, 18, 32)
        player_is_active = (True, False, False)
        perspective = 0
        result = oracle.generate_utility_matrix(
            table, player_is_active, perspective, self.full_deck
        )
        expected = np.zeros((len(oracle.POSSIBLE_HOLE_PAIRS),))
        # The only player (who is also the perspective) automatically wins, so the utility should be 1.
        expected[:] = 1
        np.testing.assert_array_equal(
            result, expected, "Expected all ones for single active player"
        )

    def test_showdown_two_players(self):
        # Terminal state: Showdown between two players
        table = (2, 29, 31, 45, 50)
        player_is_active = (True, True, False)
        perspective = 0
        # Assume the remaining deck considers the table cards are out
        deck = self.full_deck - set(table)
        result = oracle.generate_utility_matrix(
            table, player_is_active, perspective, deck
        )
        # The exact values depend on the 'find_winner' function logic
        self.assertEqual(
            result.shape,
            (len(oracle.POSSIBLE_HOLE_PAIRS), len(oracle.POSSIBLE_HOLE_PAIRS)),
            "Unexpected shape for two-player showdown",
        )

    def test_deck_respect_table(self):
        # Ensure the function respects the remaining deck after the table is dealt
        table = (12, 7, 23)
        player_is_active = (True, True)
        perspective = 0
        deck = self.full_deck - set(table)
        result = oracle.generate_utility_matrix(
            table, player_is_active, perspective, deck
        )
        # Check if any part of the result uses cards from the table
        for pair_idx in np.argwhere(result != 0):
            pair = oracle.POSSIBLE_HOLE_PAIRS[pair_idx[0]]
            self.assertNotIn(
                pair[0], table, "Utility matrix using cards already on the table"
            )
            self.assertNotIn(
                pair[1], table, "Utility matrix using cards already on the table"
            )


if __name__ == "__main__":
    unittest.main(failfast=True)
