import copy
from typing import Literal, Union, TYPE_CHECKING
import pandas as pd

from hidden_state_model.action_model import fit_model as fit_action_model
from hidden_state_model.raise_model import fit_model as fit_raise_model
from hidden_state_model.prob_model import fit_model as fit_prob_model
from hidden_state_model.rank_model import fit_model as fit_rank_model

if TYPE_CHECKING:
    from hidden_state_model.observer import Observer


class Predictor:
    _models = {
        "action": {},
        "raise": {},
        "prob": {},
        "rank": {},
    }
    fitters = {
        "action": fit_action_model,
        "raise": fit_raise_model,
        "prob": fit_prob_model,
        "rank": fit_rank_model,
    }
    observer: "Observer"

    def __init__(self, observer: "Observer"):
        self.observer = observer

    def clear_model_cache(self):
        for attribute in self._models:
            for player_name in self._models[attribute]:
                self._models[attribute][player_name]["needs_refit"] = True

    def clone(self, observer: "Observer"):
        c = Predictor(observer)
        c._models = copy.deepcopy(self._models)
        return c

    def predict(
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
        probabilities=False,
    ):
        entry = self._models[attribute].get(player_name, {})
        model = entry.get("model")
        stored_rel_weight = entry.get("relative_weight_player")
        if (
            model is None
            or stored_rel_weight != relative_weight_player
            or entry.get("needs_refit")
        ):
            fit_fn = self.fitters[attribute]
            print(f"@@@@@ Fitting {attribute} model for {player_name} @@@@@")
            model = fit_fn(
                self.observer.get_processed_df(),
                player_name,
                relative_weight_player,
                model,
            )
            self._models[attribute][player_name] = {
                "model": model,
                "relative_weight_player": relative_weight_player,
            }
        X_pred = row.to_frame().T
        if probabilities:
            return (
                model.classes_,
                model.predict_proba(X_pred)[0],
            )
        print(f"Predicting {attribute} for row:\n", X_pred)
        print("NaNs in row: ", X_pred.isna().sum().sum())
        print("NaN columns: ", X_pred.columns[X_pred.isna().any()].tolist())
        return model.predict(X_pred)[0]
