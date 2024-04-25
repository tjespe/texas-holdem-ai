import numpy as np
from orcale import POSSIBLE_HOLE_PAIRS, Card
from PlayerABC import Player
import oracle
from resolver import resolve


class ResolverPlayer(Player):
    """
    This player resolves a full game tree to determine the best action.
    """

    def __init__(self, name: str = "Resa"):
        super().__init__()
        self.name = name

    def play(self, state) -> int:
        r0 = np.ones(len(POSSIBLE_HOLE_PAIRS))
        for i, (card_a, card_b) in enumerate(POSSIBLE_HOLE_PAIRS):
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
