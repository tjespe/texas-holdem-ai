import numpy as np
from Deck import Deck
from oracle import POSSIBLE_HOLE_PAIRS
from State import State
from state_management import generate_successor_states
import oracle


class StateNode:
    """
    Class used by the resolver to store states with children, and relevant info
    such as strategies and values.
    """

    state: State
    parent: "StateNode"
    deck: set[int]

    # List of (action, StateNode) tuples
    children: list[tuple[int, "StateNode"]]

    # (h, a) The probability of taking each action at this node for each hand
    strategy: np.ndarray

    # (p, h) The value of having each hand at this node for each player
    values: np.ndarray

    # (h, a) The regret of not having taken each action at this node
    regrets: np.ndarray

    # (h,) The utility of having each hand at this node for the player whose perspective we have
    _utility_matrix: np.ndarray = None

    def __init__(
        self,
        state: State,
        end_stage: State.StageType,
        max_depth: int = 0,
        max_successors=100,
        parent: "StateNode" = None,
        deck=None,
    ):
        if deck is None:
            deck = set(range(52))
        deck -= set(state.public_cards)
        self.deck = deck
        self.state = state
        self.parent = parent
        self.values = np.full((state.n_players, len(POSSIBLE_HOLE_PAIRS)), np.nan)
        self.children = []
        self.strategy = None
        self.regrets = None
        print(
            "Creating StateNode for", state.stage, "with max_depth", max_depth, end="\r"
        )
        if end_stage != state.stage and max_depth > 0 and not state.is_terminal:
            self.children = [
                (
                    action,
                    StateNode(
                        successor, end_stage, max_depth - 1, max_successors, self, deck
                    ),
                )
                for action, successor in generate_successor_states(
                    state, max_successors
                )
            ]
            self.strategy = np.ones(
                (len(POSSIBLE_HOLE_PAIRS), len(self.children))
            ) / len(self.children)
            self.regrets = np.zeros((len(POSSIBLE_HOLE_PAIRS), len(self.children)))

    @property
    def utility_matrix(self):
        if self._utility_matrix is None:
            self._utility_matrix = oracle.generate_utility_matrix(self.state)
        return self._utility_matrix
