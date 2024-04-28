import numpy as np
from cpp_poker.cpp_poker import Hand, CardCollection
from PlayerABC import Player
from resolver import generate_uniform_ranges, resolve


class ResolverPlayer(Player):
    """
    This player resolves a full game tree to determine the best action.
    """

    def __init__(self, name: str = "Resa"):
        super().__init__()
        self.name = name
        self.ranges = None
        self._hand_index = None

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
            end_stage="terminal",
            end_depth=100,
            max_successors=3,
            simulations=100,
        )
        return action
