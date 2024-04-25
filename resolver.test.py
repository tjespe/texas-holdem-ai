import unittest

import numpy as np

from Card import POSSIBLE_HOLE_PAIRS, Card
from State import State
from StateNode import StateNode
from resolver import update_strategy

example_terminal_state = State(
    public_cards=(0, 1, 2, 3, 4),
    player_piles=(100, 100),
    current_player_i=0,
    current_bets=(100, 100),
    bet_in_round=(100, 100),
    player_has_played=(True, True),
    folded_players=(False, False),
    first_better_i=0,
    big_blind=2,
)

example_non_terminal_state = State(
    public_cards=(0, 1, 2),
    player_piles=(100, 100),
    current_player_i=1,
    current_bets=(100, 100),
    bet_in_round=(100, 100),
    player_has_played=(True, False),
    folded_players=(False, False),
    first_better_i=0,
    big_blind=2,
)


class UpdateStrategyTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.example_node = StateNode(
            state=example_non_terminal_state,
            end_stage="river",
            max_depth=3,
            max_successors=3,
        )
        np.random.seed(0)
        self.example_node.strategy = np.random.rand(
            len(POSSIBLE_HOLE_PAIRS), len(self.example_node.children)
        )
        self.example_node.strategy /= np.sum(self.example_node.strategy, axis=1)[
            :, np.newaxis
        ]
        self.example_node.values = np.random.rand(
            self.example_node.state.n_players, len(POSSIBLE_HOLE_PAIRS)
        )
        for action, child in self.example_node.children:
            child.values = np.random.rand(
                self.example_node.state.n_players, len(POSSIBLE_HOLE_PAIRS)
            )

    def test_update_strategy_terminal_node(self):
        node = StateNode(
            state=example_terminal_state, end_stage=example_terminal_state.stage
        )
        update_strategy(node)
        assert node.regrets is None or np.all(node.regrets == 0)

    def test_update_strategy_normalization(self):
        update_strategy(self.example_node)
        for i, h in enumerate(POSSIBLE_HOLE_PAIRS):
            strategy_sum = np.sum(self.example_node.strategy[i])
            assert np.isclose(
                strategy_sum, 1
            ), f"Strategy not normalized for hole pair: {Card.get_cli_repr_for_cards(h)}\n{self.example_node.strategy[i]}"

    def test_update_strategy_positive_regrets(self):
        update_strategy(self.example_node)
        assert np.all(
            self.example_node.strategy >= 0
        ), "Strategy contains negative probabilities"

    def test_update_strategy_effect(self):
        old_strategy = self.example_node.strategy.copy()
        update_strategy(self.example_node)
        assert not np.array_equal(
            self.example_node.strategy, old_strategy
        ), "Strategy didn't update with positive regret.\nOld strategy = New strategy = \n" + str(
            self.example_node.strategy
        )


if __name__ == "__main__":
    unittest.main()
