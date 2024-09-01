import unittest

import numpy as np
from cpp_poker.cpp_poker import Card, Oracle, CardCollection, Hand, HandRank, CheatSheet


class HandCheckTestCase(unittest.TestCase):
    def test_check_for_royal_flush(self):
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("J", "♥"),
                Card("Q", "♥"),
                Card("K", "♥"),
                Card("A", "♥"),
            }
        )
        ranking = hand.check_for_royal_flush()
        self.assertIsNotNone(ranking, "Royal flush should be detected")
        self.assertEqual(ranking.get_rank(), HandRank.ROYAL_FLUSH)
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("J", "♥"),
                Card("Q", "♥"),
                Card("K", "♥"),
                Card("9", "♥"),
            }
        )
        self.assertIsNone(hand.check_for_royal_flush(), "Not a royal flush")

    def test_check_for_straight_flush(self):
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("J", "♥"),
                Card("Q", "♥"),
                Card("K", "♥"),
                Card("A", "♥"),
            }
        )
        ranking = hand.check_for_straight_flush()
        self.assertIsNotNone(ranking, "Straight flush should be detected")
        self.assertEqual(ranking.get_rank(), HandRank.STRAIGHT_FLUSH)
        hand = CardCollection(
            {
                Card("8", "♥"),
                Card("10", "♥"),
                Card("J", "♥"),
                Card("Q", "♥"),
                Card("K", "♥"),
            }
        )
        ranking = hand.check_for_straight_flush()
        self.assertIsNone(ranking, "Not a straight flush")

    def test_check_for_four_of_a_kind(self):
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("10", "♣"),
                Card("10", "♠"),
                Card("A", "♥"),
            }
        )
        result = hand.check_for_four_of_a_kind()
        self.assertIsNotNone(result)
        self.assertEqual(result.get_rank(), HandRank.FOUR_OF_A_KIND)

        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("10", "♣"),
                Card("J", "♠"),
                Card("A", "♥"),
            }
        )
        self.assertIsNone(hand.check_for_four_of_a_kind())

    def test_check_for_full_house(self):
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("10", "♣"),
                Card("A", "♠"),
                Card("A", "♥"),
            }
        )
        result = hand.check_for_full_house()
        self.assertIsNotNone(result)
        self.assertEqual(result.get_rank(), HandRank.FULL_HOUSE)

        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("J", "♣"),
                Card("A", "♠"),
                Card("A", "♥"),
            }
        )
        self.assertIsNone(hand.check_for_full_house())

    def test_check_for_flush(self):
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("J", "♥"),
                Card("Q", "♥"),
                Card("K", "♥"),
                Card("A", "♥"),
            }
        )
        result = hand.check_for_flush()
        self.assertIsNotNone(result)
        self.assertEqual(result.get_rank(), HandRank.FLUSH)

        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("J", "♥"),
                Card("Q", "♥"),
                Card("K", "♥"),
                Card("9", "♦"),
            }
        )
        self.assertIsNone(hand.check_for_flush())

    def test_check_for_straight(self):
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("J", "♦"),
                Card("Q", "♣"),
                Card("K", "♠"),
                Card("A", "♥"),
            }
        )
        result = hand.check_for_straight()
        self.assertIsNotNone(result)
        self.assertEqual(result.get_rank(), HandRank.STRAIGHT)

        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("J", "♦"),
                Card("Q", "♣"),
                Card("K", "♠"),
                Card("8", "♥"),
            }
        )
        self.assertIsNone(hand.check_for_straight())

    def test_check_for_three_of_a_kind(self):
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("10", "♣"),
                Card("A", "♠"),
                Card("K", "♥"),
            }
        )
        result = hand.check_for_three_of_a_kind()
        self.assertIsNotNone(result)
        self.assertEqual(result.get_rank(), HandRank.THREE_OF_A_KIND)

        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("J", "♣"),
                Card("A", "♠"),
                Card("K", "♥"),
            }
        )
        self.assertIsNone(hand.check_for_three_of_a_kind())

    def test_check_for_two_pair(self):
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("J", "♣"),
                Card("J", "♠"),
                Card("K", "♥"),
            }
        )
        result = hand.check_for_two_pair()
        self.assertIsNotNone(result)
        self.assertEqual(result.get_rank(), HandRank.TWO_PAIR)

        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("J", "♣"),
                Card("Q", "♠"),
                Card("K", "♥"),
            }
        )
        self.assertIsNone(hand.check_for_two_pair())

    def test_check_for_one_pair(self):
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("J", "♣"),
                Card("Q", "♠"),
                Card("K", "♥"),
            }
        )
        result = hand.check_for_one_pair()
        self.assertIsNotNone(result)
        self.assertEqual(result.get_rank(), HandRank.ONE_PAIR)

        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("J", "♦"),
                Card("J", "♣"),
                Card("Q", "♠"),
                Card("K", "♥"),
            }
        )
        result = hand.check_for_one_pair()
        self.assertIsNotNone(result)
        self.assertEqual(result.get_rank(), HandRank.ONE_PAIR)


class CardCollectionTestCase(unittest.TestCase):
    def test_get_n_high_cards(self):
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("J", "♦"),
                Card("Q", "♣"),
                Card("K", "♠"),
                Card("A", "♥"),
            }
        )
        self.assertEqual(
            hand.get_n_high_cards(3),
            [Card("A", "♥"), Card("K", "♠"), Card("Q", "♣")],
        )

    def test_get_n_high_ranks(self):
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("J", "♦"),
                Card("Q", "♣"),
                Card("K", "♠"),
                Card("A", "♥"),
            }
        )
        self.assertEqual(
            hand.get_n_high_ranks(3),
            [Card.get_rank("A"), Card.get_rank("K"), Card.get_rank("Q")],
        )


class HandRankTestCase(unittest.TestCase):
    def test_rank_hand(self):
        # Royal flush
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("J", "♥"),
                Card("Q", "♥"),
                Card("K", "♥"),
                Card("A", "♥"),
            }
        )
        self.assertEqual(hand.rank_hand(), HandRank(HandRank.ROYAL_FLUSH, []))

        # Full house
        hand = CardCollection(
            {
                Card("10", "♥"),
                Card("10", "♦"),
                Card("10", "♣"),
                Card("A", "♥"),
                Card("A", "♦"),
            }
        )
        self.assertEqual(
            hand.rank_hand(),
            HandRank(HandRank.FULL_HOUSE, [Card.get_rank("10"), Card.get_rank("A")]),
        )

    def test_tie_break_for_two_pair(self):
        table = CardCollection(
            {
                Card("2", "♥"),
                Card("3", "♥"),
                Card("10", "♥"),
                Card("10", "♦"),
                Card("J", "♣"),
            }
        )
        player1_hand = CardCollection(
            {
                Card("J", "♠"),
                Card("8", "♥"),
            }
        )
        player2_hand = CardCollection(
            {
                Card("J", "♥"),
                Card("7", "♦"),
            }
        )
        # Player 1 should win because of the high card (8 > 7)
        self.assertEqual(
            Oracle.find_winner(
                table,
                [player1_hand, player2_hand],
                (True, True),
            ),
            {0},
        )

    def test_actual_tie_with_two_pairs(self):
        table = CardCollection(
            {
                Card("A", "♥"),
                Card("K", "♦"),
                Card("10", "♥"),
                Card("10", "♦"),
                Card("J", "♣"),
            }
        )
        player1_hand = CardCollection(
            {
                Card("J", "♠"),
                Card("9", "♥"),
            }
        )
        player2_hand = CardCollection(
            {
                Card("J", "♥"),
                Card("8", "♦"),
            }
        )
        # In this case, there is an actual tie, because only 5 cards should count for
        # each player, and the high card, from the table, is the same for both players.
        winner = Oracle.find_winner(table, [player1_hand, player2_hand], (True, True))
        self.assertEqual(
            len(winner), 2, "Both players should win. Returned set was\n" + str(winner)
        )
        self.assertEqual(winner, {0, 1})


class OracleTestCase(unittest.TestCase):
    def test_folded_player_can_not_win(self):
        table = CardCollection(
            {
                Card("2", "♥"),
                Card("3", "♥"),
                Card("10", "♥"),
                Card("10", "♦"),
                Card("J", "♣"),
            }
        )
        player1_hand = CardCollection(
            {
                Card("J", "♠"),
                Card("K", "♥"),
            }
        )
        player2_hand = CardCollection(
            {
                Card("J", "♥"),
                Card("Q", "♦"),
            }
        )
        # Player 2 should win because player 1 has folded or is bust
        self.assertEqual(
            Oracle.find_winner(
                table,
                [player1_hand, player2_hand],
                (False, True),
            ),
            {1},
        )

    def test_cannot_bet_more_than_smallest_stack(self):
        player_played = (True, False, False)
        current_player_i = 1
        bet_in_stage = (10, 1, 2)
        player_piles = (200, 300, 30)
        player_is_active = (True, True, True)

        # It is not allowed to place a bet that cannot be matched by all other active players
        self.assertEqual(
            Oracle.get_max_bet_allowed(
                player_played,
                current_player_i,
                bet_in_stage,
                player_piles,
                player_is_active,
            ),
            31,
        )

    def test_can_bet_even_if_players_are_bust(self):
        player_played = (True, False, False)
        current_player_i = 1
        bet_in_stage = (10, 0, 0)
        player_piles = (200, 300, 0)
        player_is_active = (True, True, False)

        # The bust players should not be considered when calculating the max bet
        self.assertEqual(
            Oracle.get_max_bet_allowed(
                player_played,
                current_player_i,
                bet_in_stage,
                player_piles,
                player_is_active,
            ),
            210,
        )

    def test_can_reraise(self):
        player_played = (True, True, True)
        current_player_i = 1
        bet_in_stage = (10, 5, 2)
        player_piles = (200, 300, 30)
        player_is_active = (True, True, True)

        # It is allowed to reraise, but only to the amount of the smallest stack
        self.assertEqual(
            Oracle.get_max_bet_allowed(
                player_played,
                current_player_i,
                bet_in_stage,
                player_piles,
                player_is_active,
            ),
            30 + 2 - 5,
        )

    def test_get_pre_flop_aces_win_prob(self):
        hand = CardCollection({Card("A", "♦"), Card("A", "♠")})
        table = CardCollection()
        self.assertAlmostEqual(
            CheatSheet.get_winning_probability(hand, table, 2, 100000), 0.86, delta=0.01
        )

    def test_get_pre_flop_ace_king_unsuited_win_prob(self):
        hand = CardCollection({Card("A", "♦"), Card("K", "♠")})
        table = CardCollection()
        self.assertAlmostEqual(
            CheatSheet.get_winning_probability(hand, table, 2, 100000), 0.65, delta=0.01
        )


class TestPokerUtilityMatrix(unittest.TestCase):
    def test_single_active_player(self):
        # Terminal state: Only one active player means they win automatically.
        table = CardCollection([5, 18, 32])
        result = np.array(Oracle.generate_utility_matrix(table, False))
        # The only player (who is also the perspective) automatically wins, so the utility should be 1
        # for all possible hands, and 0 for all other hands.
        assert result.mean() > 0.7, "Expected utility to be close to 1"
        assert (
            result.min() == 0
        ), "Utility should never be negative when only one player is active"

    def test_showdown_two_players(self):
        # Terminal state: Showdown between two players
        table = CardCollection([2, 29, 31])
        result = np.array(Oracle.generate_utility_matrix(table, True))
        print(result)
        # The exact values depend on the 'find_winner' function logic
        self.assertEqual(
            result.shape,
            (len(Hand.COMBINATIONS), len(Hand.COMBINATIONS)),
            "Unexpected shape for two-player showdown",
        )

    def test_deck_respect_table(self):
        # Ensure the function respects the remaining deck after the table is dealt
        table = CardCollection([12, 7, 23])
        result = np.array(Oracle.generate_utility_matrix(table, True))
        print(result.shape)
        print(result)
        # Check if any part of the result uses cards from the table
        cards_on_hands = CardCollection()
        samples = 100
        np.random.seed(0)
        possible_hands = np.argwhere(result != 0)
        np.random.shuffle(possible_hands)
        for i, (player_pair_idx, opponent_pair_idx) in enumerate(possible_hands):
            cards_on_hands.add_cards(Hand.COMBINATIONS[player_pair_idx])
            cards_on_hands.add_cards(Hand.COMBINATIONS[opponent_pair_idx])
            if i > samples:
                break
        assert not cards_on_hands.intersects(
            table
        ), "Some hands use cards from the table"


if __name__ == "__main__":
    unittest.main(failfast=True)
