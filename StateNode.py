import os
import numpy as np
import pandas as pd
from Deck import Deck
from cpp_poker.cpp_poker import Hand, Oracle, CardCollection
from State import State
from state_management import generate_successor_states
from datetime import datetime

run_start = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


class StateNode:
    """
    Class used by the resolver to store states with children, and relevant info
    such as strategies and values.
    """

    state: State
    parent: "StateNode"

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
        end_stage: State.StageType = None,
        end_sub_stage: State.SubStageType = None,
        max_depth: int = 0,
        max_successors_at_action_nodes=5,
        max_successors_at_chance_nodes=100,
        parent: "StateNode" = None,
    ):
        """
        Args:

            state (State): The state to create a node for
            end_stage (State.StageType): The stage to stop creating child nodes at (ignored if None, takes precedence over max_depth)
            end_sub_stage (State.SubStageType): The sub-stage to stop creating child nodes at (ignored if None, takes precedence over max_depth)
            max_depth (int): The maximum depth to create child nodes at
            max_successors_at_action_nodes (int): The maximum number of successors to create at action nodes
            max_successors_at_chance_nodes (int): The maximum number of successors to create at chance nodes
            parent (StateNode): The parent node
        """
        self.state = state
        self.parent = parent
        self.values = np.zeros((state.n_players, len(Hand.COMBINATIONS)))
        self.children = []
        self.strategy = None
        self.regrets = None
        self._utility_matrix = parent._utility_matrix if parent is not None else None
        at_or_past_end_stage = end_stage is not None and state.is_at_or_past_stage(
            end_stage, end_sub_stage
        )
        if not at_or_past_end_stage and max_depth > 0 and not state.is_terminal:
            self.children = [
                (
                    action,
                    StateNode(
                        successor,
                        end_stage,
                        end_sub_stage,
                        max_depth - 1,
                        max_successors_at_action_nodes,
                        max_successors_at_chance_nodes,
                        self,
                    ),
                )
                for action, successor in generate_successor_states(
                    state,
                    max_successors_at_action_nodes,
                    max_successors_at_chance_nodes,
                )
            ]
            self.strategy = np.ones((len(Hand.COMBINATIONS), len(self.children))) / len(
                self.children
            )
            self.regrets = np.zeros((len(Hand.COMBINATIONS), len(self.children)))

    def _propagate_util_matrix_cache(self):
        if self._utility_matrix is not None:
            if (
                self.parent is not None
                and self.parent.state.public_cards == self.state.public_cards
            ):
                if self.parent._utility_matrix is None:
                    # "Parent has no util, propagating upwards"
                    self.parent._utility_matrix = self._utility_matrix
                    self.parent._propagate_util_matrix_cache()
                else:
                    # "Both parent and child have util, not propagating further"
                    pass
            else:
                # "Parent and child public cards differ, not propagating"
                pass
            for _, child in self.children:
                if child._utility_matrix is None:
                    # "Child has no util, propagating downwards"
                    child._utility_matrix = self._utility_matrix
                    child._propagate_util_matrix_cache()
        elif self.parent and self.parent._utility_matrix is not None:
            # "Parent has util, considering propagating downwards"
            if self.parent.state.public_cards == self.state.public_cards:
                # "Parent cards matched, propagating downwards"
                self._utility_matrix = self.parent._utility_matrix
                for _, child in self.children:
                    child._utility_matrix = self._utility_matrix
                    child._propagate_util_matrix_cache()
            else:
                # "Parent cards didn't match, not propagating"
                pass
        else:
            # "Neither parent nor child have util, not propagating"
            pass

    def reset_values(self):
        self.values = np.zeros((self.state.n_players, len(Hand.COMBINATIONS)))
        if self.strategy is not None:
            self.strategy = np.ones_like(self.strategy)
            self.strategy /= self.strategy.sum(axis=1)[:, None]
        if self.regrets is not None:
            self.regrets = np.zeros_like(self.regrets)
        for _, child in self.children:
            child.reset_values()

    def get_utility_matrix(self, perspective: int):
        two_players_active = sum(self.state.player_is_active) >= 2
        if not two_players_active:
            self._utility_matrix = Oracle.generate_utility_matrix(
                CardCollection(self.state.public_cards), False
            )
            assert (
                self._utility_matrix.min() == 0
            )  # No negative payoffs for the active player
            assert self._utility_matrix.max() == 1  # There should be plenty of
            if not self.state.player_is_active[perspective]:
                self._utility_matrix = -self._utility_matrix
        elif self._utility_matrix is None:
            self._utility_matrix = Oracle.generate_utility_matrix(
                CardCollection(self.state.public_cards)
            )
            self._propagate_util_matrix_cache()
        return self._utility_matrix

    def to_df_row(self, ranges: list[np.ndarray], perspective: int):
        """
        Returns a pandas DataFrame representation of the node.
        :param ranges: The ranges per player (in Texas Hold Em: the probability distribution over possible hole pairs).
        :param perspective: The player whose perspective to use.
        """
        if np.isnan(self.values).all():
            print("Warning: Values are NaN")
            return None
        if sum(self.state.player_is_active) != 2:
            print("Only one player active, skipping.")
            return None
        if not self.state.player_is_active[perspective]:
            print("Player not active, skipping.")
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
        player_bet_in_stage = self.state.bet_in_stage[perspective]
        player_bet_in_game = self.state.bet_in_game[perspective]
        opponent_bet_in_stage = self.state.bet_in_stage[opponent]
        opponent_bet_in_game = self.state.bet_in_game[opponent]
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
            player_bet_in_stage,
            player_bet_in_game,
            opponent_bet_in_stage,
            opponent_bet_in_game,
            player_turn,
            player_has_bet,
            opponent_has_bet,
            self.state.pot,
            self.state.game_size,
            self.state.stage,
            # Use name of computer or user, concatenated with time stamp of start of run
            str(
                os.getenv("COMPUTERNAME")
                or os.getenv("USER")
                or os.getenv("USERNAME")
                or os.getenv("HOSTNAME")
                or os.uname().nodename
            )
            + "_"
            + run_start,
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
        headers.append("player_bet_in_stage")
        headers.append("player_bet_in_game")
        headers.append("opponent_bet_in_stage")
        headers.append("opponent_bet_in_game")
        headers.append("player_turn")
        headers.append("player_has_bet")
        headers.append("opponent_has_bet")
        headers.append("pot")
        headers.append("game_size")
        headers.append("stage")
        headers.append("origin")
        return headers

    def print_tree(self, depth=0):
        print("  " * depth, self.state.stage, self.state.sub_stage)
        for action, child in self.children:
            print("  " * depth, action)
            child.print_tree(depth + 1)
