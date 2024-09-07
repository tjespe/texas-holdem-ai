import unittest

import numpy as np

from cpp_poker.cpp_poker import Card, Hand
from State import State
from StateNode import StateNode
from resolver import bayesian_update, generate_uniform_ranges, resolve, update_strategy

example_terminal_state = State(
    public_cards=(0, 1, 2, 3, 4),
    player_piles=(100, 100),
    current_player_i=0,
    bet_in_stage=(100, 100),
    bet_in_game=(100, 100),
    player_has_played=(True, True),
    player_is_folded=(False, False),
    first_better_i=0,
    big_blind=2,
)

example_non_terminal_state = State(
    public_cards=(0, 1, 2),
    player_piles=(100, 100),
    current_player_i=1,
    bet_in_stage=(100, 100),
    bet_in_game=(100, 100),
    player_has_played=(True, False),
    player_is_folded=(False, False),
    first_better_i=0,
    big_blind=2,
)

example_turn_state = State(
    public_cards=(0, 1, 2, 3),
    player_piles=(100, 100),
    current_player_i=1,
    bet_in_stage=(100, 100),
    bet_in_game=(100, 100),
    player_has_played=(True, False),
    player_is_folded=(False, False),
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
            max_successors_at_action_nodes=3,
            max_successors_at_chance_nodes=3,
        )
        np.random.seed(0)
        self.example_node.strategy = np.random.rand(
            len(Hand.COMBINATIONS), len(self.example_node.children)
        )
        self.example_node.strategy /= np.sum(self.example_node.strategy, axis=1)[
            :, np.newaxis
        ]
        self.example_node.values = np.random.rand(
            self.example_node.state.n_players, len(Hand.COMBINATIONS)
        )
        for action, child in self.example_node.children:
            child.values = np.random.rand(
                self.example_node.state.n_players, len(Hand.COMBINATIONS)
            )

    def test_update_strategy_terminal_node(self):
        node = StateNode(
            state=example_terminal_state, end_stage=example_terminal_state.stage
        )
        update_strategy(node)
        assert node.regrets is None or np.all(node.regrets == 0)

    def test_update_strategy_normalization(self):
        update_strategy(self.example_node)
        for i, h in enumerate(Hand.COMBINATIONS):
            strategy_sum = np.sum(self.example_node.strategy[i])
            assert np.isclose(
                strategy_sum, 1
            ), f"Strategy not normalized for hole pair:\n{Card.get_cli_repr_for_cards(h)}\n{self.example_node.strategy[i]}"

    def test_update_strategy_positive_regrets(self):
        update_strategy(self.example_node)
        assert np.all(
            self.example_node.strategy >= 0
        ), "Strategy contains negative probabilities"

    def test_update_strategy_effect(self):
        old_strategy = self.example_node.strategy.copy()
        update_strategy(self.example_node)
        assert not np.array_equal(self.example_node.strategy, old_strategy), (
            "Strategy didn't update with positive regret.\nOld strategy = New strategy = \n"
            + str(self.example_node.strategy)
        )


class FullResolverTest(unittest.TestCase):
    def test_full_resolver(self):
        ranges = generate_uniform_ranges(example_turn_state)
        print(ranges)
        action, child_state, updated_ranges, strats_per_hand, cached_root = resolve(
            example_turn_state,
            ranges,
            end_stage="terminal",
            end_depth=100,
            max_successors_at_action_nodes=1,
            max_successors_at_chance_nodes=1,
        )
        print("Action", action)
        print("Child state", child_state)
        print("Updated ranges", updated_ranges)
        self.assertIsNotNone(action, "No action returned.")
        self.assertIsNotNone(child_state, "No child state returned.")
        self.assertIsNotNone(updated_ranges, "No updated ranges returned.")


class UtilityMatrixTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.example_node = StateNode(
            state=example_terminal_state,
            end_stage="river",
            max_depth=3,
            max_successors_at_action_nodes=3,
            max_successors_at_chance_nodes=3,
        )
        self.example_node._utility_matrix = None

    def test_utility_matrix_two_players(self):
        self.example_node.get_utility_matrix(0)
        self.assertIsNotNone(
            self.example_node._utility_matrix,
            "Utility matrix not generated for two players.",
        )


class BayesianUpdateTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.strategy = np.array(
            [
                [0.6, 0.4],  # Strategy for hole pair 1
                [0.7, 0.3],  # Strategy for hole pair 2
            ]
        )
        self.range_ = np.array([0.5, 0.5])  # Initial range

    def test_bayesian_update_valid_probability(self):
        updated_range = bayesian_update(self.range_, 0, self.strategy)
        self.assertTrue(
            np.all(updated_range >= 0) and np.all(updated_range <= 1),
            "Updated range contains invalid probabilities.",
        )
        self.assertAlmostEqual(
            np.sum(updated_range), 1, "Updated range does not sum to 1."
        )

    def test_bayesian_update_rule(self):
        # We manually calculate the updated range for a specific case to test against.
        action_i = 0
        prob_act = np.dot(self.range_, self.strategy[:, action_i])
        expected_update = (self.strategy[:, action_i] * self.range_) / prob_act
        updated_range = bayesian_update(self.range_, action_i, self.strategy)
        np.testing.assert_almost_equal(
            updated_range,
            expected_update,
            err_msg="Bayesian update rule not applied correctly.",
        )

    def test_bayesian_update_sensitivity(self):
        # Test that the update changes with different priors.
        different_prior = np.array([0.8, 0.2])
        updated_range_original = bayesian_update(self.range_, 0, self.strategy)
        updated_range_different = bayesian_update(different_prior, 0, self.strategy)
        self.assertFalse(
            np.array_equal(updated_range_original, updated_range_different),
            "Updated range does not reflect different priors.",
        )

    def test_bayesian_update_action_sensitivity(self):
        # Test that the update is sensitive to the action taken.
        updated_range_action_0 = bayesian_update(self.range_, 0, self.strategy)
        updated_range_action_1 = bayesian_update(self.range_, 1, self.strategy)
        self.assertFalse(
            np.array_equal(updated_range_action_0, updated_range_action_1),
            "Updated range does not reflect different actions.",
        )


if __name__ == "__main__":
    unittest.main()
