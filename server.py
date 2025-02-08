from collections import defaultdict
from datetime import datetime, timedelta
import os
import jwt
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Header,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Union
from uuid import uuid4
import json
import asyncio
import threading
import queue
from PlayerABC import Player
from players.ProbSimPlayer import ProbSimPlayer
from players.AwareRationalPlayerWithRandomStyle import (
    AwareRationalPlayerWithRandomStyle,
)
from players.CheatingPlayer import CheatingPlayer
from players.HumanMocker import HumanMocker
from players.LLMPlayer import LLMPlayer
from players.AllInPlayer import AllInPlayer
from players.AwareRationalPlayer import AwareRationalPlayer
from players.MaxEVandLLMPlayer import MaxEVandLLMPlayer
from players.ProbRegPlayer import ProbRegPlayer
from players.RationalPlayer import RationalPlayer
from pydantic import BaseModel


from login import authenticate_user, register_user
from GameManager import GameManager
from players.WebPlayer import WebPlayer
from players.MaxEVPlayer import MaxEVPlayer
from players.MaxEVandHumanMocker import MaxEVandHumanMocker
from players.RandomPlayer import RandomPlayer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Holds info about all lobbies in memory:
# { lobby_id: {"players": [Union[str, dict]], "started": bool} }
lobbies = {}

# Stores active WebSocket connections per lobby
lobby_connections: Dict[str, List[WebSocket]] = defaultdict(list)

# Holds references to WebPlayer objects:
# { lobby_id: { username: WebPlayer(...) } }
web_players: dict[str, dict[str, WebPlayer]] = {}

bots: list[type[Player]] = [
    MaxEVandHumanMocker,
    AwareRationalPlayerWithRandomStyle,
    MaxEVandLLMPlayer,
    MaxEVPlayer,
    HumanMocker,
    LLMPlayer,
    ProbRegPlayer,
    ProbSimPlayer,
    RationalPlayer,
    AllInPlayer,
    AwareRationalPlayer,
    CheatingPlayer,
    RandomPlayer,
]

SECRET_KEY = os.getenv("SECRET_POKER_AUTH_KEY")
if not SECRET_KEY:
    raise Exception("SECRET_POKER_AUTH_KEY environment variable not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 8  # 8 days


def find_webplayer_object(lobby_id: str, username: str) -> WebPlayer:
    if lobby_id not in web_players:
        raise Exception("Lobby not found")
    if username not in web_players[lobby_id]:
        raise Exception("User not found in lobby")
    return web_players[lobby_id][username]


class LoginRequest(BaseModel):
    username: str
    password: str


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.post("/login")
def login(creds: LoginRequest):
    if authenticate_user(creds.username, creds.password):
        token = create_access_token(creds.username)
        return {"result": "ok", "token": token}
    return {"error": "Invalid credentials"}


@app.post("/register")
def register(creds: LoginRequest):
    if register_user(creds.username, creds.password):
        token = create_access_token(creds.username)
        return {"result": "ok", "token": token}
    return {"error": "Username already exists"}


def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token missing username")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(authorization: str = Header(...)) -> str:
    """
    Extract and validate the token from the Authorization header.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = authorization.split(" ")[1]  # Extract token after "Bearer"
    return get_user_from_token(token)


@app.get("/users/me")
def check_token(user: str = Depends(get_current_user)):
    print("User is:", user)
    return {"user": user}


@app.get("/lobbies")
def get_lobbies():
    # Convert your internal dict to a list
    result = []
    for lobby_id, info in lobbies.items():
        result.append(
            {
                "lobby_id": lobby_id,
                "started": info["started"],
                "players": info["players"],
            }
        )
    return {"lobbies": result}


create_lobby_id = lambda: str(uuid4().hex)[:4]


@app.post("/lobbies")
def create_lobby():
    new_lobby_id = create_lobby_id()
    while new_lobby_id in lobbies:
        new_lobby_id = create_lobby_id()
    lobbies[new_lobby_id] = {"players": [], "started": False}
    web_players[new_lobby_id] = {}
    return {"lobby_id": new_lobby_id}


@app.get("/lobbies/{lobby_id}")
def get_lobby_details(lobby_id: str):
    lobby = lobbies.get(lobby_id)
    if not lobby:
        return {"error": "Lobby not found"}
    return {
        "lobby_id": lobby_id,
        "started": lobby["started"],
        "players": lobby["players"],
    }


@app.post("/lobbies/{lobby_id}/join")
async def join_lobby(lobby_id: str, user: str = Depends(get_current_user)):
    lobby = lobbies[lobby_id]
    if lobby["started"]:
        raise HTTPException(status_code=400, detail="Game already started")

    if user not in lobby["players"]:
        lobby["players"].append(user)
        await broadcast_lobby_update(lobby_id)

    return {"result": "ok", "players": lobby["players"]}


@app.post("/lobbies/{lobby_id}/leave")
async def leave_lobby(lobby_id: str, user: str = Depends(get_current_user)):
    lobby = lobbies[lobby_id]
    if lobby["started"]:
        raise HTTPException(status_code=400, detail="Game already started")

    if user in lobby["players"]:
        lobby["players"].remove(user)
        await broadcast_lobby_update(lobby_id)

    return {"result": "ok", "players": lobby["players"]}


@app.get("/bot-options")
def get_bot_options():
    return [{"name": bot.get_example_name(), "type": bot.__name__} for bot in bots]


@app.post("/lobbies/{lobby_id}/add_bot")
async def add_bot(lobby_id: str, bot_type: str, bot_name: str):
    lobby = lobbies[lobby_id]
    if lobby["started"]:
        raise HTTPException(status_code=400, detail="Game already started")

    bot = {"type": "bot", "bot_type": bot_type, "bot_name": bot_name}
    lobby["players"].append(bot)
    await broadcast_lobby_update(lobby_id)

    return {"result": "ok", "players": lobby["players"]}


@app.post("/lobbies/{lobby_id}/start")
async def start_lobby(lobby_id: str):
    lobby = lobbies[lobby_id]
    lobby["started"] = True

    players = []

    # Build Player objects from the lobby
    for entry in lobby["players"]:
        if isinstance(entry, str):
            # It's a human user
            p = WebPlayer(name=entry)
            # Store in web_players so the websocket route can find it
            web_players[lobby_id][entry] = p
            players.append(p)
        elif entry.get("type") == "bot":
            cls = next((bot for bot in bots if bot.__name__ == entry["bot_type"]), None)
            if cls:
                bot = cls(name=entry["bot_name"])
                players.append(bot)
            else:
                print("Warning: Bot not found:", entry["bot_type"])
                players.append(
                    MaxEVandHumanMocker(name=MaxEVandHumanMocker.get_example_name())
                )
        else:
            # fallback
            players.append(
                MaxEVandHumanMocker(name=MaxEVandHumanMocker.get_example_name())
            )

    gm = GameManager(players, big_blind=4)

    # Run GameManager in a background thread (NOT async),
    # so it doesn't block the main FastAPI event loop.
    def run_game():
        # This might do multiple rounds, etc.
        gm.play_round(print_state=False, sleep=0.5)

    thread = threading.Thread(target=run_game, daemon=True)
    thread.start()

    await broadcast_lobby_update(lobby_id)
    return {"result": "game_started"}


sent_per_webplayer = defaultdict(list)


@app.websocket("/ws/games/{lobby_id}")
async def game_socket(
    websocket: WebSocket, lobby_id: str, token: str = Depends(get_user_from_token)
):
    """
    WebSocket endpoint for a particular (lobby_id, username).
    1) Accept the socket.
    2) Attach it to the corresponding WebPlayer (so we can send e.g. observer updates).
    3) Create two tasks:
       - One to read messages from the client and pass them to WebPlayer
       - One to read messages from WebPlayer._outbox and send them to client
    """
    await websocket.accept()

    username = token

    # Find matching WebPlayer
    web_player = find_webplayer_object(lobby_id, username)

    # Task 1: read messages from client
    async def read_from_client():
        while True:
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            print("Received message from client:", data)
            msg_type = data.get("type")
            if msg_type is None:
                print("Invalid message:", data, "(missing 'type' key)")
                continue
            if msg_type == "USER_BET":
                bet_amount = data.get("bet", 0)
                # This unblocks web_player.play(...)
                web_player.set_bet_from_client(bet_amount)
            elif msg_type == "READY":
                web_player.ready()
            else:
                print("Invalid message:", data, "(unknown 'type' value)")

    # Task 2: send messages from the player's outbox to the client
    # We'll block on the queue in a thread-safe way
    async def send_to_client():
        # Re-send any messages that were sent to the client before they connected
        for message in sent_per_webplayer[web_player]:
            print("Re-sending message to client:", message)
            await websocket.send_text(json.dumps(message))
        while True:
            # readQueue is a small helper that waits for a .get() call in a thread
            message = await readQueue(web_player._outbox)
            print("Sending message to client:", message)
            sent_per_webplayer[web_player].append(message)
            await websocket.send_text(json.dumps(message))

    # Helper function to read from a standard queue in an async way
    async def readQueue(q: queue.Queue):
        """Block on q.get() in a thread, but yield control to the event loop."""
        return await loop.run_in_executor(None, q.get)

    # Start both tasks concurrently
    loop = asyncio.get_event_loop()
    receive_task = loop.create_task(read_from_client())
    send_task = loop.create_task(send_to_client())

    done, pending = await asyncio.wait(
        [receive_task, send_task], return_when=asyncio.FIRST_EXCEPTION
    )

    # If either task errors or disconnects, cancel the other
    for task in pending:
        task.cancel()

    # Optionally handle a clean shutdown (e.g. user disconnect)
    try:
        for task in done:
            task.result()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")


@app.websocket("/ws/lobbies/{lobby_id}")
async def lobby_websocket(websocket: WebSocket, lobby_id: str):
    """WebSocket for real-time lobby updates."""
    await websocket.accept()

    if lobby_id not in lobby_connections:
        lobby_connections[lobby_id] = []
    lobby_connections[lobby_id].append(websocket)

    try:
        while True:
            # Keep connection open and listen for messages (even though we don't expect any)
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Remove the client from the lobby's connection list when they disconnect
        lobby_connections[lobby_id].remove(websocket)


async def broadcast_lobby_update(lobby_id: str):
    """Send the latest lobby state to all connected clients in that lobby."""
    if lobby_id not in lobby_connections or not lobby_connections[lobby_id]:
        return

    lobby = lobbies[lobby_id]
    message = {
        "type": "LOBBY_UPDATE",
        "lobby_id": lobby_id,
        "started": lobby["started"],
        "players": lobby["players"],
    }

    # Send the message to all connected WebSockets asynchronously
    for websocket in list(
        lobby_connections[lobby_id]
    ):  # Copy list to avoid modifying it during iteration
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Failed to send WebSocket message: {e}")
            lobby_connections[lobby_id].remove(websocket)  # Remove broken connections
