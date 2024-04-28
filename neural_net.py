import numpy as np
import pandas as pd


def to_X_and_Y(df: pd.DataFrame, stage: str):
    """
    Returns a an input and output representation used in the neural network.
    :param df: The data frame representation of the node, based on the StateNode class.
    """
    df = df[df["stage"] == stage]
    return (
        np.hstack(
            [
                df["player_range"],
                df["opponent_range"],
                df["player_values"],
                df["public_cards"],
                df["player_bet"],
                df["player_bet_in_game"],
                df["opponent_bet"],
                df["opponent_bet_in_game"],
                df["player_turn"],
            ]
        ).flatten(),
        df["player_values"],
    )