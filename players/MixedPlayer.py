import numpy as np
from PlayerABC import Player
from State import State
from players.RandomPlayer import RandomPlayer
from players.RationalPlayer import RationalPlayer
from players.ResolverPlayer import ResolverPlayer
from state_management import place_bet


class MixedPlayer(Player):
    """
    This switches between RandomPlayer and RationalPlayer early in the game,
    but uses ResolverPlayer's strategy from the turn onwards.
    """

    def __init__(self, name: str = "Mick", random_factor: float = 0.2):
        super().__init__()
        self.name = name
        self.random_player = RandomPlayer()
        self.rational_player = RationalPlayer()
        self.resolver_player = ResolverPlayer(max_simulations=5)
        self.random_factor = random_factor

    def _update_hands(self):
        self.random_player.hand = self.hand
        self.rational_player.hand = self.hand
        self.resolver_player.hand = self.hand
        self.random_player.index = self.index
        self.rational_player.index = self.index
        self.resolver_player.index = self.index

    def observe_bet(
        self, from_state: State, bet: int, to_state: State, was_blind=False
    ):
        if len(from_state.public_cards) < 4:
            # No need to observe this, because the neural nets for these stages
            # are not good enough.
            return
        if place_bet(from_state, bet, False).is_terminal:
            # No need to observe this, because the game will be over before we
            # can use this information.
            return
        if from_state.stage == "turn" and from_state.sub_stage == "first_bet":
            # We are 3 steps away from the river card, so it's a bit
            # too early to use the resolver player.
            return
        return self.resolver_player.observe_bet(from_state, bet, to_state, was_blind)

    def play(self, state) -> int:
        self._update_hands()
        if len(state.public_cards) < 4 or sum(state.player_is_active) > 2:
            if np.random.rand() < self.random_factor:
                return self.random_player.play(state)
            return self.rational_player.play(state)
        else:
            if state.stage == "turn" and state.sub_stage == "first_bet":
                # We are 3 steps away from the river card, so it's a bit
                # too early to use the resolver player.
                return self.rational_player.play(state)
            return self.resolver_player.play(state)

    def __repr__(self) -> str:
        return f"MixedPlayer('{self.name}')"
