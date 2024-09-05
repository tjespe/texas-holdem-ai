import unittest

from cpp_poker.cpp_poker import Card, CardCollection, CheatSheet


class CheatSheetCase(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main(failfast=True)
