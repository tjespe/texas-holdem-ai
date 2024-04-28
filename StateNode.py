import numpy as np
import pandas as pd
from Deck import Deck
from cpp_poker.cpp_poker import Hand, Oracle, CardCollection
from State import State
from state_management import generate_successor_states


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

    # (h, h) The utility of each hand against each other hand
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
        self.values = np.full((state.n_players, len(Hand.COMBINATIONS)), np.nan)
        self.children = []
        self.strategy = None
        self.regrets = None
        self._utility_matrix = parent._utility_matrix if parent is not None else None
        print(
            "Creating StateNode for", state.stage, "with max_depth", max_depth, end="\r"
        )
        if len(self.state.public_cards) == 5 and self._utility_matrix is None:
            self._utility_matrix = Oracle.generate_utility_matrix(
                CardCollection(self.state.public_cards)
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
            self.strategy = np.ones((len(Hand.COMBINATIONS), len(self.children))) / len(
                self.children
            )
            self.regrets = np.zeros((len(Hand.COMBINATIONS), len(self.children)))

    def get_utility_matrix(self, perspective: int):
        two_players_active = sum(self.state.player_is_active) >= 2
        if not two_players_active:
            self._utility_matrix = Oracle.generate_utility_matrix(
                CardCollection(self.state.public_cards), False
            )
            if not self.state.player_is_active[perspective]:
                self._utility_matrix = -self._utility_matrix
        elif self._utility_matrix is None:
            self._utility_matrix = Oracle.generate_utility_matrix(
                CardCollection(self.state.public_cards)
            )
        return self._utility_matrix

    def to_df_row(self, ranges: list[np.ndarray], perspective: int):
        """
        Returns a pandas DataFrame representation of the node.
        :param ranges: The ranges per player (in Texas Hold Em: the probability distribution over possible hole pairs).
        :param perspective: The player whose perspective to use.
        """
        if np.isnan(self.values).all():
            return None
        if sum(self.state.player_is_active) != 2:
            return None
        if not self.state.player_is_active[perspective]:
            return None
        player_range = ranges[perspective]
        opponent = next(
            i
            for i, active in enumerate(self.state.player_is_active)
            if active and i != perspective
        )
        opponent_range = ranges[opponent]
        player_values = self.values[
            perspective
        ]  # (h,): The value of having each hand at this node for the player
        player_bet = self.state.current_bets[perspective]
        player_bet_in_round = self.state.bet_in_round[perspective]
        opponent_bet = self.state.current_bets[opponent]
        opponent_bet_in_round = self.state.bet_in_round[opponent]
        player_turn = self.state.current_player_i == perspective
        player_has_bet = self.state.player_has_played[perspective]
        opponent_has_bet = self.state.player_has_played[opponent]
        public_cards_one_hot = np.zeros(52)
        for card in self.state.public_cards:
            public_cards_one_hot[card] = 1
        arrays = [
            player_range,
            opponent_range,
            player_values,
            public_cards_one_hot,
        ]
        other_props = [
            player_bet,
            player_bet_in_round,
            opponent_bet,
            opponent_bet_in_round,
            player_turn,
            player_has_bet,
            opponent_has_bet,
            self.state.pot,
            self.state.game_size,
            self.state.stage,
        ]
        arr = [item for array in arrays for item in array] + other_props
        return arr

    @classmethod
    def get_df_headers(cls):
        headers = []
        for i in range(len(Hand.COMBINATIONS)):
            headers.append(f"prob_P_has_hand_{i}")
        for i in range(len(Hand.COMBINATIONS)):
            headers.append(f"prob_O_has_hand_{i}")
        for i in range(len(Hand.COMBINATIONS)):
            headers.append(f"value_of_hand_{i}")
        for i in range(52):
            headers.append(f"public_card_{i}")
        headers.append("player_bet")
        headers.append("player_bet_in_round")
        headers.append("opponent_bet")
        headers.append("opponent_bet_in_round")
        headers.append("player_turn")
        headers.append("player_has_bet")
        headers.append("opponent_has_bet")
        headers.append("pot")
        headers.append("game_size")
        headers.append("stage")
        return headers
