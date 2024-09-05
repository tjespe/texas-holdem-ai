import pandas as pd


def get_sample_weights(
    df: pd.DataFrame,
    player_name: str = None,
    rel_weight_player_match=1,
    op_name: str = None,
    rel_weight_op_match=1,
):
    matching_player = df["player_name"] == player_name
    sample_weights = matching_player * rel_weight_player_match + (1 - matching_player)
    matching_opponent = df["opponent_name"] == op_name
    sample_weights *= matching_opponent * rel_weight_op_match + (1 - matching_opponent)
    return sample_weights
