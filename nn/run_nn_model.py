import json
import os

import numpy as np
import pandas as pd
import tensorflow as tf
from State import State
from StateNode import StateNode
from keras.models import load_model
import logging
from cpp_poker.cpp_poker import Hand

tf.get_logger().setLevel(logging.ERROR)

bet_columns = [
    "player_bet_in_stage",
    "player_bet_in_game",
    "opponent_bet_in_stage",
    "opponent_bet_in_game",
    "pot",
]
range_columns = [col for col in StateNode.get_df_headers() if col.startswith("prob_")]
value_columns = [
    col for col in StateNode.get_df_headers() if col.startswith("value_of_")
]
bool_columns = [
    "player_turn",
    "player_has_bet",
    "opponent_has_bet",
]

__dir__ = os.path.dirname(__file__)
MODEL_DIR = os.path.join(__dir__, "models")


def load_stage_model(stage: State.StageType):
    model_fname = os.path.join(MODEL_DIR, f"model_{stage}_latest.h5")
    meta_fname = os.path.join(MODEL_DIR, f"model_{stage}_latest.json")
    if not os.path.exists(model_fname):
        print(f"Warning: Model file {model_fname} not found")
        return None, None
    model = load_model(model_fname)
    meta = json.load(open(meta_fname))
    return model, meta


models = {
    "flop": load_stage_model("flop"),
    "turn": load_stage_model("turn"),
    "river": load_stage_model("river"),
}


def scale_bets(df: pd.DataFrame):
    df[bet_columns] = df[bet_columns].div(df["game_size"], axis=0)


def scale_ranges(df, training_mean, training_sd):
    df[range_columns] = (df[range_columns] - training_mean) / training_sd


def encode_bools(df: pd.DataFrame):
    df[bool_columns] = df[bool_columns].astype(int)


def preprocess_data(
    df: pd.DataFrame, mean_training_range_val: float, std_training_range_val: float
):
    scale_bets(df)
    scale_ranges(df, mean_training_range_val, std_training_range_val)
    df.drop(columns=["game_size", "stage", "origin"] + value_columns, inplace=True)
    encode_bools(df)


def estimate_value_vector(
    state_node: StateNode, ranges: list[np.ndarray], perspective: int
):
    stage = state_node.state.stage
    if stage == "terminal":
        stage = "river"
    model, meta = models[stage]
    x = state_node.to_df_row(ranges, perspective)
    df = pd.DataFrame([x], columns=StateNode.get_df_headers())
    preprocess_data(df, meta["mean_training_range_val"], meta["sd_training_range_val"])
    X = df.values
    prediction = model.predict(X)
    return prediction[0]

def _get_stage(node: StateNode):
    stage = node.state.stage
    if stage == "terminal":
        stage = "river"
    return stage

def estimate_value_vectors(
    nodes: list[StateNode], ranges_per_child: list[np.ndarray], perspective: int
):
    stages = set([_get_stage(node) for node in nodes])
    if len(stages) != 1:
        predictions = np.full((len(nodes), len(Hand.COMBINATIONS)), np.nan)
        indices_per_stage = {}
        for i, node in enumerate(nodes):
            stage = _get_stage(node)
            if stage not in indices_per_stage:
                indices_per_stage[stage] = []
            indices_per_stage[stage].append(i)
        for stage, indices in indices_per_stage.items():
            nodes_at_stage = [nodes[i] for i in indices]
            ranges_at_stage = [ranges_per_child[i] for i in indices]
            stages_at_stage = set([_get_stage(node) for node in nodes_at_stage])
            if len(stages_at_stage) != 1:
                raise ValueError("Nodes at stage have different stages: %s" % stages_at_stage)
            predictions_at_stage = estimate_value_vectors(nodes_at_stage, ranges_at_stage, perspective)
            predictions[indices] = predictions_at_stage
        return predictions
    stage = nodes[0].state.stage
    if stage == "terminal":
        stage = "river"
    model, meta = models[stage]
    rows = [
        node.to_df_row(ranges, perspective)
        for node, ranges in zip(nodes, ranges_per_child)
    ]
    df = pd.DataFrame(rows, columns=StateNode.get_df_headers())
    preprocess_data(df, meta["mean_training_range_val"], meta["sd_training_range_val"])
    X = df.values
    predictions = model.predict(X)
    return predictions
