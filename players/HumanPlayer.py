from cpp_poker.cpp_poker import Card, Oracle
from PlayerABC import Player
from State import State
import inquirer


class HumanPlayer(Player):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def play(self, state: State) -> int:
        print("Your cards are")
        print(Card.get_cli_repr_for_cards(self.hand))
        try:
            call_bet = (
                max(state.bet_in_round) - state.bet_in_round[state.current_player_i]
            )
            max_raise = Oracle.get_max_bet_allowed(
                state.player_has_played,
                state.current_player_i,
                state.current_bets,
                state.player_piles,
                state.player_is_active,
            )
            can_raise = (
                state.player_piles[state.current_player_i] > call_bet
                and not state.player_has_played[state.current_player_i]
                and max_raise > call_bet
            )
            options = (
                ["Call" if call_bet else "Check"]
                + (["Raise"] if can_raise else [])
                + (["Fold"] if call_bet else [])
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
                    },
                ),
            ]
            answer = inquirer.prompt(questions)["action"]
            if answer == "Fold":
                return 0
            elif answer == "Call" or answer == "Check":
                return call_bet
            elif answer == "Raise":
                questions = [
                    inquirer.Text(
                        "amount",
                        message=f"How much do you want to bet? Minimum is {call_bet + state.big_blind} and maximum is "
                        + str(max_raise),
                        validate=lambda _, x: x.isdigit(),
                    ),
                ]
                return int(inquirer.prompt(questions)["amount"])
        except ValueError:
            print("Invalid input. Please enter an integer.")
            return self.play(state)

    def __repr__(self) -> str:
        return f"HumanPlayer('{self.name}')"
