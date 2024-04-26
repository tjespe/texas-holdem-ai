from cpp_poker.cpp_poker import Card
from PlayerABC import Player
import oracle


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
        current_bet = state.current_bets[current_player_i]
        call_bet = max(state.current_bets) - current_bet
        winning_prob = oracle.get_winning_prob(
            self.hand,
            state.public_cards,
            state.player_is_active.sum(),
        )
        print(f"Hand:\n{Card.get_cli_repr_for_cards(self.hand)}")
        print(f"Winning prob: {winning_prob}")
        rational_max = winning_prob * state.pot
        avg_forced_loss = (state.big_blind + state.small_blind) / state.n_players
        rational_max += avg_forced_loss
        print(f"Rational max: {rational_max}")
        if call_bet > rational_max:
            print(
                f"Folding, as call bet {call_bet} is greater than rational max {rational_max}"
            )
            return 0
        print(f"Calling {call_bet}")
        return call_bet
