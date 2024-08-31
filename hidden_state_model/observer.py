import os
from typing import Union
import pandas as pd

from State import State
from cpp_poker.cpp_poker import CardCollection, CheatSheet, Hand


class Observer:
    df: pd.DataFrame
    df_fname: Union[str, None]

    DF_HEADERS = [
        "state_id",
        "prev_entry",
        "public_cards",
        "player_piles",
        "current_player_i",
        "bet_in_stage",
        "bet_in_game",
        "player_has_played",
        "player_is_folded",
        "first_better_i",
        "big_blind",
        "player_name",
        "player_type",
        "action",
        "amount",
        "p",
        "relative_ev",
        "rank",
        "tiebreakers",
    ]

    def __init__(self, df_fname=None) -> None:
        self.df_fname = df_fname
        if df_fname and os.path.exists(df_fname):
            self.df = pd.read_parquet(df_fname)
        else:
            self.df = pd.DataFrame(columns=self.DF_HEADERS).set_index("state_id")

    def _classify_action(self, state: State, bet: int):
        call_bet = max(state.bet_in_game) - state.bet_in_game[state.current_player_i]
        if bet < call_bet:
            return "fold"
        if bet == call_bet:
            if bet == 0:
                return "check"
            return "call"
        return "raise"

    def _classify_hand(self, hand: tuple[int, int], state: State) -> str:
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
            # Only write rows with hand data
            filtered_df = self.df[self.df["rank"].notnull()]
            filtered_df.to_parquet(self.df_fname, index=True)

    def observe_action(
        self,
        state: State,
        player_name: str,
        player_type: str,
        amount: int,
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
            "amount": amount,
            "action": self._classify_action(state, amount),
            **(self._classify_hand(hand, state) if hand else {}),
        }
        self._write_df()

    def retrofill_hand_stats(self, state_ids: list[str], hand: tuple[int, int]):
        for state_id in state_ids:
            state_row = self.df.loc[self.df["state_id"] == state_id]
            if state_row.empty:
                raise ValueError(
                    f"State with id {state_id} not found in observer dataframe"
                )
            state = State.from_tuple(state_row.iloc[0][State.TUPLE_HEADERS])
            hand_stats = self._classify_hand(hand, state)
            for k, v in hand_stats.items():
                self.df.loc[self.df["state_id"] == state_id, k] = v
