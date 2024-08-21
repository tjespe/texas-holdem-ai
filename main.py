from GameManager import GameManager
from players.HumanPlayer import HumanPlayer
from players.MixedPlayer import MixedPlayer
from players.RationalPlayer import RationalPlayer
from players.AwareRationalPlayer import AwareRationalPlayer
from players.ResolverPlayer import ResolverPlayer
from players.RandomPlayer import RandomPlayer

players = [
    HumanPlayer(name="You"),
    AwareRationalPlayer(name="Larnes"),
]

game_manager = GameManager(players, big_blind=4)
game_manager.play_round(print_state=True, sleep=1)
