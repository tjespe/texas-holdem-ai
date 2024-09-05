import inquirer
from GameManager import GameManager
from login import login
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
from players.CheatingPlayer import CheatingPlayer
from players.ProbRegPlayer import ProbRegPlayer
from players.ProbSimPlayer import ProbSimPlayer
from players.MaxEVPlayer import MaxEVPlayer
from players.HumanMocker import HumanMocker

players = [
    HumanPlayer(name=login()),
    # AllInPlayer(name="Aladdin"),
    # AwareRationalPlayer(name="Larnes"),
    # AwareRationalPlayer(name="William", randomness=0.2, aggression_sensitivity=0.5),
    # AwareRationalPlayer(
    #     name="Styggberget", aggression_sensitivity=1.2, randomness=0.05
    # ),
    # AwareRationalPlayerWithRandomStyle(name="Henning", switch_freq=0.1),
    # RandomPlayer(),
    # RationalPlayer(),
    # AwareRationalPlayer(name="Optuna", randomness=0.5, aggression_sensitivity=1.0),
    # CheatingPlayer(),
    # ProbRegPlayer(),
    # ProbSimPlayer(),
    MaxEVPlayer(),
    # HumanMocker(mock="Arin"),
    # HumanMocker(mock="Arin Bavian"),
]

game_manager = GameManager(players, big_blind=4)
game_manager.play_round(
    print_state=True,
    sleep=0.5 if any(isinstance(p, HumanPlayer) for p in players) else 0,
)
