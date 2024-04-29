import numpy as np
import pandas as pd
from StateNode import StateNode
from cpp_poker.cpp_poker import Hand, CardCollection
from PlayerABC import Player
from resolver import generate_uniform_ranges, resolve
from datetime import datetime


class ResolverPlayer(Player):
    def __init__(
        self,
        name: str = "Resa",
        max_successors_at_action_nodes=5,
        max_successors_at_chance_nodes=50,
        simulations=200,
        max_depth=100,
        end_stage="river",
        end_sub_stage="first_bet",
    ):
        """
        Args:
            name (str): Player name
            max_successors_at_action_nodes (int): Max number of successors to consider at action nodes
            max_successors_at_chance_nodes (int): Max number of successors to consider at chance nodes
            simulations (int): Number of simulations to run
            max_depth (int): Max depth to search before using a Neural Net as a heuristic
            end_stage (str): Stage to stop searching at before using a Neural Net as a heuristic
            end_sub_stage (str): Sub-stage to stop searching at before using a Neural Net as a heuristic
        """
        super().__init__()
        self.name = name
        self.ranges = None
        self._hand_index = None
        self.max_successors_at_action_nodes = max_successors_at_action_nodes
        self.max_successors_at_chance_nodes = max_successors_at_chance_nodes
        self.simulations = simulations
        self.max_depth = max_depth
        self.end_stage = end_stage
        self.end_sub_stage = end_sub_stage
        self.cache_fname = (
            "dfs/df_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".parquet"
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
        if self.ranges is None:
            self.ranges = generate_uniform_ranges(state)
        action, child_state, self.ranges, cached_root = resolve(
            state,
            self.ranges,
            end_stage=self.end_stage,
            end_sub_stage=self.end_sub_stage,
            end_depth=self.max_depth,
            max_successors_at_action_nodes=self.max_successors_at_action_nodes,
            max_successors_at_chance_nodes=self.max_successors_at_chance_nodes,
            max_simulations=self.simulations,
            hand_index=self.hand_index,
        )
        # self.cached_rows.append(cached_root.to_df_row(self.ranges, 0))
        # df = pd.DataFrame(self.cached_rows, columns=StateNode.get_df_headers())
        # df.to_parquet(self.cache_fname)
        return action
