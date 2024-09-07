import pandas as pd
from sklearn.calibration import LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from hidden_state_model.weigthing import get_sample_weights
from hidden_state_model.interface import HiddenStateModel


class ActionModel(HiddenStateModel):
    def initalize_model(self):
        categorical_cols = ["excess_rank", "stage", "player_name", "opponent_name"]

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

        self.label_encoder = LabelEncoder()

        # Modify the classifier to XGBClassifier
        self.model = Pipeline(
            [
                ("preprocess", preprocessor),
                (
                    "classifier",
                    XGBClassifier(
                        objective="multi:softprob",  # for multiclass classification with probability
                        eval_metric="mlogloss",
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        verbosity=1,
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
        X = train_df.drop(["game_id", "action", "amount"], axis=1)
        y = train_df["action"]
        y_encoded = self.label_encoder.fit_transform(y)
        sample_weights = get_sample_weights(
            train_df, player_name, rel_weight_player_match, op_name, rel_weight_op_match
        )
        self.model.fit(X, y_encoded, classifier__sample_weight=sample_weights)

    def _predict(self, X: pd.DataFrame):
        y_encoded = self.model.predict(X)
        return self.label_encoder.inverse_transform(y_encoded)

    def _predict_proba(self, X: pd.DataFrame):
        return self.model.predict_proba(X)

    def get_classes(self) -> list[str]:
        return self.label_encoder.inverse_transform(self.model.classes_)
