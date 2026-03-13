from groq import RateLimitError
from PlayerABC import Player
from State import State
from players.HumanMocker import HumanMocker
from players.MaxEVPlayer import MaxEVPlayer


class MaxEVandHumanMocker(Player):
    """
    This player uses the HumanMocker's strategy in the beginning of the game to save
    time, and then switches to the MaxEVPlayer's strategy.
    """

    title = "Bot"

    def __init__(self, name: str = "Mr. Max"):
        super().__init__()
        self.name = name
        self.max_ev_player = MaxEVPlayer(name)
        self.human_mocker = HumanMocker("Tord")

    def _update_hands(self):
        self.max_ev_player.hand = self.hand
        self.human_mocker.hand = self.hand
        self.max_ev_player.index = self.index
        self.human_mocker.index = self.index

    def get_to_know_each_other(self, players):
        self._update_hands()
        self.max_ev_player.get_to_know_each_other(players)
        self.human_mocker.get_to_know_each_other(players)

    def observe_bet(
        self, from_state: State, bet: int, to_state: State, was_blind=False
    ):
        self._update_hands()
        self.max_ev_player.observe_bet(from_state, bet, to_state, was_blind)
        self.human_mocker.observe_bet(from_state, bet, to_state, was_blind)

    def round_over(self, state, prev_state):
        self._update_hands()
        self.max_ev_player.round_over(state, prev_state)
        self.human_mocker.round_over(state, prev_state)

    def showdown(self, state, all_hands):
        self._update_hands()
        self.max_ev_player.showdown(state, all_hands)
        self.human_mocker.showdown(state, all_hands)

    def play(self, state) -> int:
        self._update_hands()
        if state.stage == "preflop" or (
            state.stage == "flop" and state.sub_stage == "first_bet"
        ):
            return self.human_mocker.play(state)
        else:
            return self.max_ev_player.play(state)

    def __repr__(self) -> str:
        return f"MaxEVandLLMPlayer('{self.name}')"
