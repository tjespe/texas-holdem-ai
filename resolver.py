import sys
from typing import Union
import numpy as np
import pandas as pd
from State import State
from StateNode import StateNode
from cpp_poker.cpp_poker import Hand, CardCollection
from neural_net import to_X_and_Y
from datetime import datetime

from nn.run_nn_model import estimate_value_vector, estimate_value_vectors

np.set_printoptions(threshold=50)


def generate_uniform_ranges(state: State):
    r = np.ones(len(Hand.COMBINATIONS))
    table = CardCollection(state.public_cards)
    for i, hand in enumerate(Hand.COMBINATIONS):
        if hand.intersects(table):
            r[i] = 0
    r /= r.sum()
    return [r.copy() for _ in range(state.n_players)]


def debug_print(*args, **kwargs):
    return # Remove this line to enable debug print
    kwargs["file"] = sys.stderr
    return __builtins__.print(*args, **kwargs)


def resolve(
    state: State,
    ranges: list[np.ndarray],
    end_stage: State.StageType,
    end_depth: int,
    end_sub_stage: Union[State.SubStageType, None] = None,
    max_successors_at_action_nodes=5,
    max_successors_at_chance_nodes=100,
    max_simulations=10_000,
    min_simulations=1,
    strat_convergence_threshold=0.02,
    patience=10,
    hand_index=None,
    cached_root: StateNode = None,
    sliding_window=None
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
        sliding_window: If this is set, only the last `sliding_window` iterations are used to calculate the strategy.
    """
    debug_print("\n\n@@@@@ STARTING RESOLUTION @@@@@")
    generate_nodes_to = {
        "end_stage": end_stage,
        "end_sub_stage": end_sub_stage,
        "max_depth": end_depth,
    }
    debug_print("ARGS:", generate_nodes_to)
    if end_stage and state.is_at_or_past_stage(end_stage, end_sub_stage):
        generate_nodes_to["end_stage"] = None
        generate_nodes_to["max_depth"] = 1
    debug_print("GENERATING NODES TO:", generate_nodes_to)
    if cached_root is None:
        root = StateNode(
            state,
            max_successors_at_action_nodes=max_successors_at_action_nodes,
            max_successors_at_chance_nodes=max_successors_at_chance_nodes,
            **generate_nodes_to,
        )
    else:
        root = cached_root
        root.reset_values()
    if not root.children:
        raise Exception("No children were generated for the root node")
    debug_print("\n\nGENERATED TREE:")
    debug_print(root.get_tree_str())
    value_vectors = []
    strategies = []
    debug_print("\nPossible actions:")
    for i, (action, child) in enumerate(root.children):
        debug_print(i, action)
    errors = []
    debug_print("\n---- Root node ----")
    debug_print("| Stage:", root.state.stage)
    debug_print("| Sub stage:", root.state.sub_stage)
    if sliding_window is None:
        sliding_window = max_simulations
    for t in range(max_simulations):
        _precompute_leaf_node_values(root, ranges, state.current_player_i)
        subtree_traversal_rollout(root, ranges, state.current_player_i)
        update_strategy(root)
        if t % 10 == 0:
            # print("Current strategy", root.strategy)
            pass
        strategies.append(root.strategy)
        value_vectors.append(root.values)
        if t >= min_simulations:
            strat_diff = np.abs(root.strategy - np.mean(strategies[-sliding_window:], axis=0)).sum()
            percentage_off = strat_diff / root.strategy.sum()
            errors.append(percentage_off)
            print(
                "Iteration:",
                t,
                "Strat diff:",
                strat_diff,
                "Percentage off:",
                percentage_off,
            )
            if percentage_off < strat_convergence_threshold:
                print(
                    "Breaking because the percentage error is less than",
                    strat_convergence_threshold,
                )
                break
            if len(errors) > patience:
                if np.all(np.diff(errors[-patience:]) > 0):
                    print(
                        "Breaking because the error has increased for",
                        patience,
                        "iterations",
                    )
                    print("Latest errors:", errors[-patience:])
                    print("Worsening:", np.diff(errors[-patience:]))
                    break
        else:
            print("Iteration:", t, end="\r")
    if t == max_simulations - 1:
        print("Warning: CFR did not converge")
    strategies_per_hand = np.mean(strategies[-sliding_window:], axis=0)
    if hand_index:
        strategy = strategies_per_hand[hand_index]
        print("Strategy for hand:", strategy)
    else:
        strategy = ranges[state.current_player_i] @ strategies_per_hand
        print("Strategy given range:", strategy)
    action_i = np.random.choice(len(strategy), p=strategy)
    action, child_state = root.children[action_i]
    updated_ranges = [r.copy() for r in ranges]
    updated_ranges[state.current_player_i] = bayesian_update(
        updated_ranges[state.current_player_i], action_i, strategies_per_hand
    )
    mean_values = np.array(value_vectors).mean(axis=0)
    debug_print("Mean values (target var for NN):", mean_values)
    debug_print("Max of mean values:", mean_values.max())
    debug_print("Min of mean values:", mean_values.min())
    root.values = mean_values
    return (
        action,
        child_state,
        updated_ranges,
        root,
    )

def _build_leaf_node_list(
    node: StateNode, ranges: list[np.ndarray], perspective: int
):
    nodes = []
    ranges_list = []
    for i, (action, child) in enumerate(node.children):
        updated_ranges = ranges.copy()
        if node.state.action_required:
            updated_ranges[node.state.current_player_i] = bayesian_update(
                updated_ranges[node.state.current_player_i], i, node.strategy
            )
        if child.children:
            child_nodes, child_ranges_list = _build_leaf_node_list(
                child, updated_ranges, perspective
            )
            nodes.extend(child_nodes)
            ranges_list.extend(child_ranges_list)
        elif not child.state.is_terminal:
            ranges_list.append(updated_ranges)
            nodes.append(child)
    return nodes, ranges_list

def _precompute_leaf_node_values(root: StateNode, ranges: list[np.ndarray], perspective: int):
    leaf_nodes, ranges_list = _build_leaf_node_list(root, ranges, perspective)
    payoff_vectors = estimate_value_vectors(leaf_nodes, ranges_list, perspective)
    for i, node in enumerate(leaf_nodes):
        payoff = payoff_vectors[i]
        payoff *= node.state.pot / node.state.game_size
        node.values[:] = -payoff
        node.values[perspective] = payoff
        node.values_calculated_ahead = True

def subtree_traversal_rollout(
    node: StateNode, ranges: list[np.ndarray], perspective: int, indentation=0
):
    """
    Recursively traverse the tree, updating the values and strategies of the nodes.

    Args:
        node: The node to traverse.
        ranges: The ranges per player (in Texas Hold Em: the probability distribution over possible hole pairs).
        perspective: The player for which to update the values and strategies.
    """
    ind_str = "|" + "    " * indentation
    debug_print("|" + "----" * indentation, "Traversing node:")
    debug_print(ind_str, "Stage:", node.state.stage)
    debug_print(ind_str, "Sub stage:", node.state.sub_stage)

    # Decide what to do based on the type of node
    if node.state.is_terminal:
        debug_print(ind_str, "Getting util matrix because we are at a terminal node:")
        debug_print(ind_str, "Players have played:", node.state.player_has_played)
        debug_print(ind_str, "Players are folded:", node.state.player_is_folded)
        debug_print(ind_str, "Player bets in stage:", node.state.bet_in_stage)
        payoff = ranges[perspective] @ node.get_utility_matrix(perspective)
        # Scale payoff by the pot size/game size to make it comparable across different games
        payoff *= node.state.pot / node.state.game_size
        node.values[:] = -payoff
        node.values[perspective] = payoff
        if np.isnan(node.values).any():
            debug_print(ind_str, "Payoff", payoff)
            debug_print(ind_str, "Ranges", ranges)
            raise ValueError("Nan values found in terminal node")
    elif not node.children:
        debug_print(
            ind_str,
            "Running ML model for sub stage",
            node.state.sub_stage,
            "in stage",
            node.state.stage,
            "for player",
            perspective,
        )
        if node.values_calculated_ahead:
            debug_print(ind_str, "Values already calculated ahead")
            node.values_calculated_ahead = False # Reset this flag
        else:
            print("Values for leaf node was not precomputed:", node.state.sub_stage, "in stage", node.state.stage, "for player", perspective)
            payoff = estimate_value_vector(node, ranges, perspective)
            payoff *= node.state.pot / node.state.game_size
            node.values[:] = -payoff
            node.values[perspective] = payoff
            if np.isnan(node.values).any():
                debug_print(ind_str, "Payoff", payoff)
                raise ValueError("Nan values found in estimated vector at leaf node")
    elif node.state.action_required:
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
            subtree_traversal_rollout(child, child_ranges, perspective, indentation + 1)
            for h in range(len(Hand.COMBINATIONS)):
                node.values[P, h] = child.values[P, h] * node.strategy[h, i]
                node.values[O, h] = child.values[O, h] * node.strategy[h, i]
        if np.isnan(node.values).any():
            if np.isnan(node.values).all():
                debug_print(ind_str, "All values are nan")
            debug_print(ind_str, node.values)
            raise ValueError("Nan values found in children of action node")
    else:
        # This is a chance node
        for i, (action, child) in enumerate(node.children):
            subtree_traversal_rollout(child, ranges, perspective, indentation + 1)
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
        debug_print("r", r)
        debug_print("prob_act_given_state", prob_act_given_state)
        debug_print("prob_act_given_state.sum()", prob_act_given_state.sum())
        raise Exception("NBNBNBNBNBNNB: Zero probability of taking this action")
    return (prob_act_given_state * r) / prob_act


def update_strategy(node: StateNode):
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
    # Disable division by zero warning
    with np.errstate(divide="ignore", invalid="ignore"):
        node.strategy = np.where(
            regret_sums > 0,
            positive_regrets / regret_sums,
            node.strategy,
        )
    node.strategy /= node.strategy.sum(axis=1, keepdims=True)
    if (node.strategy[:, 0] == 0).all():
        raise Exception("The probability of folding is 0 regardless of hand")
