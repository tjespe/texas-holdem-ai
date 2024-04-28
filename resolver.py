import numpy as np
from State import State
from StateNode import StateNode
from cpp_poker.cpp_poker import Hand, CardCollection


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
    max_successors=10,
    simulations=100,
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
        simulations: The number of simulations to run.
        hand_index: The index of the hand in the Hand.COMBINATIONS list, if known.
    """
    print("Generating tree")
    root = StateNode(state, end_stage, end_depth, max_successors)
    strategies = []
    for t in range(simulations):
        print("Simulation", t, "of", simulations, end="\r")
        subtree_traversal_rollout(root, ranges, state.current_player_i)
        update_strategy(root)
        strategies.append(root.strategy)
    strategies_per_hand = np.mean(strategies, axis=0)
    if hand_index:
        strategy = strategies_per_hand[hand_index]
    else:
        strategy = ranges[state.current_player_i] @ strategies_per_hand
    action_i = np.random.choice(len(strategy), p=strategy)
    action, child_state = root.children[action_i]
    updated_ranges = [r.copy() for r in ranges]
    updated_ranges[state.current_player_i] = bayesian_update(
        updated_ranges[state.current_player_i], action_i, strategies_per_hand
    )
    print(
        "Update to ranges:",
        updated_ranges[state.current_player_i] - ranges[state.current_player_i],
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
    if node.state.is_terminal:
        payoff = ranges[perspective] @ node.get_utility_matrix(perspective)
        node.values[:] = (
            -payoff
        )  # TODO: what is the correct payoff for the other players if there are more than 2 players?
        node.values[perspective] = payoff
    elif not node.children:
        payoff = ranges[perspective] @ ml_model(node.state)
        node.values[:] = -payoff
        node.values[perspective] = payoff
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
    else:
        # This is a chance node
        values_per_child = np.zeros(
            (len(node.children), node.state.n_players, len(Hand.COMBINATIONS))
        )
        for i, (action, child) in enumerate(node.children):
            subtree_traversal_rollout(child, ranges, perspective)
            values_per_child[i] = child.values
        node.values = values_per_child.mean(axis=0)


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
