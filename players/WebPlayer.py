import queue
import json
from typing import Union, Optional
from abc import ABC, abstractmethod

from PlayerABC import Player
from State import State


class WebPlayer(Player):
    """
    A synchronous Player that blocks in `play()` until the user
    sends a bet from the front-end via an async WebSocket route.
    """

    def __init__(self, name: str):
        self.name = name
        self.hand = None

        # Queue where we block waiting for the bet:
        self._bet_queue = queue.Queue()

        # Queue for outgoing messages to the client:
        self._outbox = queue.Queue()

    def play(self, state: State) -> int:
        """
        Called by the GameManager in a synchronous loop.
        We'll block until the user bet is placed into `_bet_queue`.
        """

        # Send a "it's your turn" message to the client by pushing
        # into the outbox. The async server code will forward it.
        message = {
            "type": "PLAY_REQUEST",
            "player": {"name": self.name, "index": self.index},
            "state": state.to_dict(),  # or however you serialize
            "hand": list(self.hand),
        }
        self._outbox.put(message)

        # Now block until we get a bet from the client:
        bet = self._bet_queue.get()  # blocks this thread
        print(f"Placing bet: {bet}")
        return bet

    def set_bet_from_client(self, bet: int):
        """
        Called by the async server code when it receives a bet
        (e.g. {"type": "USER_BET", "bet": 30}) from the WebSocket.
        This unblocks `play()`.
        """
        print(f"Received bet from client: {bet}")
        self._bet_queue.put(bet)

    def observe_bet(self, from_state: State, bet: int, was_blind=False):
        """
        Let the client know that someone has bet.
        """
        message = {
            "type": "OBSERVE_BET",
            "player_index": from_state.current_player_i,
            "bet": bet,
            "state": from_state.to_dict(),
            "was_blind": bool(was_blind),
        }
        self._outbox.put(message)

    def round_over(self, state: State, prev_state: State):
        message = {"type": "ROUND_OVER", "state": state.to_dict()}
        self._outbox.put(message)

    def get_to_know_each_other(self, players: list["Player"]):
        info = [
            {"name": p.name, "index": p.index, "type": type(p).__name__}
            for p in players
        ]
        message = {"type": "GET_TO_KNOW_EACH_OTHER", "players": info}
        self._outbox.put(message)

    def showdown(self, state: State, all_hands: list[Union[tuple[int, int], None]]):
        message = {"type": "SHOWDOWN", "state": state.to_dict(), "all_hands": all_hands}
        self._outbox.put(message)
