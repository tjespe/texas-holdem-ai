import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Identify categorical columns (excluding 'game_id')
categorical_cols = ["action", "stage", "player_name"]

# Preprocessing pipeline: OneHotEncoding for categorical and scaling for numerical
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), categorical_cols)
    ],
    remainder="passthrough",
)


def fit_model(
    df: pd.DataFrame, player_name: str = None, relative_weight_player=1, model=None
):
    train_df = df[df["excess_rank"].notnull() & df["excess_rank"].notna()]
    X = train_df.drop(["excess_rank", "game_id", "p", "relative_ev"], axis=1)
    y = train_df["excess_rank"].astype(int)
    # Convert y to discrete categories if needed
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
