from GameManager import GameManager
from players.HumanPlayer import HumanPlayer
from players.MixedPlayer import MixedPlayer
from players.RationalPlayer import RationalPlayer
from players.ResolverPlayer import ResolverPlayer
from players.RandomPlayer import RandomPlayer

players = [
    HumanPlayer(name="You"),
    RationalPlayer(name="Larnes"),
]

game_manager = GameManager(players)
game_manager.play_round(print_state=True, sleep=1)
