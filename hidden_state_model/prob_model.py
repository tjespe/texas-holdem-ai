import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Identify categorical columns (excluding 'game_id')
categorical_cols = ["action", "stage", "player_name"]

# Preprocessing pipeline: OneHotEncoding for categorical and scaling for numerical
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
    train_df = df[df["p"].notnull()]
    X = train_df.drop(["excess_rank", "game_id", "p", "relative_ev"], axis=1)
    y = train_df["p"]
    matching_player = train_df["player_name"] == player_name
    if model is None:
        model = Pipeline(
            [
                ("preprocess", preprocessor),
                ("regressor", LinearRegression()),
            ]
        )
    sample_weights = matching_player * relative_weight_player + (1 - matching_player)
    model.fit(X, y, regressor__sample_weight=sample_weights)
    return model


def fit_and_predict(
    df: pd.DataFrame,
    state_id: str,
    player_name: str = None,
    relative_weight_player=1,
):
    mdoel = fit_model(df, player_name, relative_weight_player)
    X_pred = df.loc[state_id].drop(["excess_rank", "game_id", "p", "relative_ev"])
    X_pred = X_pred.to_frame().T
    return mdoel.predict(X_pred)
