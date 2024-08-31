import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from State import State

# Identify categorical columns (excluding 'game_id')
categorical_cols = ["action", "stage", "player_name"]

# Preprocessing pipeline: OneHotEncoding for categorical and scaling for numerical
preprocessor = ColumnTransformer(
    transformers=[("cat", OneHotEncoder(drop="first"), categorical_cols)],
    remainder="passthrough",
)

# Create the full pipeline with logistic regression
model = Pipeline(
    [
        ("preprocess", preprocessor),
        ("regressor", LinearRegression()),
    ]
)


def fit_and_predict(
    df: pd.DataFrame,
    state_id: str,
    player_name: str = None,
    relative_weight_player=1,
):
    train_df = df[df["p"].notnull()]
    print("Dropped rows with null p:", len(df) - len(train_df))
    X = train_df.drop(["excess_rank", "game_id", "p", "relative_ev"], axis=1)
    y = train_df["p"]
    matching_player = train_df["player_name"] == player_name
    sample_weights = matching_player * relative_weight_player + (1 - matching_player)
    print("X:", X)
    print("y:", y)
    print("sample_weights:", sample_weights)
    model.fit(X, y, regressor__sample_weight=sample_weights)
    X_pred = df.loc[state_id].drop(["excess_rank", "game_id", "p", "relative_ev"])
    # Correct the shape of the input
    X_pred = X_pred.to_frame().T
    return model.predict(X_pred)
