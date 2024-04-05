from typing import List
from Deck import Deck
from State import State


class GameManager:
    players: List[Player]
    deck: Deck
    state: State
