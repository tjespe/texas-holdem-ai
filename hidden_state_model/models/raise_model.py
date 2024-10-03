import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from hidden_state_model.interface import HiddenStateModel
from hidden_state_model.weigthing import get_sample_weights


class RaiseModel(HiddenStateModel):
    def initalize_model(self):
        # Identify categorical columns (excluding 'game_id')
        categorical_cols = [
            "excess_rank",
            "stage",
            "player_name",
            "opponent_name",
            "hand_group",
            "hand_suited",
        ]

        # Preprocessing pipeline: OneHotEncoding for categorical and scaling for numerical
        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "cat",
                    OneHotEncoder(handle_unknown="ignore"),
                    categorical_cols,
                )
            ],
            remainder="passthrough",
        )

        self.model = Pipeline(
            [
                ("preprocess", preprocessor),
                ("regressor", LinearRegression()),
            ]
        )
        self.last_fit_signature = None

    def get_train_df(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["amount"].notnull() & df["p"].notnull()]

    def _fit(
        self,
        train_df: pd.DataFrame,
        player_name: str = None,
        rel_weight_player_match=1,
        op_name: str = None,
        rel_weight_op_match=1,
    ):
        X = train_df.drop(
            [
                "game_id",
                "action",
                "amount",
                *(c for c in train_df.columns if c.startswith("n_")),
            ],
            axis=1,
        )
        y = train_df["amount"]
        sample_weights = get_sample_weights(
            train_df, player_name, rel_weight_player_match, op_name, rel_weight_op_match
        )
        self.model.fit(X, y, regressor__sample_weight=sample_weights)

    def _predict(self, X: pd.DataFrame):
        return self.model.predict(X)
