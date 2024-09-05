import os
from typing import Callable, Literal, Union
import pandas as pd

from State import State
from cpp_poker.cpp_poker import CardCollection, CheatSheet, Hand
from hidden_state_model.predictor import Predictor
from hidden_state_model.processor import Processor

import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)


class Observer:
    df: pd.DataFrame
    df_fname: Union[str, None]
    processor: Processor
    predictor: Predictor

    DF_HEADERS_AND_DTYPES = {
        "prev_entry": "str",
        "public_cards": "object",
        "player_piles": "object",
        "current_player_i": "int64",
        "bet_in_stage": "object",
        "bet_in_game": "object",
        "player_has_played": "object",
        "player_is_folded": "object",
        "first_better_i": "int64",
        "big_blind": "int64",
        "player_name": "object",
        "player_type": "object",
        "opponent_names": "object",
        "action": "object",
        "amount": "Int64",
        "p": "float64",
        "relative_ev": "float64",
        "rank": "Int64",
        "tiebreakers": "object",
        "hand_index": "Int64",
    }

    @property
    def filtered_df(self):
        """
        Only write/send to processor rows with hand data
        """
        return self.df[self.df["rank"].notnull()]

    def __init__(self, df_fname=None, df=None) -> None:
        self.df_fname = df_fname
        if df is not None:
            self.df = df
        elif df_fname and os.path.exists(df_fname):
            self.df = pd.read_parquet(df_fname)
        else:
            self.df = pd.DataFrame(
                columns=["state_id", *self.DF_HEADERS_AND_DTYPES.keys()]
            ).set_index("state_id")
        self._ensure_dtypes()
        self.processor = Processor(self.df)
        self.predictor = Predictor(self)

    def _ensure_dtypes(self):
        for col, dtype in self.DF_HEADERS_AND_DTYPES.items():
            series = self.df.get(col)
            if series is None:
                self.df[col] = pd.Series(dtype=dtype)
            else:
                self.df[col] = series.astype(dtype)

    def _classify_action(self, state: State, bet: int):
        call_bet = max(state.bet_in_game) - state.bet_in_game[state.current_player_i]
        if bet < call_bet:
            return "fold"
        if bet == call_bet:
            if bet == 0:
                return "check"
            return "call"
        return "raise"

    def _get_hand_stats(self, hand: tuple[int, int], state: State) -> str:
        hand = CardCollection(list(hand))
        table = CardCollection(list(state.public_cards))
        p = CheatSheet.get_winning_probability(
            hand, table, state.player_is_active.sum()
        )
        hand_cards = CardCollection(list(hand))
        hand_index = None
        for i, hand in enumerate(Hand.COMBINATIONS):
            if hand_cards == hand:
                hand_index = i
                break
        rank_obj = CardCollection(list(hand + table)).rank_hand()
        rank = rank_obj.get_rank()
        tiebreakers = rank_obj.get_tiebreakers()
        relative_ev = state.pot * p / state.game_size
        return {
            "p": p,
            "rank": rank,
            "relative_ev": relative_ev,
            "tiebreakers": tiebreakers,
            "hand_index": hand_index,
        }

    def _write_df(self):
        if self.df_fname:
            self.filtered_df.to_parquet(self.df_fname, index=True)

    def observe_action(
        self,
        state: State,
        player_name: str,
        player_type: str,
        amount: int,
        opponent_names: Union[list[str], None],
        hand: Union[tuple[int, int], None],
    ) -> None:
        prev_entry = None
        prev_state = state.prev_state
        while prev_state:
            if (
                prev_state.id in self.df.index
                and self.df.at[prev_state.id, "current_player_i"]
                == state.current_player_i
            ):
                prev_entry = prev_state.id
                break
            prev_state = prev_state.prev_state
        if hand:
            # Reset dependant models when we have new training data
            self.predictor.clear_model_cache()
        self.df.loc[state.id] = {
            "prev_entry": prev_entry,
            "public_cards": state.public_cards,
            "player_piles": state.player_piles,
            "current_player_i": state.current_player_i,
            "bet_in_stage": state.bet_in_stage,
            "bet_in_game": state.bet_in_game,
            "player_has_played": state.player_has_played,
            "player_is_folded": state.player_is_folded,
            "first_better_i": state.first_better_i,
            "big_blind": state.big_blind,
            "player_name": player_name,
            "player_type": player_type,
            "opponent_names": opponent_names,
            "amount": amount,
            "action": self._classify_action(state, amount),
            **(self._get_hand_stats(hand, state) if hand else {}),
        }
        self._write_df()

    def observe_state(
        self,
        state: State,
        player_name: str,
        player_type: str,
        opponent_names: Union[list[str], None],
        hand: Union[tuple[int, int], None],
    ) -> None:
        prev_entry = None
        prev_state = state.prev_state
        while prev_state:
            if prev_state.id in self.df.index:
                prev_entry = prev_state.id
                break
            prev_state = prev_state.prev_state
        self.df.loc[state.id] = {
            "prev_entry": prev_entry,
            "public_cards": state.public_cards,
            "player_piles": state.player_piles,
            "current_player_i": state.current_player_i,
            "bet_in_stage": state.bet_in_stage,
            "bet_in_game": state.bet_in_game,
            "player_has_played": state.player_has_played,
            "player_is_folded": state.player_is_folded,
            "first_better_i": state.first_better_i,
            "big_blind": state.big_blind,
            "player_name": player_name,
            "player_type": player_type,
            "opponent_names": opponent_names,
            **(self._get_hand_stats(hand, state) if hand else {}),
        }

    def retrofill_hand_stats(self, states: list[State], hand: tuple[int, int]):
        self._ensure_dtypes()
        for state in states:
            hand_stats = self._get_hand_stats(hand, state)
            # Check if state id exists in df
            if not state.id in self.df.index:
                continue
            for k, v in hand_stats.items():
                self.df.at[state.id, k] = v
        # Reset dependant models
        self.predictor.clear_model_cache()

    def retrofill_action(self, state: State, amount: int):
        self._ensure_dtypes()
        if not state.id in self.df.index:
            return
        self.df.at[state.id, "action"] = self._classify_action(state, amount)
        self.df.at[state.id, "amount"] = amount
        # Reset dependant models
        self.predictor.clear_model_cache()

    def get_processed_df(self):
        self.processor.update_df(self.df)
        return self.processor.get_processed_df()

    def get_processed_df_row(self, state_id: str):
        return self.get_processed_df().loc[state_id]

    def clone(self):
        c = Observer(df=self.df.copy())
        c.processor = self.processor.clone()
        c.predictor = c.predictor.clone(observer=c)
        return c

    def clone_with_filtered_df(self, filter_fn: Callable[[pd.DataFrame], pd.DataFrame]):
        df = filter_fn(self.df.copy())
        c = Observer(df=df)
        return c
