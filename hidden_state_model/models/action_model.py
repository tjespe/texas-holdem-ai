import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


categorical_cols = ["excess_rank", "stage", "player_name"]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "cat",
            OneHotEncoder(
                drop="first",
                handle_unknown="infrequent_if_exist",
                min_frequency=0.05,
            ),
            categorical_cols,
        )
    ],
    remainder="passthrough",
)


def fit_model(
    df: pd.DataFrame, player_name: str = None, relative_weight_player=1, model=None
):
    train_df = df[df["p"].notnull() & df["action"].notnull()]
    X = train_df.drop(["game_id", "action", "amount"], axis=1)
    y = train_df["action"]
    matching_player = train_df["player_name"] == player_name
    if model is None:
        model = Pipeline(
            [
                ("preprocess", preprocessor),
                (
                    "classifier",
                    LogisticRegression(
                        multi_class="multinomial", solver="lbfgs", max_iter=10_000
                    ),
                ),
            ]
        )
    sample_weights = matching_player * relative_weight_player + (1 - matching_player)
    model.fit(X, y, classifier__sample_weight=sample_weights)
    return model


def fit_and_predict_proba(
    df: pd.DataFrame,
    state_id: str,
    player_name: str = None,
    relative_weight_player=1,
):
    model = fit_model(df, player_name, relative_weight_player)
    X_pred = df.loc[state_id].drop(["game_id", "action", "amount"])
    # Correct the shape of the input
    X_pred = X_pred.to_frame().T
    return model.classes_, model.predict_proba(X_pred)[0]
