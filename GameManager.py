import os
import numpy as np
from Deck import Deck
from PlayerABC import Player
from State import State
from state_management import (
    BettingRuleViolation,
    add_cards,
    end_round,
    generate_root_state,
    get_blind_bet,
    place_bet,
    skip_current_player,
)
from db_interface import get_value, set_value


class GameManager:
    players: list[Player]
    deck: Deck
    state: State

    def __init__(self, players: list[Player], buy_in: int = 100, big_blind: int = 2):
        self.players = players
        self.deck = Deck()
        self.state = generate_root_state(len(self.players), buy_in, big_blind)

    def play_round(self, print_state: bool = False, sleep=0):
        """
        Play a round of poker.
        """
        # Get a new shuffled deck
        self.deck = Deck()
        # Give all players new cards
        for player in self.players:
            player.hand = self.deck.draw_n(2)
        # Start game loop
        while not self.state.is_terminal:
            if sleep:
                import time

                time.sleep(sleep)
            if print_state:
                os.system("clear")
                print(self.state.get_cli_repr())
            if self.state.all_players_are_done:
                # Deal cards
                if self.state.public_cards == ():
                    _burn, *cards = self.deck.draw_n(4)
                    self.state = add_cards(self.state, cards)
                elif len(self.state.public_cards) < 5:
                    _burn, card = self.deck.draw_n(2)
                    self.state = add_cards(self.state, (card,))
                continue
            player = self.players[self.state.current_player_i]
            if not self.state.player_is_active[self.state.current_player_i]:
                self.state = skip_current_player(self.state)
                continue
            if blind_bet := get_blind_bet(self.state):
                self.state = place_bet(self.state, blind_bet, is_blind=True)
            else:
                bet = player.play(self.state)
                try:
                    self.state = place_bet(self.state, bet)
                except BettingRuleViolation as e:
                    print(
                        "\n@@@@@@@@@@@@@@@@@@@@@@@@\nBetting rules violation:\n@@@@@@@@@@@@@@@@@@@@@@@@\n",
                        e,
                    )
                    input("Press enter to continue...")
        if print_state:
            os.system("clear")
            print(self.state.get_cli_repr())
        self.state = end_round(self.state, self.players, print_result=True)
        if sleep:
            input("Press enter to continue...")
        bust_players = set()
        for i, player in enumerate(self.players):
            if self.state.player_piles[i] < self.state.big_blind:
                bust_players.add(player)
        if len(set(self.players) - bust_players) == 1:
            # Only one player left, end the game
            print("Game over!")
            winner = list(set(self.players) - bust_players)[0]
            print("Winner:", winner.name)
            print("Final state:")
            print(self.state.get_cli_repr())
            winner_list = get_value("winners")
            if winner_list is None:
                winner_list = []
            winner_list.append(winner.name)
            set_value("winners", winner_list)
        else:
            self.play_round(print_state=print_state, sleep=sleep)


if __name__ == "__main__":
    from players.RandomPlayer import RandomPlayer
    from players.HumanPlayer import HumanPlayer
    from players.ResolverPlayer import ResolverPlayer
    from players.RationalPlayer import RationalPlayer

    players = [
        RandomPlayer(name="Random Randall"),
        RandomPlayer(name="Random Rhonda"),
        # HumanPlayer(name="Tord"),
        RationalPlayer(name="Rational Rasmus"),
        # ResolverPlayer(name="Resa the Resolver"),
    ]
    game_manager = GameManager(players)
    game_manager.play_round(print_state=True, sleep=0)
