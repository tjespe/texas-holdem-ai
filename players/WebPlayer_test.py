import unittest
import queue
from players.WebPlayer import WebPlayer


# Minimal placeholder for State with a to_dict method
class MockState:
    def __init__(self, description):
        self.description = description

    def to_dict(self):
        return {"desc": self.description}


class TestWebPlayer(unittest.TestCase):
    def setUp(self):
        self.player = WebPlayer(name="TestPlayer", index=0)

    def test_play_blocks_and_receives_bet(self):
        """
        Ensures that play() blocks until set_bet_from_client is called,
        and that the correct message is placed into _outbox.
        """
        # We'll run play() in a separate thread so we can unblock it:
        import threading

        mock_state = MockState("Test state #1")
        bet_result = None

        def player_play():
            nonlocal bet_result
            bet_result = self.player.play(mock_state)

        # Start thread
        t = threading.Thread(target=player_play)
        t.start()

        # Meanwhile, in the main thread, read from player's outbox
        out_msg = self.player._outbox.get(timeout=1)
        self.assertEqual(out_msg["type"], "PLAY_REQUEST")
        self.assertIn("state", out_msg)
        self.assertEqual(out_msg["state"], {"desc": "Test state #1"})

        # The thread is still blocked, so let's send a bet
        self.player.set_bet_from_client(42)

        # Now join the thread
        t.join(timeout=2)
        self.assertEqual(bet_result, 42)

    def test_observe_bet_puts_message_in_outbox(self):
        mock_state = MockState("Some updated state")
        self.player.observe_bet(mock_state, bet=10)

        msg = self.player._outbox.get(timeout=1)
        self.assertEqual(msg["type"], "OBSERVE_BET")
        self.assertEqual(msg["bet"], 10)
        self.assertEqual(msg["state"], {"desc": "Some updated state"})

    def test_round_over(self):
        mock_state = MockState("Final state")
        self.player.round_over(mock_state)

        msg = self.player._outbox.get(timeout=1)
        self.assertEqual(msg["type"], "ROUND_OVER")
        self.assertEqual(msg["state"], {"desc": "Final state"})

    def test_get_to_know_each_other(self):
        class DummyPlayer:
            def __init__(self, name, index):
                self.name = name
                self.index = index

        others = [DummyPlayer("Alice", 1), DummyPlayer("Bob", 2)]
        self.player.get_to_know_each_other(others)

        msg = self.player._outbox.get(timeout=1)
        self.assertEqual(msg["type"], "GET_TO_KNOW_EACH_OTHER")
        self.assertEqual(len(msg["players"]), 2)
        self.assertEqual(msg["players"][0]["name"], "Alice")

    def test_showdown(self):
        mock_state = MockState("Showdown state")
        all_hands = [(1, 2), None, (13, 47)]
        self.player.showdown(mock_state, all_hands)

        msg = self.player._outbox.get(timeout=1)
        self.assertEqual(msg["type"], "SHOWDOWN")
        self.assertEqual(msg["state"], {"desc": "Showdown state"})
        self.assertEqual(msg["all_hands"], [(1, 2), None, (13, 47)])


if __name__ == "__main__":
    unittest.main()
