from abc import ABC, abstractmethod
import asyncio

import numpy as np
import pandas as pd


class HiddenStateModel(ABC):
    _fit_signature = None

    def __init__(self) -> None:
        self.initalize_model()
        self._fit_task = None  # Track async fitting task

    @abstractmethod
    def initalize_model(self):
        pass

    @abstractmethod
    def get_train_df(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

    @property
    def is_fitted(self) -> bool:
        return self._fit_signature is not None

    async def _fit_async(
        self, df, player_name, rel_weight_player_match, op_name, rel_weight_op_match
    ):
        """Runs fit asynchronously in a background thread."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._fit,
            df,
            player_name,
            rel_weight_player_match,
            op_name,
            rel_weight_op_match,
        )
        self._fit_signature = (
            df.shape,
            player_name,
            rel_weight_player_match,
            op_name,
            rel_weight_op_match,
        )
        self._fit_task = None  # Clear task reference after completion

    def fit(
        self,
        df: pd.DataFrame,
        player_name: str = None,
        rel_weight_player_match=1,
        op_name: str = None,
        rel_weight_op_match=1,
        async_fit=False,
    ):
        """
        Schedules an async fit if model exists, otherwise fits synchronously.
        """
        train_df = self.get_train_df(df)
        fit_signature = (
            train_df.shape,
            player_name,
            rel_weight_player_match,
            op_name,
            rel_weight_op_match,
        )

        if fit_signature == self._fit_signature:
            return  # No need to refit

        print(
            f"@@@ Refitting {self.__class__.__name__} {'asynchronously' if async_fit else 'synchronously'} with signature {fit_signature} @@@"
        )

        if async_fit and self._fit_task is None:
            # Ensure we are using a valid event loop
            if HiddenStateModel._loop.is_closed():
                HiddenStateModel._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(HiddenStateModel._loop)

            # Run async fitting in the main loop
            self._fit_task = asyncio.run_coroutine_threadsafe(
                self._fit_async(
                    train_df,
                    player_name,
                    rel_weight_player_match,
                    op_name,
                    rel_weight_op_match,
                ),
                HiddenStateModel._loop,
            )
        else:
            # Fit synchronously if async is disabled or a task is already running
            self._fit(
                train_df,
                player_name,
                rel_weight_player_match,
                op_name,
                rel_weight_op_match,
            )
            self._fit_signature = fit_signature

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
            if not _is_retry:
                print(f"Rebuilding {self.__class__.__name__} and retrying prediction")
                self.initalize_model()
                self.fit(X, async_fit=False)  # Force sync refit
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
