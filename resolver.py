import sys
from typing import Union
import numpy as np
import pandas as pd
from State import State
from StateNode import StateNode
from cpp_poker.cpp_poker import Hand, CardCollection
from neural_net import to_X_and_Y
from datetime import datetime

np.set_printoptions(threshold=50)


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
    min_simulations=1,
    strat_convergence_threshold=0.02,
    patience=10,
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
    print("Possible actions:")
    for i, (action, child) in enumerate(root.children):
        print(i, action)
    errors = []
    for t in range(max_simulations):
        subtree_traversal_rollout(root, ranges, state.current_player_i)
        update_strategy(root)
        if t % 10 == 0:
            # print("Current strategy", root.strategy)
            pass
        strategies.append(root.strategy)
        value_vectors.append(root.values)
        if t >= min_simulations:
            strat_diff = np.abs(root.strategy - np.mean(strategies, axis=0)).sum()
            percentage_off = strat_diff / root.strategy.sum()
            errors.append(percentage_off)
            print("Iteration:", t, "Strat diff:", strat_diff, "Percentage off:", percentage_off)
            if percentage_off < strat_convergence_threshold:
                print(
                    "Breaking because the percentage error is less than",
                    strat_convergence_threshold,
                )
                break
            if len(errors) > patience:
                if np.all(np.diff(errors[-patience:]) > 0):
                    print("Breaking because the error has increased for", patience, "iterations")
                    print("Latest errors:", errors[-patience:])
                    print("Worsening:", np.diff(errors[-patience:]))
                    break
        else:
            print("Iteration:", t, end="\r")
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
    print("Mean values (target var for NN):", mean_values)
    print("Max of mean values:", mean_values.max())
    print("Min of mean values:", mean_values.min())
    root.values = mean_values
    return (
        action,
        child_state,
        updated_ranges,
        root.to_df_row(ranges, state.current_player_i),
    )


def subtree_traversal_rollout(
    node: StateNode, ranges: list[np.ndarray], perspective: int
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
        if np.isnan(node.values).any():
            print("Payoff", payoff)
            print("Ranges", ranges)
            raise ValueError("Nan values found in terminal node")
    elif not node.children:
        node.values = ml_model(node.state)
    elif not node.state.all_players_are_done:
        # Player P is the acting player
        P = node.state.current_player_i
        O = next(
            i
            for i in range(node.state.n_players)
            if i != P and node.state.player_is_active[i]
        )
        node.values = np.zeros((node.state.n_players, len(Hand.COMBINATIONS)))
        for i, (action, child) in enumerate(node.children):
            child_ranges = ranges.copy()
            child_ranges[P] = bayesian_update(child_ranges[P], i, node.strategy)
            subtree_traversal_rollout(child, child_ranges, perspective)
            for h in range(len(Hand.COMBINATIONS)):
                node.values[P, h] = child.values[P, h] * node.strategy[h, i]
                node.values[O, h] = child.values[O, h] * node.strategy[h, i]
        if np.isnan(node.values).any():
            if np.isnan(node.values).all():
                print("All values are nan")
            print(node.values)
            raise ValueError("Nan values found in children of action node")
    else:
        # This is a chance node
        for i, (action, child) in enumerate(node.children):
            subtree_traversal_rollout(child, ranges, perspective)
            for h in range(len(Hand.COMBINATIONS)):
                node.values[:, h] += child.values[:, h] / len(node.children)
        if np.isnan(node.values).any():
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
        raise Exception("NBNBNBNBNBNNB: Zero probability of taking this action")
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
    regret_sums = positive_regrets.sum(axis=1, keepdims=True)  # (h, 1)
    node.strategy = np.where(
        regret_sums > 0,
        positive_regrets / regret_sums,
        node.strategy,
    )
    node.strategy /= node.strategy.sum(axis=1, keepdims=True)
    if (node.strategy[:, 0] == 0).all():
        raise Exception("The probability of folding is 0 regardless of hand")
