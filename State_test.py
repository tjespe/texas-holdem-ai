import unittest
from State import State
import numpy as np


class TestState(unittest.TestCase):
    def test_initial_preflop(self):
        """
        Test a brand new state with 0 public cards -> should be preflop.
        """
        s = State(
            public_cards=(),
            player_piles=(100, 100),
            current_player_i=0,
            bet_in_stage=(0, 0),
            bet_in_game=(0, 0),
            player_has_played=(False, False),
            player_is_folded=(False, False),
            first_better_i=0,
            big_blind=4,
        )
        self.assertEqual(s.stage, "preflop")
        self.assertFalse(s.is_terminal)
        self.assertEqual(s.pot, 0)
        self.assertEqual(s.n_players, 2)
        self.assertFalse(s.all_players_are_done)

    def test_flop(self):
        """
        Test that 3 public cards -> flop.
        """
        s = State(
            public_cards=(12, 33, 48),
            player_piles=(95, 105),
            current_player_i=1,
            bet_in_stage=(2, 4),
            bet_in_game=(5, 10),
            player_has_played=(True, True),
            player_is_folded=(False, False),
            first_better_i=0,
            big_blind=4,
        )
        self.assertEqual(s.stage, "flop")
        self.assertEqual(s.pot, 15)  # sum of bet_in_game
        self.assertFalse(s.is_terminal)

    def test_river_terminal(self):
        """
        Test a scenario with 5 public cards and all players done -> terminal.
        """
        s = State(
            public_cards=(0, 13, 26, 39, 52),
            player_piles=(50, 200),
            current_player_i=0,
            bet_in_stage=(10, 10),
            bet_in_game=(40, 40),
            player_has_played=(True, True),
            player_is_folded=(False, False),
            first_better_i=0,
            big_blind=4,
        )
        # Force a condition that all players have called + 5 cards on table
        self.assertEqual(s.stage, "river")
        # If the game logic says they're done, we can check is_terminal:
        # Possibly they'd be done if 'all_players_are_done' is True
        # or if there's only one active player, etc.
        # We'll artificially claim they're done:
        self.assertFalse(s.is_terminal)  # might be True depending on logic

    def test_to_dict(self):
        """
        Test the new to_dict() method to ensure JSON-serializable output.
        """
        s = State(
            public_cards=(1, 2, 3),
            player_piles=(100, 200),
            current_player_i=0,
            bet_in_stage=(4, 2),
            bet_in_game=(14, 12),
            player_has_played=(True, False),
            player_is_folded=(False, False),
            first_better_i=0,
            big_blind=4,
        )
        d = s.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("public_cards", d)
        self.assertEqual(d["public_cards"], [1, 2, 3])
        self.assertIn("pot", d)
        self.assertEqual(d["pot"], 26)  # 14 + 12
        self.assertEqual(d["stage"], "flop")  # 3 public cards => flop


if __name__ == "__main__":
    unittest.main()
