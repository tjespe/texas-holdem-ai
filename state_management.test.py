from typing import Iterable
import unittest
from Card import Card
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
            pot=0,
            current_player_i=1,
            current_bets=(0, 0),
            folded_players=(False, False),
            player_has_played=(True, True),
            first_better_i=0,
            big_blind=2,
        )
        new_state = add_cards(state, (0, 1, 2))
        self.assertEqual(new_state.public_cards, (0, 1, 2))
        self.assertEqual(new_state.current_bets, (0, 0))
        self.assertEqual(new_state.player_has_played, (False, False))

    def test_add_turn(self):
        state = State(
            public_cards=(0, 1, 2),
            player_piles=(100, 100),
            pot=1000,
            current_player_i=1,
            current_bets=(10, 10),
            folded_players=(False, False),
            first_better_i=0,
            big_blind=2,
            player_has_played=(True, True),
        )
        new_state = add_cards(state, (3, 4))
        self.assertEqual(new_state.public_cards, (0, 1, 2, 3, 4))
        self.assertEqual(new_state.current_bets, (0, 0))
        self.assertEqual(new_state.player_has_played, (False, False))

    def test_add_river(self):
        state = State(
            public_cards=(0, 1, 2, 3),
            player_piles=(100, 100, 100),
            pot=200,
            current_player_i=2,
            current_bets=(10, 0, 0),
            player_has_played=(True, True, False),
            folded_players=(False, True, False),
            first_better_i=0,
            big_blind=2,
        )
        new_state = add_cards(state, (4,))
        self.assertEqual(new_state.public_cards, (0, 1, 2, 3, 4))
        self.assertEqual(new_state.current_bets, (0, 0))
        self.assertEqual(new_state.player_has_played, (False, False))

    def _vectorization(self):
        state = State(
            public_cards=(0, 1, 2, 3, 4),
            player_piles=(100, 200, 300, 400),
            pot=200,
            current_player_i=2,
            current_bets=(10, 0, 0, 0),
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
        self.assertEqual(state.current_bets, new_state.current_bets)
        self.assertEqual(state.folded_players, new_state.folded_players)
        self.assertEqual(state.first_better_i, new_state.first_better_i)
        self.assertEqual(state.n_players, new_state.n_players)
        self.assertEqual(state, new_state)


if __name__ == "__main__":
    unittest.main()
