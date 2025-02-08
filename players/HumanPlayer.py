from datetime import datetime
import threading
from cpp_poker.cpp_poker import Card, Oracle, CardCollection, CheatSheet, TerminalColors
from PlayerABC import Player
from State import State
import inquirer

from hidden_state_model.observer import Observer


time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
observer = Observer(f"hidden_state_model/data/human-{time_str}.parquet")


class HumanPlayer(Player):
    name: str
    allow_hints: bool
    opponent_names: list[str]

    def __init__(self, name: str, allow_hints=False):
        super().__init__()
        self.name = name
        self.allow_hints = allow_hints
        self.opponent_names = []

    def get_to_know_each_other(self, players: list[Player]):
        self.opponent_names = [p.name for p in players if p != self]

    def _play(self, state: State, display_cards=True) -> int:
        if display_cards:
            print("Your cards are")
            print(Card.get_cli_repr_for_cards(self.hand))
        try:
            call_bet = (
                max(state.bet_in_game) - state.bet_in_game[state.current_player_i]
            )
            max_bet = Oracle.get_max_bet_allowed(
                state.player_has_played,
                state.current_player_i,
                state.bet_in_stage,
                state.player_piles,
                state.player_is_active,
            )
            # The player can raise if they enough in their pile and the Oracle's max bet exceeds the call bet
            can_raise = (
                state.player_piles[state.current_player_i] > call_bet
                and max_bet > call_bet
            )
            options = (
                ["Call" if call_bet else "Check"]
                + (["Raise"] if can_raise else [])
                + (["Fold"] if call_bet else [])
                + (["Get hint"] if self.allow_hints else [])
            )
            questions = [
                inquirer.List(
                    "action",
                    message="What do you want to do?",
                    choices=options,
                    autocomplete=True,
                    carousel=True,
                    default=options[0],
                    hints={
                        "Fold": "Fold and lose the round",
                        "Call": f"Match the current bet ({call_bet})",
                        "Check": "Pass the turn without betting",
                        "Raise": "Increase the current bet",
                        "Get hint": "Get a hint on what to do",
                    },
                ),
            ]
            answer = inquirer.prompt(questions)["action"]
            if answer == "Fold":
                return 0
            elif answer == "Call" or answer == "Check":
                return call_bet
            elif answer == "Raise":
                min_raise = call_bet + state.big_blind

                def validate(_, x):
                    if not x.isdigit():
                        return False
                    x = int(x)
                    if x == call_bet:
                        call_q = inquirer.prompt(
                            [
                                inquirer.Confirm(
                                    "confirm",
                                    message="So you want to call instead?",
                                    default=False,
                                )
                            ]
                        )
                        if call_q["confirm"]:
                            return True
                        return False
                    if x == 0:
                        fold_q = inquirer.prompt(
                            [
                                inquirer.Confirm(
                                    "confirm",
                                    message="Are you sure you want to fold?",
                                    default=False,
                                )
                            ]
                        )
                        if fold_q["confirm"]:
                            return True
                        return False
                    return min_raise <= x <= max_bet

                questions = [
                    inquirer.Text(
                        "amount",
                        message=f"How much do you want to bet? Minimum is {min_raise} and maximum is {max_bet}",
                        validate=validate,
                    ),
                ]
                resp = inquirer.prompt(questions)
                if resp is None:
                    return self._play(state, display_cards=False)
                return int(resp["amount"])
            elif answer == "Get hint":
                print(" Calculating winning probability...", end="\r")
                winning_prob = CheatSheet.get_winning_probability(
                    CardCollection(self.hand),
                    CardCollection(state.public_cards),
                    sum(state.player_is_active),
                    100000,
                )
                print(
                    f"Your chance of winning (based only on your cards and table cards) is {TerminalColors.BLUE}{winning_prob:.2%}{TerminalColors.DEFAULT}.\n",
                )
                ev = winning_prob * state.pot
                print(
                    f"Given that the pot is {state.pot} your expected value from continuing is {TerminalColors.BLUE}{ev:.2f}{TerminalColors.DEFAULT}.\n"
                )
                if call_bet < ev:
                    print(
                        f"Based on the expected value, you should {TerminalColors.BLUE}call or raise{TerminalColors.DEFAULT}."
                    )
                else:
                    print(
                        f"Based on the expected value, you should {TerminalColors.BLUE}fold{TerminalColors.DEFAULT}."
                    )
                print()  # Add a newline
                return self._play(state, display_cards=False)
        except ValueError:
            print("Invalid input. Please enter an integer.")
            return self._play(state)

    def play(self, state: State) -> int:
        action = self._play(state)
        observer.observe_action(
            state,
            self.name,
            HumanPlayer.__name__,
            action,
            self.opponent_names,
            self.hand,
        )
        return action

    def get_ready(self):
        if self._ready_event is None:
            self._ready_event = threading.Event()
        self._ready_event.clear()
        input("Press enter to continue...")
        self._ready_event.set()

    def wait_for_ready(self):
        return self._ready_event

    def bet_rejected(self, from_state, bet, reason):
        print(
            "\n\nBetting rules violation:\n",
            reason,
        )
        input("Press enter to continue")

    def __repr__(self) -> str:
        return f"HumanPlayer('{self.name}')"
