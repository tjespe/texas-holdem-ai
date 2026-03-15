import os
import random
from time import sleep

from groq import Groq, InternalServerError, RateLimitError
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
    print(*args, **kwargs, file=log_file, flush=True)
    if also_print:
        print(*args, **kwargs)


POSSIBLE_MODELS = [
    'openai/gpt-oss-safeguard-20b',
    # 'meta-llama/llama-prompt-guard-2-22m',
     'moonshotai/kimi-k2-instruct',
     # 'canopylabs/orpheus-v1-english',
     'openai/gpt-oss-120b',
     'llama-3.1-8b-instant',
     'qwen/qwen3-32b',
     'groq/compound',
     # 'canopylabs/orpheus-arabic-saudi',
     'allam-2-7b',
     'moonshotai/kimi-k2-instruct-0905',
     # 'meta-llama/llama-prompt-guard-2-86m',
     'groq/compound-mini',
     'meta-llama/llama-4-scout-17b-16e-instruct',
     # 'whisper-large-v3',
     # 'whisper-large-v3-turbo',
     'llama-3.3-70b-versatile',
     'openai/gpt-oss-20b'
]


class LLMPlayer(Player):
    title = "Eloquent"
    name: str
    allow_hints: bool
    opponent_names: list[str]
    players: list[Player]
    reflections: str
    behavior_prompt: str

    def __init__(
        self,
        # name="Lemuel",
        name="Lionel",
        allow_hints=False,
        llm_model="openai/gpt-oss-120b",
        # behavior_prompt="Don't be too agressive on the preflop: it's okay to raise, but if the other player has raised, prefer calling rather than raising again, and obviously fold instead of calling if the bet is too high and your hand is too weak. Normally, you should only raise if you have a strong hand.",
        behavior_prompt="Make well-contemplated decisions, taking into account what you think about the other player's hand, your own hand, the table, expected responses to different moves, expected value, and risk.",
    ):
        super().__init__()
        self.name = name
        self.allow_hints = allow_hints
        self.opponent_names = []
        self.players = []
        self.betting_history = []
        self.llm_model = llm_model
        self.reflections = "I have a tendency to be overly aggressive on the preflop."
        self.behavior_prompt = behavior_prompt

    def get_to_know_each_other(self, players: list[Player]):
        self.opponent_names = [p.name for i, p in enumerate(players) if i != self.index]
        self.players = players

    @property
    def player_names(self):
        return [p.name for p in self.players]

    def _write_list(self, list):
        return ", ".join(list[:-1]) + " and " + list[-1]

    def _capitalize(self, string):
        return string[0].upper() + string[1:]

    def _describe_bets_in_stage(self, state: State):
        bets = state.bet_in_stage
        if state.stage == "preflop":
            bets = [max(b - state.big_blind, 0) for b in bets]
        return (
            self._write_list(
                [
                    (f"{player.name} has" if i != self.index else "you have")
                    + f" bet {bet}"
                    for i, (player, bet) in enumerate(zip(self.players, bets))
                ]
            )
            + f" in the {state.stage} stage.\n"
        )

    def describe_state(self, state: State):
        return (
            "Betting history:\n"
            + (
                "\n".join(self.betting_history)
                if self.betting_history
                else "No players have bet yet."
            )
            + f"\nYour cards are {CardCollection(self.hand).str()}.\n"
            + self._capitalize(
                self._write_list(
                    [
                        (f"{player.name}'s" if i != self.index else "your")
                        + f" stack is {stack}"
                        for i, (player, stack) in enumerate(
                            zip(self.players, state.player_piles)
                        )
                    ]
                )
            )
            + ".\n"
            + f"The pot is {state.pot}.\n"
            + self._describe_bets_in_stage(state)
            + (
                (
                    "The cards on the table are "
                    + CardCollection(state.public_cards).str()
                    + ".\n"
                )
                if state.public_cards
                else "There are no cards on the table yet.\n"
            )
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
        return f"Your name is {self.name} and you are playing Texas Hold-Em."

    def within_ranges(self, bet, ranges):
        for range in ranges:
            if isinstance(range, int):
                if bet == range:
                    return True
            else:
                if range[0] <= bet <= range[1]:
                    return True
        return False

    def prompt(self, system: str, user: str):
        log("Using model: " + self.llm_model + "\n\n")
        log("System prompt:\n" + system + "\n\n")
        log("Prompt:\n" + user + "\n\n")
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system,
                    },
                    {
                        "role": "user",
                        "content": user,
                    },
                ],
                model=self.llm_model,
            )
        except InternalServerError as e:
            log(
                f"Internal server error ({e.status_code} {e.message}), retrying in 1s...",
                also_print=True,
            )
            sleep(1)
            return self.prompt(system, user)
        except RateLimitError:
            log("Rate limit error, switching model...", also_print=True)
            self.llm_model = random.choice(
                list(set(POSSIBLE_MODELS) - {self.llm_model})
            )
            return self.prompt(system, user)
        response = chat_completion.choices[0].message.content
        log("Response:\n" + response + "\n\n")
        return response

    def prompt_for_bet(self, state: State):
        options, ranges = self.describe_options(state)
        if not options:
            return "0"

        equity = CheatSheet.get_winning_probability(
            CardCollection(self.hand),
            CardCollection(state.public_cards),
            sum(state.player_is_active),
            100000,
        )
        n_players = sum(state.player_is_active)
        scenario = (
            self.describe_state(state)
            + f"Your equity (winning probability given cards and public cards) is {equity*100:.2f}% (compare to a baseline of {100/n_players:.2f}% when there are {n_players} players).\n"
            + "Your options now are:\n"
            + "\n".join(options)
            + "\nTo be super clear, you must write a number within one of these ranges:\n"
            + "\n".join(f"- {range}" for range in ranges)
        )
        system_prompt = (
            self.base_prompt
            + self.behavior_prompt
            + "When prompted with a game history and state, respond with two lines of"
            + "text, on the first line, only include a single integer representing your"
            + "bet. On the second line, provide a reasoning.\n"
        )
        if self.reflections:
            system_prompt += (
                " Previously, you have made the following reflections, so keep them in mind:\n"
                + '"'
                + self.reflections.strip()
                + '"'
                + "\nMake sure to consider the betting history in this game and compare it to what you know about your opponents' playstyle when making your decision."
            )
        response = self.prompt(system_prompt, scenario)
        bet = int(response.split("\n")[0])
        # Check if the bet is within the allowed ranges
        if not self.within_ranges(bet, ranges):
            # If it's not, try increasing the bet by the big blind
            bet += state.big_blind
        if not self.within_ranges(bet, ranges):
            # If it's still not within the ranges, return the first option
            opt = ranges[0]
            if isinstance(opt, int):
                return opt
            return opt[0]
        return bet

    def observe_bet(self, from_state, bet, to_state: State, was_blind=False):
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
            return int(self.prompt_for_bet(state))
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
        prompt = f"{self.base_prompt} Reflect on how you and your opponents played this round that was just completed. Is there anything about your opponent you should remember or anything you should change about your own play? Keep it as short as you are able to while including the most relevant information."
        if self.reflections:
            prompt += (
                " Previously, you have made the following reflections, so keep them in mind:\n"
                + self.reflections.strip()
                + "\nReflect both on this round and the game as a whole. If you did not learn anything specific this round, just respond with the pervious reflections."
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
        reflection_scenario += (
            "\nThe final state was:\n"
            + state.get_cli_repr(self.player_names, short=True)
            + "\n."
        )
        winners = Oracle.find_winner(
            CardCollection(state.public_cards),
            [CardCollection(p.hand) for p in self.players],
            state.player_is_active,
        )
        for i, player in enumerate(self.players):
            name = player.name if i != self.index else "You"
            if state.player_is_active[i]:
                rank = (
                    TerminalColors.FOLDED
                    + (
                        CardCollection(list(player.hand) + list(state.public_cards))
                        .rank_hand()
                        .get_rank_name()
                    )
                    + TerminalColors.DEFAULT
                )
                outcome = "won" if i in winners else "lost"
                reflection_scenario += f"{name} {outcome} with {CardCollection(player.hand).str()} ({rank}).\n"
        self.reflections = self.prompt(
            self.reflection_system_prompt, reflection_scenario
        )
        self.betting_history = []

    def round_over(self, new_state: State, prev_state: State):
        if sum(prev_state.player_is_active) > 1:
            # This is a showdown, so we reflect in the showdown method instead so that
            # we can see all hands
            return
        reflection_scenario = "The bets were:\n" + "\n".join(self.betting_history)
        reflection_scenario += (
            "\nThe final state was:\n"
            + prev_state.get_cli_repr(self.player_names, short=True)
            + "\n."
        )
        self.reflections = self.prompt(
            self.reflection_system_prompt, reflection_scenario
        )
        self.betting_history = []

    def __repr__(self) -> str:
        return f"LLMPlayer('{self.name}')"
