import copy
from typing import Literal, Union, TYPE_CHECKING
import pandas as pd

from hidden_state_model.interface import HiddenStateModel
from hidden_state_model.models import ActionModel, RaiseModel, ProbModel, RankModel

if TYPE_CHECKING:
    from hidden_state_model.observer import Observer


class Predictor:
    _models: dict[dict[str, HiddenStateModel]] = {
        "action": {},
        "raise": {},
        "prob": {},
        "rank": {},
    }
    model_classes: dict[str, type[HiddenStateModel]] = {
        "action": ActionModel,
        "raise": RaiseModel,
        "prob": ProbModel,
        "rank": RankModel,
    }
    observer: "Observer"

    def __init__(self, observer: "Observer"):
        self.observer = observer

    def clear_model_cache(self):
        # Don't think we need this anymore?
        # for attribute in self._models:
        #     for player_name in self._models[attribute]:
        #         self._models[attribute][player_name]["needs_refit"] = True
        pass

    def clone(self, observer: "Observer"):
        c = Predictor(observer)
        c._models = copy.deepcopy(self._models)
        return c

    def _predict(
        self,
        attribute: Literal["action", "raise", "prob", "rank"],
        state_id: str,
        player_name: Union[str, None],
        relative_weight_player=1,
        probabilities=False,
    ):
        row = self.observer.get_processed_df().loc[state_id]
        return self.predict_for_row(
            attribute,
            row,
            player_name,
            relative_weight_player,
            probabilities,
        )

    def predict_for_row(
        self,
        attribute: Literal["action", "raise", "prob", "rank"],
        row: pd.Series,
        player_name: Union[str, None],
        relative_weight_player=1,
        opponent_name: Union[str, None] = None,
        relative_weight_opponent=1,
        probabilities=False,
    ):
        model = self._models[attribute].get(player_name)
        if model is None:
            model = self.model_classes[attribute]()
            self._models[attribute][player_name] = model
        model.fit(
            self.observer.get_processed_df(),
            player_name,
            relative_weight_player,
            opponent_name,
            relative_weight_opponent,
        )
        X_pred = row.to_frame().T
        try:
            if probabilities:
                return (
                    model.get_classes(),
                    model.predict_proba(X_pred)[0],
                )
            return model.predict(X_pred)[0]
        except Exception as e:
            print(f"Failed to predict {attribute} for {player_name}: {e}")
            print(X_pred)
            print(
                f"Cells with NaN values ({X_pred.isna().sum().sum()}):\n",
                X_pred[X_pred.columns[X_pred.isna().any()]],
            )
            print("dtypes:\n", X_pred.dtypes)
            raise e
