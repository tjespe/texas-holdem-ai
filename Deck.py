from math import factorial
from typing import List
import numpy as np

from Card import Card


class Deck:
    cards: List[int]

    def __init__(self):
        self.cards = np.arange(52).tolist()
        self.shuffle()

    def shuffle(self):
        np.random.shuffle(self.cards)

    def draw(self) -> int:
        return self.cards.pop()
