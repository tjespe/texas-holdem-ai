import numpy as np
from oracle import POSSIBLE_HOLE_PAIRS
from State import State
from StateNode import StateNode


def resolve(
    state: State,
    ranges: list[np.ndarray],
    end_stage: State.StageType,
    end_depth: int,
    max_successors=10,
    simulations=100,
):
    """
    Resolve a state using the CFR algorithm.

    Args:
        state: The state to resolve.
        ranges: The ranges per player (in Texas Hold Em: the probability distribution over possible hole pairs).
        end_stage: The stage at which to stop resolving (in Texas Hold Em: preflop, flop, etc.)
        end_depth: The tree depth at which to stop resolving, and use NN instead.
        max_successors: The maximum number of successors to generate for each state.
        initial_strategy_generator: A function that generates the initial strategy for a state.
    """
    print("Generating tree")
    root = StateNode(state, end_stage, end_depth, max_successors)
    strategies = []
    for t in range(simulations):
        print("Simulation", t, "of", simulations, end="\r")
        subtree_traversal_rollout(root, ranges, state.current_player_i)
        update_strategy(root)
        strategies.append(root.strategy)
    strategy = np.mean(strategies, axis=0)
    action_i = np.random.choice(len(strategy), p=strategy)
    action, child_state = root.children[action_i]
    updated_ranges = [ranges.copy() for _ in range(len(ranges))]
    updated_ranges[state.current_player_i] = bayesian_update(
        updated_ranges[state.current_player_i], action_i, strategy
    )
    return action, child_state, updated_ranges


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
    print("Traversing", node.state.stage, ", player", node.state.current_player_i, end="\r")
    if node.state.is_terminal:
        payoff = node.utility_matrix * ranges[perspective]
        node.values[:] = (
            -payoff
        )  # TODO: what is the correct payoff for the other players if there are more than 2 players?
        node.values[perspective] = payoff
    elif not node.children:
        payoff = ml_model(node.state) * ranges[perspective]
        node.values[:] = -payoff
        node.values[perspective] = payoff
    elif not node.state.all_players_are_done:
        # Player P is the acting player
        P = node.state.current_player_i
        values_per_child = np.full(
            (len(node.children), node.state.n_players, len(POSSIBLE_HOLE_PAIRS)), np.nan
        )
        for action_i, (action, child) in enumerate(node.children):
            child_ranges = [r.copy() for r in ranges]
            child_ranges[P] = bayesian_update(ranges[P], action_i, node.strategy)
            subtree_traversal_rollout(child, child_ranges, perspective)
            values_per_child[action_i] = child.values
        node.values = node.strategy @ values_per_child
    else:
        # This is a chance node
        values_per_child = np.zeros(
            (len(node.children), node.state.n_players, len(POSSIBLE_HOLE_PAIRS))
        )
        for i, (action, child) in enumerate(node.children):
            subtree_traversal_rollout(child, ranges, perspective)
            values_per_child[i] = child.values
        node.values = values_per_child.mean(axis=0)


def bayesian_update(r, action_i, strategy: np.ndarray):
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

    prob_act_given_state = strategy[:, action_i] # (h, )
    prob_act = r @ prob_act_given_state  # (h, ) @ (h, ) = (1, )
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
    regret_sums = positive_regrets.sum(axis=1, keepdims=True)  # (h, 1)
    node.strategy = np.where(
        regret_sums > 0,
        positive_regrets / regret_sums,
        node.strategy,
    )
