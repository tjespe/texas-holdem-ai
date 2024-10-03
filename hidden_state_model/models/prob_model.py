import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

from hidden_state_model.interface import HiddenStateModel
from hidden_state_model.weigthing import get_sample_weights


class ProbModel(HiddenStateModel):
    def initalize_model(self):
        # Identify categorical columns (excluding 'game_id')
        categorical_cols = ["action", "stage", "player_name", "opponent_name"]

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
                (
                    "regressor",
                    XGBRegressor(
                        colsample_bytree=0.6,
                        learning_rate=0.01,
                        max_depth=7,
                        n_estimators=500,
                        subsample=0.6,
                    ),
                ),
            ]
        )

    def get_train_df(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["p"].notnull()]

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
                "excess_rank",
                "game_id",
                "p",
                "relative_ev",
                "hand_group",
                "hand_suited",
            ],
            axis=1,
        )
        y = train_df["p"]
        sample_weights = get_sample_weights(
            train_df, player_name, rel_weight_player_match, op_name, rel_weight_op_match
        )
        self.model.fit(X, y, regressor__sample_weight=sample_weights)

    def _predict(self, X: pd.DataFrame):
        return self.model.predict(X)
