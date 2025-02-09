from abc import ABC, abstractmethod
import random
import threading
from typing import Union

import numpy as np

from State import State


class Player(ABC):
    hand: Union[tuple[int, int], None] = None
    index: Union[int, None] = None
    name: str
    example_names = [
        "Alice",
        "Bob",
        "Charlie",
        "David",
        "Eve",
        "Frank",
        "Grace",
        "Heidi",
        "Ivan",
        "Judy",
        "Kevin",
        "Linda",
        "Mallory",
        "Nancy",
        "Oscar",
        "Peggy",
        "Quentin",
        "Romeo",
        "Sue",
        "Trent",
        "Ursula",
        "Victor",
        "Walter",
        "Xander",
        "Yvonne",
        "Zelda",
    ]
    title = None
    # Event to signal readiness
    _ready_event = None

    @classmethod
    def get_example_name(cls):
        name = random.choice(cls.example_names)
        if cls.title is not None:
            name = f"{name} the {cls.title}"
        return name

    @abstractmethod
    def play(self, state: State) -> int:
        """
        Given the current state of the game, return the amount of money to bet.
        0 is treated as check/call/fold depending on the context.
        """

    def observe_bet(
        self, from_state: State, bet: int, to_state: State, was_blind=False
    ):
        """
        This method allows the player to observe what other players are doing.
        Every time the state changes, the game manager will call this method
        for every player.
        """
        # By default, do nothing
        pass

    def bet_rejected(self, from_state: State, bet: int, reason: str):
        """
        This method is called if the player's bet is rejected by the game
        manager. This can happen if they raise by less than the big blind, for
        example.
        """
        # By default, do nothing
        pass

    def round_over(self, new_state: State, prev_state: State):
        """
        This method is called when the round is over, in case the player wants
        to do something, e.g. clean up state variables.
        """
        # By default, do nothing
        pass

    def cheat(self, hands: list[tuple[int, int]]):
        """
        This method allows the player to look at the other players' hands.
        """
        # By default, do nothing
        pass

    def get_to_know_each_other(self, players: list["Player"]):
        """
        This method is called by the manager in the beginning of the game and
        allows the players to know each other's names and types.
        """
        # By default, do nothing
        pass

    def showdown(self, state: State, all_hands: list[Union[tuple[int, int], None]]):
        """
        This method is called when the game is over and the player can see
        the hands of all other players in the game.
        """
        # By default, do nothing
        pass

    def get_ready(self):
        """
        Default implementation: immediately signal readiness.
        """
        if self._ready_event is None:
            self._ready_event = threading.Event()
            self._ready_event.set()  # Default to always ready

    def wait_for_ready(self):
        """
        Exposes an appropriate synchronization object for GameManager.
        Default is an event that is always set (for bot players).
        """
        if self._ready_event is None:
            self._ready_event = threading.Event()
        return self._ready_event

    def game_over(self, winner: "Player", state: State):
        """
        This method is called when only one player is left in the game (the winner).
        """
        # By default, do nothing
