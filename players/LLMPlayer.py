import os
from time import sleep

from groq import Groq, InternalServerError
from datetime import datetime
from cpp_poker.cpp_poker import Card, Oracle, CardCollection, CheatSheet, TerminalColors
from PlayerABC import Player
from State import State
import inquirer

from hidden_state_model.observer import Observer

client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)


time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
observer = Observer(f"hidden_state_model/data/llm-{time_str}.parquet")
log_file = open("stats/LLMPlayer.log", "a")


def log(*args, **kwargs):
    print(*args, kwargs, file=log_file, flush=True)


class LLMPlayer(Player):
    name: str
    allow_hints: bool
    opponent_names: list[str]
    player_names: list[str]

    def __init__(
        self,
        name="Lemuel",
        allow_hints=False,
        llm_model="llama-3.3-70b-versatile",
        # llm_model="gemma2-9b-it",
    ):
        super().__init__()
        self.name = name
        self.allow_hints = allow_hints
        self.opponent_names = []
        self.player_names = []
        self.betting_history = []
        self.llm_model = llm_model

    def get_to_know_each_other(self, players: list[Player]):
        self.opponent_names = [p.name for p in players if p != self]
        self.player_names = [p.name for p in players]

    def prompt(self, state: State):
        call_bet = max(state.bet_in_game) - state.bet_in_game[state.current_player_i]
        max_bet = Oracle.get_max_bet_allowed(
            state.player_has_played,
            state.current_player_i,
            state.bet_in_stage,
            state.player_piles,
            state.player_is_active,
        )
        min_raise = call_bet + state.big_blind
        # The player can raise if they enough in their pile and the Oracle's max bet exceeds the call bet
        can_raise = (
            state.player_piles[state.current_player_i] > call_bet
            and max_bet > call_bet
            and min_raise <= max_bet
        )
        if not can_raise and not call_bet:
            # If the player can't raise and the call bet is 0, they can only check, and there
            # is no need to prompt the LLM.
            return 0
        ranges = []
        options = []
        if call_bet:
            options.append(f"- Call (respond with {call_bet})")
            ranges.append(call_bet)
            options.append("- Fold (respond with 0)")
            ranges.append(0)
        else:
            options.append("- Check (respond with 0)")
            ranges.append(0)
        if can_raise:
            options.append(
                f"- Raise (respond with a number in the range {min_raise}-{max_bet} representing how much to increase your bet, not what you raise to. You must raise by at least the big blind so the minimum raise is {min_raise})"
            )
            ranges.append((min_raise, max_bet))
        scenario = (
            "Betting history:\n"
            + (
                "\n".join(self.betting_history)
                if self.betting_history
                else "No players have bet yet."
            )
            + f"\nYour cards are {CardCollection(self.hand).str()}.\n"
            + state.get_cli_repr(self.player_names, short=True)
            + "Your options now are:\n"
            + "\n".join(options)
            + "\nTo be super clear, you must write a number within one of these ranges:\n"
            + "\n".join(f"- {range}" for range in ranges)
        )
        log("Prompt:\n" + scenario + "\n\n")
        system_prompt = f"Your name is {self.name} and you are playing Texas Hold-Em. When prompted with a game history and state, respond with two lines of text, on the first line, only include a single integer representing your bet. On the second line, provide a reasoning."
        if state.stage == "preflop":
            # It has a tendency to be overly aggressive on the preflop
            system_prompt += "Don't be overly aggressive."
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": scenario,
                    },
                ],
                model=self.llm_model,
            )
        except InternalServerError:
            print("Internal server error, retrying in 1s...")
            sleep(1)
            return self.prompt(state)

        response = chat_completion.choices[0].message.content
        bet = response.split("\n")[0]
        log("Response:\n" + response + "\n\n")
        return bet

    def observe_bet(self, from_state, bet):
        player_name = self.player_names[from_state.current_player_i]
        stage = from_state.stage
        self.betting_history.append(f"{player_name} bet {bet} at {stage}")

    def _play(self, state: State) -> int:
        try:
            return int(self.prompt(state))
        except ValueError:
            return self._play(state)

    def play(self, state: State) -> int:
        action = self._play(state)
        observer.observe_action(
            state,
            self.name,
            LLMPlayer.__name__,
            action,
            self.opponent_names,
            self.hand,
        )
        return action

    def __repr__(self) -> str:
        return f"LLMPlayer('{self.name}')"
