import numpy as np
from cpp_poker.cpp_poker import Hand
from PlayerABC import Player
from resolver import resolve


class ResolverPlayer(Player):
    """
    This player resolves a full game tree to determine the best action.
    """

    def __init__(self, name: str = "Resa"):
        super().__init__()
        self.name = name

    def play(self, state) -> int:
        r0 = np.ones(len(len(Hand.COMBINATIONS)))
        for i, (card_a, card_b) in enumerate(len(Hand.COMBINATIONS)):
            if (
                card_a.to_index() in state.public_cards
                or card_b.to_index() in state.public_cards
            ):
                r0[i] = 0
        r0 /= r0.sum()
        initial_ranges = [r0.copy() for _ in range(state.n_players)]
        action, child_state, updated_ranges = resolve(
            state,
            initial_ranges,
            end_stage="terminal",
            end_depth=100,
            max_successors=3,
            simulations=100,
        )
        return action
