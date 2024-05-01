import numpy as np
from PlayerABC import Player
from State import State
from players.RandomPlayer import RandomPlayer
from players.RationalPlayer import RationalPlayer
from players.ResolverPlayer import ResolverPlayer


class MixedPlayer(Player):
    """
    This switches between RandomPlayer and RationalPlayer early in the game,
    but uses ResolverPlayer's strategy from the turn onwards.
    """
    
    def __init__(self, name: str = "Mick", random_factor: float = 0.5):
        super().__init__()
        self.name = name
        self.random_player = RandomPlayer()
        self.rational_player = RationalPlayer()
        self.resolver_player = ResolverPlayer()
        self.random_factor = random_factor

    def _update_hands(self):
        self.random_player.hand = self.hand
        self.rational_player.hand = self.hand
        self.resolver_player.hand = self.hand

    # def observe_bet(self, from_state: State, bet: int):
    #     return self.resolver_player.observe_bet(from_state, bet)

    def play(self, state) -> int:
        self._update_hands()
        if len(state.public_cards) < 4 or sum(state.player_is_active) > 2:
            if np.random.rand() < self.random_factor:
                return self.random_player.play(state)
            return self.rational_player.play(state)
        else:
            return self.resolver_player.play(state)

    def __repr__(self) -> str:
        return f"MixedPlayer('{self.name}')"