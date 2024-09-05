from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class HiddenStateModel(ABC):
    _fit_signature = None

    def __init__(self) -> None:
        self.initalize_model()

    @abstractmethod
    def initalize_model(self):
        pass

    @abstractmethod
    def get_train_df(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

    def fit(
        self,
        df: pd.DataFrame,
        player_name: str = None,
        rel_weight_player_match=1,
        op_name: str = None,
        rel_weight_op_match=1,
    ):
        train_df = self.get_train_df(df)
        fit_signature = (
            train_df.shape,
            player_name,
            rel_weight_player_match,
            op_name,
            rel_weight_op_match,
        )
        if fit_signature != self._fit_signature:
            print(
                f"@@@ Refitting {self.__class__.__name__} with signature ({fit_signature}) @@@"
            )
            try:
                self._fit(
                    train_df,
                    player_name,
                    rel_weight_player_match,
                    op_name,
                    rel_weight_op_match,
                )
                self._fit_signature = fit_signature
            except Exception as e:
                print(f"Failed to fit {self.__class__.__name__}: {e}")
                print(f"Signature: {fit_signature}")
                print("Train df:")
                print(train_df)
                print("NaN count:")
                print(train_df.isna().sum())
                print("NaN cells:")
                nan_cols = train_df.columns[train_df.isna().any()]
                print(train_df[train_df.isna().any(axis=1)][nan_cols])
                raise e

    @abstractmethod
    def _fit(
        self,
        train_df: pd.DataFrame,
        player_name: str = None,
        rel_weight_player_match=1,
        op_name: str = None,
        rel_weight_op_match=1,
    ):
        pass

    @abstractmethod
    def _predict(self, X: pd.DataFrame) -> np.ndarray:
        pass

    def predict(self, X: pd.DataFrame, _is_retry=False) -> np.ndarray:
        try:
            return self._predict(X)
        except ValueError as e:
            # This might be caused by a new class appearing and being encoded by the
            # OneHotEncoder and not being part of the model, so attempt rebuilding the
            # model and retrying the prediction
            if not _is_retry:
                print(f"Rebuilding {self.__class__.__name__} and retrying prediction")
                self.initalize_model()
                self.fit(X)
                return self.predict(X, _is_retry=True)
            raise e

    def _predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support predict_proba"
        )

    def predict_proba(self, X: pd.DataFrame, _is_retry=False) -> np.ndarray:
        try:
            return self._predict_proba(X)
        except ValueError as e:
            # This might be caused by a new class appearing and being encoded by the
            # OneHotEncoder and not being part of the model, so attempt rebuilding the
            # model and retrying the prediction
            if not _is_retry:
                print(f"Rebuilding {self.__class__.__name__} and retrying prediction")
                self.initalize_model()
                self.fit(X)

    def get_classes(self) -> list[str]:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support get_classes"
        )
