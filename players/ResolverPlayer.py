import numpy as np
import pandas as pd
from StateNode import StateNode
from cpp_poker.cpp_poker import Hand, CardCollection
from PlayerABC import Player
from resolver import generate_uniform_ranges, resolve
from datetime import datetime


class ResolverPlayer(Player):
    """
    A player that uses Monte Carlo Tree Search to resolve the game tree down to a
    certain depth.
    At the specified depth, the player uses a neural network to estimate the value
    of the game state.
    """
    def __init__(
        self,
        name: str = "Resa",
        max_successors_at_action_nodes=5,
        max_successors_at_chance_nodes=50,
        max_simulations=5,
        max_depth=3,
    ):
        """
        Args:
            name (str): Player name
            max_successors_at_action_nodes (int): Max number of successors to consider at action nodes
            max_successors_at_chance_nodes (int): Max number of successors to consider at chance nodes
            max_simulations (int): Maximum number of simulations to run
            max_depth (int): Max depth to search before using a Neural Net as a heuristic
        """
        super().__init__()
        self.name = name
        self.ranges = None
        self._hand_index = None
        self.max_successors_at_action_nodes = max_successors_at_action_nodes
        self.max_successors_at_chance_nodes = max_successors_at_chance_nodes
        self.simulations = max_simulations
        self.max_depth = max_depth
        self.cache_fname = (
            "nn/dfs/df_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".parquet"
        )
        self.cached_rows = []

    @property
    def hand_index(self):
        if self._hand_index is None:
            hand_cards = CardCollection(self.hand)
            for i, hand in enumerate(Hand.COMBINATIONS):
                if hand_cards == hand:
                    self._hand_index = i
                    break
        return self._hand_index

    def play(self, state) -> int:
        if sum(state.player_is_active) > 2:
            print("The ResolverPlayer only supports heads-up games")
            return 0
        if state.stage == "preflop":
            # Neural net for preflop is not implemented yet, so just call or check
            return max(state.bet_in_stage) - state.bet_in_stage[state.current_player_i]
        if self.ranges is None:
            self.ranges = generate_uniform_ranges(state)
        action, child_state, self.ranges, cached_root = resolve(
            state,
            self.ranges,
            end_depth=self.max_depth,
            end_stage=None,
            max_successors_at_action_nodes=self.max_successors_at_action_nodes,
            max_successors_at_chance_nodes=self.max_successors_at_chance_nodes,
            max_simulations=self.simulations,
            hand_index=self.hand_index,
        )
        self.cached_rows.append(cached_root.to_df_row(self.ranges, 0))
        df = pd.DataFrame(self.cached_rows, columns=StateNode.get_df_headers())
        df.to_parquet(self.cache_fname)
        return action
