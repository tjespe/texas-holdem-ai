from cpp_poker.cpp_poker import Card, Oracle, CardCollection
from PlayerABC import Player


class RationalPlayer(Player):
    """
    This player never bets more than what is rational in terms of expected value,
    assuming that the other players are rational as well (which is not a good
    assumption in practice).
    """

    def __init__(self, name: str = "Rasmus"):
        super().__init__()
        self.name = name

    def play(self, state) -> int:
        current_player_i = state.current_player_i
        if state.player_is_folded[current_player_i]:
            return 0
        current_bet = state.bet_in_stage[current_player_i]
        call_bet = max(state.bet_in_stage) - current_bet
        winning_prob = Oracle.get_winning_probability(
            CardCollection(self.hand),
            CardCollection(state.public_cards),
            state.player_is_active.sum(),
        )
        rational_max = winning_prob * state.pot
        avg_forced_loss = (state.big_blind + state.small_blind) / state.n_players
        rational_max += avg_forced_loss
        if call_bet > rational_max:
            return 0
        return call_bet
