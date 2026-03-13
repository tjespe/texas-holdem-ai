from groq import RateLimitError
import numpy as np
from PlayerABC import Player
from State import State
from players.LLMPlayer import LLMPlayer
from players.MaxEVPlayer import MaxEVPlayer
from players.RandomPlayer import RandomPlayer
from players.RationalPlayer import RationalPlayer
from state_management import place_bet


class MaxEVandLLMPlayer(Player):
    """
    This players uses the LLMPlayer's strategy preflop and the MaxEVPlayer's strategy postflop.
    """

    title = "Decent"

    def __init__(self, name: str = "Max-Lennart"):
        super().__init__()
        self.name = name
        self.max_ev_player = MaxEVPlayer(name)
        self.llm_player = LLMPlayer(
            name,
            behavior_prompt="Don't be too agressive on the preflop: it's okay to raise, but if the other player has raised, prefer calling rather than raising again, and obviously fold instead of calling if the bet is too high and your hand is too weak. Normally, you should only raise if you have a strong hand.",
        )

    def _update_hands(self):
        self.max_ev_player.hand = self.hand
        self.llm_player.hand = self.hand
        self.max_ev_player.index = self.index
        self.llm_player.index = self.index

    def get_to_know_each_other(self, players):
        self._update_hands()
        self.max_ev_player.get_to_know_each_other(players)
        self.llm_player.get_to_know_each_other(players)

    def observe_bet(
        self, from_state: State, bet: int, to_state: State, was_blind=False
    ):
        self._update_hands()
        self.max_ev_player.observe_bet(from_state, bet, to_state, was_blind)
        self.llm_player.observe_bet(from_state, bet, to_state, was_blind)

    def round_over(self, state, prev_state):
        self._update_hands()
        self.max_ev_player.round_over(state, prev_state)
        self.llm_player.round_over(state, prev_state)

    def showdown(self, state, all_hands):
        self._update_hands()
        self.max_ev_player.showdown(state, all_hands)
        self.llm_player.showdown(state, all_hands)

    def play(self, state) -> int:
        self._update_hands()
        if state.stage == "preflop":
            try:
                return self.llm_player.play(state)
            except RateLimitError:
                return self.max_ev_player.play(state)
        else:
            return self.max_ev_player.play(state)

    def __repr__(self) -> str:
        return f"MaxEVandLLMPlayer('{self.name}')"
