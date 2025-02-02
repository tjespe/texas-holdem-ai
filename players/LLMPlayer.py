import os
from time import sleep

from groq import Groq, InternalServerError
from datetime import datetime
from cpp_poker.cpp_poker import Card, Oracle, CardCollection, CheatSheet, TerminalColors
from PlayerABC import Player
from State import State
import inquirer

from hidden_state_model.observer import Observer
from state_management import get_blind_bet

client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)


time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
observer = Observer(f"hidden_state_model/data/llm-{time_str}.parquet")
log_file = open("stats/LLMPlayer.log", "a")


def log(*args, also_print=False, **kwargs):
    print(*args, kwargs, file=log_file, flush=True)
    if also_print:
        print(*args, kwargs)


class LLMPlayer(Player):
    name: str
    allow_hints: bool
    opponent_names: list[str]
    player_names: list[str]
    reflections: str
    behavior_prompt: str

    def __init__(
        self,
        name="Lemuel",
        allow_hints=False,
        llm_model="llama-3.3-70b-versatile",
        # llm_model="llama3-70b-8192",
        behavior_prompt="",
    ):
        super().__init__()
        self.name = name
        self.allow_hints = allow_hints
        self.opponent_names = []
        self.player_names = []
        self.betting_history = []
        self.llm_model = llm_model
        self.reflections = "I have a tendency to be overly aggressive on the preflop."
        self.behavior_prompt = behavior_prompt

    def get_to_know_each_other(self, players: list[Player]):
        self.opponent_names = [p.name for p in players if p != self]
        self.player_names = [p.name for p in players]

    def describe_state(self, state: State):
        return (
            "Betting history:\n"
            + (
                "\n".join(self.betting_history)
                if self.betting_history
                else "No players have bet yet."
            )
            + f"\nYour cards are {CardCollection(self.hand).str()}.\n"
            + state.get_cli_repr(self.player_names, short=True)
        )

    def describe_options(self, state: State):
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
            return [], []
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
            if min_raise == max_bet:
                ranges.append(min_raise)
            else:
                ranges.append((min_raise, max_bet))
        return options, ranges

    @property
    def base_prompt(self):
        return f"Your name is {self.name} and you are playing Texas Hold-Em. {self.behavior_prompt}"

    def prompt(self, state: State):
        options, ranges = self.describe_options(state)
        if not options:
            return "0"
        scenario = (
            self.describe_state(state)
            + "Your options now are:\n"
            + "\n".join(options)
            + "\nTo be super clear, you must write a number within one of these ranges:\n"
            + "\n".join(f"- {range}" for range in ranges)
        )
        system_prompt = (
            self.base_prompt
            + "When prompted with a game history and state, respond with two lines of"
            + "text, on the first line, only include a single integer representing your"
            + "bet. On the second line, provide a reasoning.\n"
        )
        if self.reflections:
            system_prompt += (
                " Previously, you have made the following reflections, so keep them in mind:\n"
                + self.reflections
            )
        log("System prompt:\n" + system_prompt + "\n\n")
        log("Prompt:\n" + scenario + "\n\n")
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
            log("Internal server error, retrying in 1s...", also_print=True)
            sleep(1)
            return self.prompt(state)

        response = chat_completion.choices[0].message.content
        bet = response.split("\n")[0]
        log("Response:\n" + response + "\n\n")
        return bet

    def observe_bet(self, from_state, bet, was_blind=False):
        player_name = self.player_names[from_state.current_player_i]
        if player_name == self.name:
            player_name = "You"
        stage = from_state.stage
        prev_bet = from_state.bet_in_game[from_state.current_player_i]
        call_bet = max(from_state.bet_in_game) - prev_bet
        blind_bet = get_blind_bet(from_state)
        max_bet = Oracle.get_max_bet_allowed(
            from_state.player_has_played,
            from_state.current_player_i,
            from_state.bet_in_stage,
            from_state.player_piles,
            from_state.player_is_active,
        )
        player_pile = from_state.player_piles[from_state.current_player_i]
        if player_pile == 0:
            self.betting_history.append(
                f"{player_name} is already all in and had to check at {stage}"
            )
        elif max_bet == 0:
            self.betting_history.append(
                f"{player_name} was forced to check at {stage} because higher bets could not be matched"
            )
        elif player_pile == bet:
            self.betting_history.append(f"{player_name} went all in at {stage}")
        else:
            if blind_bet:
                if bet == blind_bet:
                    self.betting_history.append(
                        f"{player_name} posted the blind bet of {blind_bet} at {stage}"
                    )
                else:
                    raise Exception("Blind bet violation")
            elif call_bet:
                if bet == 0:
                    self.betting_history.append(f"{player_name} folded at {stage}")
                if bet == call_bet:
                    self.betting_history.append(f"{player_name} called at {stage}")
                if bet > call_bet:
                    self.betting_history.append(
                        f"{player_name} raised to {prev_bet + bet} at {stage}"
                    )
            else:
                if bet == 0:
                    self.betting_history.append(f"{player_name} checked at {stage}")
                if bet:
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

    @property
    def reflection_system_prompt(self):
        prompt = f"{self.base_prompt} Reflect on how you and your opponents played this round that was just completed. Is there anything about your opponent you should remember or anything you should change about your own play?"
        if self.reflections:
            prompt += (
                " Previously, you have made the following reflections, so keep them in mind:\n"
                + self.reflections
                + "\nReflect both on this round and the game as a whole and keep it short."
            )
        return prompt

    def showdown(self, state, all_hands):
        reflection_scenario = "The game came to a showdown. Here are the hands:\n"
        for i, hand in enumerate(all_hands):
            if hand:
                reflection_scenario += (
                    f"{self.player_names[i]}: {CardCollection(hand).str()}\n"
                )
            else:
                reflection_scenario += f"{self.player_names[i]} folded\n"
        reflection_scenario += "The bets were:\n" + "\n".join(self.betting_history)
        reflection_scenario += "The final state was:\n" + state.get_cli_repr(
            self.player_names, short=True
        )
        try:
            log("Reflection system prompt:\n" + self.reflection_system_prompt + "\n\n")
            log("Reflection scenario:\n" + reflection_scenario + "\n\n")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.reflection_system_prompt,
                    },
                    {
                        "role": "user",
                        "content": reflection_scenario,
                    },
                ],
                model=self.llm_model,
            )
            self.reflections = chat_completion.choices[0].message.content
            log("Reflection response:\n" + self.reflections + "\n\n")
            self.betting_history = []
        except InternalServerError:
            log("Internal server error, retrying in 1s...", also_print=True)
            sleep(1)
            return self.showdown(state, all_hands)

    def round_over(self, new_state: State, prev_state: State):
        if sum(prev_state.player_is_active) > 1:
            # This is a showdown, so we reflect in the showdown method instead so that
            # we can see all hands
            return
        reflection_scenario = self.describe_state(prev_state)
        try:
            log("Reflection system prompt:\n" + self.reflection_system_prompt + "\n\n")
            log("Reflection scenario:\n" + reflection_scenario + "\n\n")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.reflection_system_prompt,
                    },
                    {
                        "role": "user",
                        "content": reflection_scenario,
                    },
                ],
                model=self.llm_model,
            )
            self.reflections = chat_completion.choices[0].message.content
            log("Reflection response:\n" + self.reflections + "\n\n")
            self.betting_history = []
        except InternalServerError:
            log("Internal server error, retrying in 1s...", also_print=True)
            sleep(1)
            return self.round_over(new_state, prev_state)

    def __repr__(self) -> str:
        return f"LLMPlayer('{self.name}')"
