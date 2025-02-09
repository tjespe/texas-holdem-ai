from datetime import datetime
import queue
import threading
from typing import Union

from PlayerABC import Player
from State import State

from cpp_poker.cpp_poker import Oracle, CardCollection
from hidden_state_model.observer import Observer
from state_management import place_bet

time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
observer = Observer(f"hidden_state_model/data/web-player-{time_str}.parquet")


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

        # Event to signal readiness
        self._ready_event = threading.Event()

        # Queue for outgoing messages to the client:
        self._outbox = queue.Queue()

        # Keeps track of the players
        self.players = []

    @property
    def _opponent_names(self):
        if self.players is None:
            return None
        return [p.name for p in self.players if p != self]

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
        observer.observe_action(
            state,
            self.name,
            WebPlayer.__name__,
            bet,
            self._opponent_names,
            self.hand,
        )
        return bet

    def set_bet_from_client(self, bet: int):
        """
        Called by the async server code when it receives a bet
        (e.g. {"type": "USER_BET", "bet": 30}) from the WebSocket.
        This unblocks `play()`.
        """
        print(f"Received bet from client: {bet}")
        self._bet_queue.put(bet)

    def observe_bet(
        self, from_state: State, bet: int, to_state: State, was_blind=False
    ):
        """
        Let the client know that someone has bet.
        """
        message = {
            "type": "OBSERVE_BET",
            "player_index": from_state.current_player_i,
            "bet": bet,
            "from_state": from_state.to_dict(),
            "state": to_state.to_dict(),
            "was_blind": bool(was_blind),
        }
        self._outbox.put(message)

    def bet_rejected(self, from_state, bet, reason):
        print("Bet rejected:", reason, "Letting the client know")
        message = {
            "type": "BET_REJECTED",
            "from_state": from_state.to_dict(),
            "bet": bet,
            "reason": reason,
        }
        self._outbox.put(message)

    def round_over(self, state: State, prev_state: State):
        message = {
            "type": "ROUND_OVER",
            "state": prev_state.to_dict(),
        }
        self._outbox.put(message)

    def get_to_know_each_other(self, players: list["Player"]):
        info = [
            {"name": p.name, "index": p.index, "type": type(p).__name__}
            for p in players
        ]
        message = {"type": "GET_TO_KNOW_EACH_OTHER", "players": info}
        self._outbox.put(message)
        self.players = players

    def showdown(self, state: State, all_hands: list[Union[tuple[int, int], None]]):
        winners = Oracle.find_winner(
            CardCollection(state.public_cards),
            [CardCollection(list(hand) if hand else []) for hand in all_hands],
            state.player_is_active,
        )
        message = {
            "type": "SHOWDOWN",
            "state": state.to_dict(),
            "all_hands": [
                (
                    {
                        "cards": list(hand),
                        "rank": CardCollection(list(hand) + list(state.public_cards))
                        .rank_hand()
                        .get_rank_name(),
                    }
                    if hand
                    else None
                )
                for hand in all_hands
            ],
            "winners": list(winners),
        }
        self._outbox.put(message)

    def get_ready(self):
        self._ready_event.clear()  # Reset event for WebPlayer
        message = {"type": "GET_READY"}
        self._outbox.put(message)

    def ready(self):
        print("Setting ready signal")
        self._ready_event.set()  # Signal readiness when WebSocket message arrives

    def wait_for_ready(self):
        return self._ready_event

    def game_over(self, winner: "Player", state: State):
        message = {
            "type": "GAME_OVER",
            "winner": winner.name,
            "state": state.to_dict(),
        }
        self._outbox.put(message)
