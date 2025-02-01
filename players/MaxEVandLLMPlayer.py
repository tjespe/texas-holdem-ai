from groq import RateLimitError
import numpy as np
from PlayerABC import Player
from State import State
from players.LLMPlayer import LLMPlayer
from players.MaxEVPlayer import MaxEVPlayer
from players.RandomPlayer import RandomPlayer
from players.RationalPlayer import RationalPlayer
from players.ResolverPlayer import ResolverPlayer
from state_management import place_bet


class MaxEVandLLMPlayer(Player):
    """
    This switches between RandomPlayer and RationalPlayer early in the game,
    but uses ResolverPlayer's strategy from the turn onwards.
    """

    def __init__(self, name: str = "Max-Lennart"):
        super().__init__()
        self.name = name
        self.max_ev_player = MaxEVPlayer(name)
        self.llm_player = LLMPlayer(name)

    def _update_hands(self):
        self.max_ev_player.hand = self.hand
        self.llm_player.hand = self.hand
        self.max_ev_player.index = self.index
        self.llm_player.index = self.index

    def get_to_know_each_other(self, players):
        self.max_ev_player.get_to_know_each_other(players)
        self.llm_player.get_to_know_each_other(players)

    def observe_bet(self, from_state: State, bet: int):
        self.max_ev_player.observe_bet(from_state, bet)
        self.llm_player.observe_bet(from_state, bet)

    def round_over(self, state):
        self.max_ev_player.round_over(state)
        self.llm_player.round_over(state)

    def showdown(self, state, all_hands):
        self.max_ev_player.showdown(state, all_hands)
        self.llm_player.showdown(state, all_hands)

    def play(self, state) -> int:
        self._update_hands()
        if len(state.public_cards) < 4:
            try:
                return self.llm_player.play(state)
            except RateLimitError:
                return self.max_ev_player.play(state)
        else:
            return self.max_ev_player.play(state)

    def __repr__(self) -> str:
        return f"MaxEVandLLMPlayer('{self.name}')"
