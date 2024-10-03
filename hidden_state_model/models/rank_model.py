import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from hidden_state_model.interface import HiddenStateModel
from hidden_state_model.weigthing import get_sample_weights


class RankModel(HiddenStateModel):
    def initalize_model(self):
        # Identify categorical columns (excluding 'game_id')
        categorical_cols = [
            "action",
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
                (
                    "classifier",
                    XGBClassifier(
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
        return df[df["excess_rank"].notnull() & df["excess_rank"].notna()]

    def _fit(
        self,
        train_df: pd.DataFrame,
        player_name: str = None,
        rel_weight_player_match=1,
        op_name: str = None,
        rel_weight_op_match=1,
    ):
        X = train_df.drop(["excess_rank", "game_id", "p", "relative_ev"], axis=1)
        y = train_df["excess_rank"].astype(int)
        sample_weights = get_sample_weights(
            train_df, player_name, rel_weight_player_match, op_name, rel_weight_op_match
        )
        self.model.fit(X, y, classifier__sample_weight=sample_weights)

    def _predict(self, X: pd.DataFrame):
        return self.model.predict(X)

    def _predict_proba(self, X: pd.DataFrame):
        return self.model.predict_proba(X)

    def get_classes(self) -> list[str]:
        return self.model.classes_
