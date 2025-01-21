# test_server.py
import unittest
from fastapi.testclient import TestClient
from server import app  # Your FastAPI instance


class TestServerEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_lobby(self):
        resp = self.client.post("/lobbies")
        data = resp.json()
        self.assertIn("lobby_id", data)
        self.assertTrue(len(data["lobby_id"]) > 0)

    def test_login(self):
        resp = self.client.post(
            "/login", data={"username": "alice", "password": "secret"}
        )
        data = resp.json()
        self.assertIn("result", data)
        self.assertEqual(data["result"], "ok")


if __name__ == "__main__":
    unittest.main()
