from GameManager import GameManager
from players.AllInPlayer import AllInPlayer
from players.AwareRationalPlayerWithRandomStyle import (
    AwareRationalPlayerWithRandomStyle,
)
from players.HumanPlayer import HumanPlayer
from players.MixedPlayer import MixedPlayer
from players.RationalPlayer import RationalPlayer
from players.AwareRationalPlayer import AwareRationalPlayer
from players.ResolverPlayer import ResolverPlayer
from players.RandomPlayer import RandomPlayer

players = [
    # HumanPlayer(name="You"),
    AllInPlayer(name="Aladdin"),
    AwareRationalPlayer(name="Larnes"),
    AwareRationalPlayer(name="William", randomness=0.2, aggression_sensitivity=0.5),
    AwareRationalPlayer(
        name="Styggberget", aggression_sensitivity=1.2, randomness=0.05
    ),
    AwareRationalPlayerWithRandomStyle(name="Henning", switch_freq=0.1),
    RandomPlayer(),
    RationalPlayer(),
    AwareRationalPlayer(name="Optuna", randomness=0.5, aggression_sensitivity=1.0),
]

game_manager = GameManager(players, big_blind=4)
game_manager.play_round(print_state=True, sleep=0)
