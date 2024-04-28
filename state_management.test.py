from typing import Iterable
import unittest
from cpp_poker.cpp_poker import Card
from PlayerABC import Player
from State import State
from state_management import (
    end_round,
    fold_current_player,
    place_bet,
    skip_current_player,
    add_cards,
)


class MockPlayer(Player):
    def __init__(self, hand: Iterable[int]):
        self.hand = hand

    def play(self, state):
        raise Exception("This method should not be called.")

    def __repr__(self) -> str:
        return f"MockPlayer({self.hand})"


class TestStateManager(unittest.TestCase):
    def test_add_flop(self):
        state = State(
            public_cards=(),
            player_piles=(100, 100),
            current_player_i=1,
            bet_in_stage=(0, 0),
            bet_in_game=(0, 0),
            folded_players=(False, False),
            player_has_played=(True, True),
            first_better_i=0,
            big_blind=2,
        )
        new_state = add_cards(state, (0, 1, 2))
        self.assertEqual(new_state.public_cards, (0, 1, 2))
        self.assertEqual(new_state.bet_in_stage, (0, 0))
        self.assertEqual(new_state.player_has_played, (False, False))

    def test_add_turn(self):
        state = State(
            public_cards=(0, 1, 2),
            player_piles=(100, 100),
            current_player_i=1,
            bet_in_stage=(10, 10),
            bet_in_game=(10, 10),
            folded_players=(False, False),
            first_better_i=0,
            big_blind=2,
            player_has_played=(True, True),
        )
        new_state = add_cards(state, (3, 4))
        self.assertEqual(new_state.public_cards, (0, 1, 2, 3, 4))
        self.assertEqual(new_state.bet_in_stage, (0, 0))
        self.assertEqual(new_state.player_has_played, (False, False))

    def test_add_river(self):
        state = State(
            public_cards=(0, 1, 2, 3),
            player_piles=(100, 100, 100),
            current_player_i=2,
            bet_in_stage=(10, 0, 10),
            bet_in_game=(10, 0, 10),
            player_has_played=(True, True, True),
            folded_players=(False, True, False),
            first_better_i=0,
            big_blind=2,
        )
        new_state = add_cards(state, (4,))
        self.assertEqual(new_state.public_cards, (0, 1, 2, 3, 4))
        self.assertEqual(new_state.bet_in_stage, (0, 0, 0))
        self.assertEqual(new_state.bet_in_game, (10, 0, 10))
        self.assertEqual(new_state.pot, 20)
        self.assertEqual(new_state.player_has_played, (False, False, False))
        self.assertEqual(new_state.player_is_folded, (False, True, False))

    def test_end_round(self):
        state = State(
            public_cards=(0, 2, 4, 6, 8),
            player_piles=(200, 100, 0),
            current_player_i=2,
            bet_in_stage=(20, 20, 20),
            bet_in_game=(40, 40, 40),
            player_has_played=(True, True, True),
            folded_players=(False, False, False),
            first_better_i=0,
            big_blind=2,
        )
        players = [
            MockPlayer((1, 2)),
            MockPlayer((3, 4)),
            MockPlayer((5, 6)),
        ]
        new_state = end_round(state, players)
        # Check that the pot was distributed correctly (player 3 should get 120)
        self.assertEqual(new_state.player_piles, (200, 100, 120))

    def _vectorization(self):
        state = State(
            public_cards=(0, 1, 2, 3, 4),
            player_piles=(100, 200, 300, 400),
            current_player_i=2,
            bet_in_stage=(10, 0, 0, 0),
            player_has_played=(True, True, False, False),
            folded_players=(False, True, False, False),
            first_better_i=0,
            big_blind=2,
        )
        arr = state.to_array()
        new_state = State.from_array(arr)
        self.assertEqual(state.public_cards, new_state.public_cards)
        self.assertEqual(state.player_piles, new_state.player_piles)
        self.assertEqual(state.pot, new_state.pot)
        self.assertEqual(state.current_player_i, new_state.current_player_i)
        self.assertEqual(state.bet_in_stage, new_state.bet_in_stage)
        self.assertEqual(state.player_is_folded, new_state.player_is_folded)
        self.assertEqual(state.first_better_i, new_state.first_better_i)
        self.assertEqual(state.n_players, new_state.n_players)
        self.assertEqual(state, new_state)


if __name__ == "__main__":
    unittest.main()
