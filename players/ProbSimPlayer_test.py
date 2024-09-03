import unittest
from PlayerABC import Player
from players.HumanPlayer import HumanPlayer
from players.ProbSimPlayer import ProbSimPlayer
from state_management import generate_root_state


class ProbSimPlayerTestCase(unittest.TestCase):
    def test_can_play_preflop(self):
        player = ProbSimPlayer()
        opponent = HumanPlayer(name="Arin")
        players: list[Player] = [player, opponent]
        player.hand = [0, 1]
        opponent.hand = [2, 3]
        for i, p in enumerate(players):
            p.get_to_know_each_other(players)
            p.index = i
        state = generate_root_state(len(players))
        state.current_player_i = 0
        bet = player.play(state)
        assert isinstance(bet, int), f"Expected int, got {type(bet)}"
        assert bet >= 0, f"Expected positive int, got {bet}"
