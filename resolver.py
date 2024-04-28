from typing import Union
import numpy as np
import pandas as pd
from State import State
from StateNode import StateNode
from cpp_poker.cpp_poker import Hand, CardCollection
from neural_net import to_X_and_Y
from datetime import datetime


def generate_uniform_ranges(state: State):
    r = np.ones(len(Hand.COMBINATIONS))
    table = CardCollection(state.public_cards)
    for i, hand in enumerate(Hand.COMBINATIONS):
        if hand.intersects(table):
            r[i] = 0
    r /= r.sum()
    return [r.copy() for _ in range(state.n_players)]


def resolve(
    state: State,
    ranges: list[np.ndarray],
    end_stage: State.StageType,
    end_depth: int,
    max_successors_at_action_nodes=5,
    max_successors_at_chance_nodes=100,
    max_simulations=10_000,
    strat_convergence_threshold=1,
    convergence_lookback=20,
    hand_index=None,
):
    """
    Resolve a state using the CFR algorithm.

    Args:
        state: The state to resolve.
        end_stage: The stage at which to stop resolving (in Texas Hold Em: preflop, flop, etc.)
        end_depth: The tree depth at which to stop resolving, and use NN instead.
        ranges: The ranges per player (in Texas Hold Em: the probability distribution over possible hole pairs). Can be None if uninformed, in which case the ranges are assumed to be uniform.
        max_successors: The maximum number of successors to generate for each state.
        max_simulations: The number of simulations to run.
        hand_index: The index of the hand in the Hand.COMBINATIONS list, if known.
    """
    print("Generating tree")
    root = StateNode(
        state,
        end_stage,
        end_depth,
        max_successors_at_action_nodes,
        max_successors_at_chance_nodes,
    )
    value_vectors = []
    strategies = []
    for t in range(max_simulations):
        subtree_traversal_rollout(
            root, ranges, state.current_player_i, print_values=True
        )
        update_strategy(root, print_details=True)
        print("Possible actions:")
        for i, (action, child) in enumerate(root.children):
            print(i, action)
        print("Adding strategy to cache", root.strategy)
        strategies.append(root.strategy)
        print("Adding values to cache", root.values)
        value_vectors.append(root.values)
        strat_diff = np.abs(
            root.strategy - np.mean(strategies[-convergence_lookback:], axis=0)
        ).sum()
        print(t, "Strat diff:", strat_diff)
        if strat_diff < strat_convergence_threshold and t > 10:
            break
    if t == max_simulations - 1:
        print("Warning: CFR did not converge")
    strategies_per_hand = np.mean(strategies, axis=0)
    if hand_index:
        strategy = strategies_per_hand[hand_index]
    else:
        strategy = ranges[state.current_player_i] @ strategies_per_hand
    print("Strategy:", strategy)
    action_i = np.random.choice(len(strategy), p=strategy)
    action, child_state = root.children[action_i]
    updated_ranges = [r.copy() for r in ranges]
    updated_ranges[state.current_player_i] = bayesian_update(
        updated_ranges[state.current_player_i], action_i, strategies_per_hand
    )
    mean_values = np.array(value_vectors).mean(axis=0)
    root.values = mean_values
    return (
        action,
        child_state,
        updated_ranges,
        root.to_df_row(ranges, state.current_player_i),
    )


def subtree_traversal_rollout(
    node: StateNode, ranges: list[np.ndarray], perspective: int, print_values=False
):
    """
    Recursively traverse the tree, updating the values and strategies of the nodes.

    Args:
        node: The node to traverse.
        ranges: The ranges per player (in Texas Hold Em: the probability distribution over possible hole pairs).
        perspective: The player for which to update the values and strategies.
    """
    if node.state.is_terminal:
        payoff = ranges[perspective] @ node.get_utility_matrix(perspective)
        # Scale payoff by the pot size/game size to make it comparable across different games
        payoff *= node.state.pot / node.state.game_size
        node.values[:] = -payoff
        node.values[perspective] = payoff
        if print_values:
            print("Set values for terminal state to", node.values)
        if np.isnan(node.values).any():
            print("Payoff", payoff)
            print("Ranges", ranges)
            raise ValueError("Nan values found in terminal node")
    elif not node.children:
        node.values = ml_model(node.state)
    elif not node.state.all_players_are_done:
        # Player P is the acting player
        P = node.state.current_player_i
        values_per_child = np.full(
            (len(node.children), node.state.n_players, len(Hand.COMBINATIONS)), np.nan
        )
        for action_i, (action, child) in enumerate(node.children):
            child_ranges = [r.copy() for r in ranges]
            child_ranges[P] = bayesian_update(ranges[P], action_i, node.strategy)
            subtree_traversal_rollout(child, child_ranges, perspective)
            values_per_child[action_i] = child.values  # (p, h)
        # node.strategy has shape (h, a), add an axis to make it (h, a, 1) for broadcasting
        strategy_expanded = node.strategy[:, :, np.newaxis]

        # values_per_child has shape (a, p, h), transpose it to (h, a, p) to align for multiplication
        values_per_child_transposed = np.transpose(values_per_child, (2, 0, 1))

        # Multiply, which will broadcast strategy_expanded across the p dimension
        # After multiplication, sum over the action axis (axis=1) to collapse the actions
        # The resulting shape will be (h, p)
        expected_values = np.sum(
            strategy_expanded * values_per_child_transposed, axis=1
        )

        # The final output shape (p, h) aligns with the pseudo code's structure where
        # there's no direct multiplication with the range at this stage.
        node.values = expected_values.T
        if np.isnan(node.values).any():
            print("Values per child", values_per_child)
            raise ValueError("Nan values found in child of player action node")
        if print_values:
            print("Set values for player action state to", node.values)
    else:
        # This is a chance node
        values_per_child = np.zeros(
            (len(node.children), node.state.n_players, len(Hand.COMBINATIONS))
        )
        for i, (action, child) in enumerate(node.children):
            subtree_traversal_rollout(child, ranges, perspective)
            values_per_child[i] = child.values
        node.values = values_per_child.mean(axis=0)
        if print_values:
            print("Set values for chance state to", node.values)
        if np.isnan(node.values).any():
            print("Values per child", values_per_child)
            raise ValueError("Nan values found in children of chacne node")


def bayesian_update(r: np.ndarray, action_i, strategy: np.ndarray):
    """
    Update the range using Bayes' theorem, where:
    prob(state | act) = (prob(act | state) * prob(state)) / prob(act)

    Args:
        r (h, ): The probability distribution over different hidden states (in Texas Hold Em: hole pairs)
        action_i: The index of the action taken relative to the columns in the strategy matrix.
        strategy (h, a): The strategy matrix giving the probability of taking each action with each possible hole pair (prob(act | pair)).

    Returns:
        The updated range (prob(state | act)).
    """

    prob_act_given_state = strategy[:, action_i]  # (h, )
    prob_act = r @ prob_act_given_state  # (h, ) @ (h, ) = (1, )
    if prob_act == 0:
        print("r", r)
        print("prob_act_given_state", prob_act_given_state)
        print("prob_act_given_state.sum()", prob_act_given_state.sum())
        print("NBNBNBNBNBNNB: Zero probability of taking this action")
    return (prob_act_given_state * r) / prob_act


def update_strategy(node: StateNode, print_details=False):
    if not node.children:
        # This is a leaf node, so there are no regrets to use for updating the strategy.
        return
    for action, child in node.children:
        update_strategy(child)
    if node.state.all_players_are_done:
        # There is no acting player
        return
    P = node.state.current_player_i
    prev_regrets = node.regrets.copy()
    node.regrets += np.array(
        # (a, h)
        [
            # (h, ) - (h, ) = (h, )
            child.values[P] - node.values[P]
            for action, child in node.children
        ],
    ).T  # (h, a)
    positive_regrets = np.maximum(node.regrets, 0)  # (h, a)
    # Make regret_sums a (h, a) matrix where each row is the sum of the positive regrets for that hand
    regret_sums = positive_regrets.sum(axis=1).repeat(node.regrets.shape[1]).reshape(
        node.regrets.shape
    )
    print("Regret sums", regret_sums)
    print("Regret sums shape", regret_sums.shape)
    print("Positive regrets shape", positive_regrets.shape)
    if positive_regrets[:, 0].sum() == 0:
        fold_action, fold_child = node.children[0]
        assert fold_action == 0
        print("∑∑∑∑∑∑∑∑∑∑∑∑ DETECTED 0 REGRETS FOR FOLDING ∑∑∑∑∑∑∑∑∑∑∑∑∑")
        print("Values at node were", node.values)
        print("Min value of hands at node", node.values[P].min())
        print("Mean value of hands at node", node.values[P].mean())
        print("Value at folding node", fold_child.values[P])
        diff = fold_child.values[P] - node.values[P]
        print("Difference in value", diff)
        print("Max diff", diff.max())
        print("Min diff", diff.min())
        prev_pos_regret_folding_hands = np.argwhere(prev_regrets[:, 0] > 0)
        print("Previously positive regrets of folding at hands", prev_regrets[prev_pos_regret_folding_hands, 0])
        print("Delta at those hands", diff[prev_pos_regret_folding_hands].flatten())
        print("Regrets for those hands now", node.regrets[prev_pos_regret_folding_hands, 0])
        print("Positive regrets:", positive_regrets)
        print("Regret sums:", regret_sums)
        print("Strategy was", node.strategy)
        print("Player has played?", node.state.player_has_played)
        print("State was", node.state.get_cli_repr())
    node.strategy = np.where(
        (regret_sums > 0) & (positive_regrets > 0),
        positive_regrets / regret_sums,
        node.strategy,
    )
    node.strategy /= node.strategy.sum(axis=1, keepdims=True)
    print("Updating parts of strategy where regret sums are positive, i.e.", regret_sums > 0)
    if (node.strategy[:, 0] == 0).all():
        raise Exception("The probability of folding is 0 regardless of hand")
    if print_details:
        print("Updated strategy to", node.strategy)
