import unittest

import numpy as np

from Card import POSSIBLE_HOLE_PAIRS, Card
from State import State
from StateNode import StateNode
from resolver import bayesian_update, update_strategy

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


class BayesianUpdateTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.strategy = np.array([
            [0.6, 0.4],  # Strategy for hole pair 1
            [0.7, 0.3],  # Strategy for hole pair 2
        ])
        self.range_ = np.array([0.5, 0.5])  # Initial range

    def test_bayesian_update_valid_probability(self):
        updated_range = bayesian_update(self.range_, 0, self.strategy)
        self.assertTrue(np.all(updated_range >= 0) and np.all(updated_range <= 1), "Updated range contains invalid probabilities.")
        self.assertAlmostEqual(np.sum(updated_range), 1, "Updated range does not sum to 1.")

    def test_bayesian_update_rule(self):
        # We manually calculate the updated range for a specific case to test against.
        action_i = 0
        prob_act = np.dot(self.range_, self.strategy[:, action_i])
        expected_update = (self.strategy[:, action_i] * self.range_) / prob_act
        updated_range = bayesian_update(self.range_, action_i, self.strategy)
        np.testing.assert_almost_equal(updated_range, expected_update, err_msg="Bayesian update rule not applied correctly.")

    def test_bayesian_update_sensitivity(self):
        # Test that the update changes with different priors.
        different_prior = np.array([0.8, 0.2])
        updated_range_original = bayesian_update(self.range_, 0, self.strategy)
        updated_range_different = bayesian_update(different_prior, 0, self.strategy)
        self.assertFalse(np.array_equal(updated_range_original, updated_range_different), "Updated range does not reflect different priors.")

    def test_bayesian_update_action_sensitivity(self):
        # Test that the update is sensitive to the action taken.
        updated_range_action_0 = bayesian_update(self.range_, 0, self.strategy)
        updated_range_action_1 = bayesian_update(self.range_, 1, self.strategy)
        self.assertFalse(np.array_equal(updated_range_action_0, updated_range_action_1), "Updated range does not reflect different actions.")



if __name__ == "__main__":
    unittest.main()
