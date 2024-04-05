from Card import Card
from PlayerABC import Player
from State import State


class HumanPlayer(Player):
    def play(self, state: State) -> int:
        print("Your cards are", Card.get_cli_repr_for_cards(self.hand), "\n")
        try:
            return int(input("Enter your bet: "))
        except ValueError:
            print("Invalid input. Please enter an integer.")
            return self.play(state)
