import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Identify categorical columns (excluding 'game_id')
categorical_cols = ["excess_rank", "stage", "player_name"]


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
    train_df = df[df["p"].notnull()]
    X = train_df.drop(["game_id", "action", "amount"], axis=1)
    y = train_df["amount"]
    print("Fitting model for player", player_name)
    print("X.shape", X.shape)
    print("y.shape", y.shape)
    print("Tail of X\n", X.tail(2)[["excess_rank", "p", "stage", "player_name"]])
    print("NaN in X\n", X.isna().sum())
    print("Rows with NaN in X\n", X[X.isna().any(axis=1)])
    print("NaN in y\n", y.isna().sum())
    print("Rows with NaN in y\n", y[y.isna()])
    matching_player = train_df["player_name"] == player_name
    sample_weights = matching_player * relative_weight_player + (1 - matching_player)
    if model is None:
        model = Pipeline(
            [
                ("preprocess", preprocessor),
                ("regressor", LinearRegression()),
            ]
        )
    model.fit(X, y, regressor__sample_weight=sample_weights)
    return model


def fit_and_predict_raise(
    df: pd.DataFrame,
    state_id: str,
    player_name: str = None,
    relative_weight_player=1,
):
    model = fit_model(df, player_name, relative_weight_player)
    X_pred = df.loc[state_id].drop(["game_id", "action", "amount"])
    # Correct the shape of the input
    X_pred = X_pred.to_frame().T
    return model.predict(X_pred)
