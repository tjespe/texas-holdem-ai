import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
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

# Create the full pipeline with logistic regression
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


def fit_and_predict_proba(
    df: pd.DataFrame,
    state_id: str,
    player_name: str = None,
    relative_weight_player=1,
):
    train_df = df[df["p"].notnull() & df["action"].notnull()]
    X = train_df.drop(["game_id", "action", "amount"], axis=1)
    y = train_df["action"]
    matching_player = train_df["player_name"] == player_name
    sample_weights = matching_player * relative_weight_player + (1 - matching_player)
    model.fit(X, y, classifier__sample_weight=sample_weights)
    X_pred = df.loc[state_id].drop(["game_id", "action", "amount"])
    # Correct the shape of the input
    X_pred = X_pred.to_frame().T
    return model.classes_, model.predict_proba(X_pred)[0]
