import uuid
import pandas as pd

from State import State
from cpp_poker.cpp_poker import CardCollection

feature_skeleton = {
    f"{action}_{stage}": 0
    for action in ["raise", "call", "check"]
    for stage in ["preflop", "flop", "turn", "river", "showdown"]
}

feature_skeleton = {
    **feature_skeleton,
    **{f"opponent_" + key: 0 for key in feature_skeleton.keys()},
}


class Processor:
    df: pd.DataFrame
    processed: dict[str, dict]

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self.processed = {}

    def _process_state(self, row: pd.Series, parent_id: str) -> dict:
        state = State(
            public_cards=row["public_cards"],
            player_piles=row["player_piles"],
            current_player_i=row["current_player_i"],
            bet_in_stage=row["bet_in_stage"],
            bet_in_game=row["bet_in_game"],
            player_has_played=row["player_has_played"],
            player_is_folded=row["player_is_folded"],
            first_better_i=row["first_better_i"],
            big_blind=row["big_blind"],
        )
        table_rank = CardCollection(list(state.public_cards)).rank_hand().get_rank()
        parent_result = self.processed.get(parent_id)
        result = {
            "game_id": uuid.uuid4(),
            **(parent_result or feature_skeleton),
            "action": row["action"],
            "amount": row["amount"],
            "excess_rank": row["rank"] - table_rank,
            "p": row["p"],
            "relative_ev": row["relative_ev"],
            "stage": state.stage,
        }
        if parent_result:
            prev_stage = parent_result["stage"]
            prev_action = parent_result["action"]
            if prev_action == "raise":
                result[f"raise_{prev_stage}"] += parent_result["amount"]
                if state.stage == prev_stage:
                    # If we're still on the same stage, the opponent must have reraised
                    result[f"opponent_call_{prev_stage}"] += parent_result["amount"]
                    increase = (
                        max(state.bet_in_stage)
                        - state.bet_in_stage[state.current_player_i]
                    )
                    assert (
                        increase > 0
                    ), "Something wrong with logic, increase should be positive"
                    result[f"opponent_raise_{prev_stage}"] += increase
                else:
                    # If we're on a new stage, the opponent must have called
                    result[f"opponent_call_{prev_stage}"] += parent_result["amount"]
            elif prev_action == "call":
                result[f"call_{prev_stage}"] += parent_result["amount"]
                if state.stage == prev_stage:
                    # If we're still on the same stage, the opponent must have raised
                    increase = (
                        max(state.bet_in_stage)
                        - state.bet_in_stage[state.current_player_i]
                    )
                    assert (
                        increase > 0
                    ), "Something wrong with logic, increase should be positive"
                    result[f"opponent_raise_{prev_stage}"] += increase
                else:
                    # If we're on a new stage, one of two things have happened:
                    # 1. We were the last to act on the previous stage and the opponent has done an action on this stage
                    if sum(state.player_has_played):
                        bet_in_stage = max(state.bet_in_stage)
                        if bet_in_stage == 0:
                            result[f"opponent_check_{state.stage}"] += 1
                        else:
                            result[f"opponent_raise_{state.stage}"] += bet_in_stage
                    # 2. The opponent checked and we are the first to act
                    else:
                        result[f"opponent_check_{state.stage}"] += 1
            elif prev_action == "check":
                result[f"check_{prev_stage}"] += 1
                if state.stage == prev_stage:
                    # If we're still on the same stage, the opponent must have raised
                    increase = (
                        max(state.bet_in_stage)
                        - state.bet_in_stage[state.current_player_i]
                    )
                    assert (
                        increase > 0
                    ), "Something wrong with logic, increase should be positive"
                    result[f"opponent_raise_{prev_stage}"] += increase
                else:
                    # If we're on a new stage, the opponent must have checked
                    result[f"opponent_check_{prev_stage}"] += 1
            else:
                raise NotImplementedError(
                    "Not implemented how to deal with", prev_action
                )
        else:
            if state.stage != "preflop":
                print("Cannot process state without parent", row)
                return None
        return result

    def get_processed_df(self) -> pd.DataFrame:
        queue = self.df.index.to_list()
        while queue:
            state_id = queue.pop(0)
            if state_id in self.processed:
                continue
            row = self.df.loc[state_id]
            parent_id = row["prev_entry"]
            if parent_id not in self.processed and parent_id in self.df.index:
                queue.append(state_id)
                continue
            if result := self._process_state(row, parent_id):
                self.processed[state_id] = result
        return pd.DataFrame.from_dict(self.processed, orient="index")
