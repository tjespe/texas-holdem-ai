import numpy as np
from cpp_poker.cpp_poker import Hand, CardCollection
from PlayerABC import Player
from resolver import generate_uniform_ranges, resolve


class ResolverPlayer(Player):
    """
    This player resolves a full game tree to determine the best action.
    """

    def __init__(self, name: str = "Resa", max_successors=4, simulations=100, max_depth=100, end_stage="terminal"):
        super().__init__()
        self.name = name
        self.ranges = None
        self._hand_index = None
        self.max_successors = max_successors
        self.simulations = simulations
        self.max_depth = max_depth
        self.end_stage = end_stage

    @property
    def hand_index(self):
        if self._hand_index is None:
            hand_cards = CardCollection(self.hand)
            for i, hand in enumerate(Hand.COMBINATIONS):
                if hand_cards == hand.get_cards():
                    self._hand_index = i
                    break
        return self._hand_index

    def play(self, state) -> int:
        if self.ranges is None:
            self.ranges = generate_uniform_ranges(state)
        action, child_state, self.ranges = resolve(
            state,
            self.ranges,
            end_stage=self.end_stage,
            end_depth=self.max_depth,
            max_successors=self.max_successors,
            simulations=self.simulations,
        )
        return action
