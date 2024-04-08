from Deck import Deck
from PlayerABC import Player
from State import State
from state_management import (
    add_cards,
    end_round,
    generate_root_state,
    place_bet,
    skip_current_player,
)


class GameManager:
    players: list[Player]
    deck: Deck
    state: State
    bust_players: set[Player]

    def __init__(self, players: list[Player], buy_in: int = 100, big_blind: int = 2):
        self.players = players
        self.deck = Deck()
        self.state = generate_root_state(len(self.players), buy_in, big_blind)
        self.bust_players = set()

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
            if player in self.bust_players:
                self.state = skip_current_player(self.state)
                continue
            if self.state.folded_players[self.state.current_player_i]:
                self.state = skip_current_player(self.state)
                continue
            bet = player.play(self.state)
            self.state = place_bet(self.state, bet)
        if print_state:
            print(self.state.get_cli_repr())
        self.state, bust_players = end_round(self.state, self.players)
        self.bust_players = self.bust_players.union(bust_players)
        if len(self.bust_players) == len(self.players) - 1:
            # Only one player left, end the game
            print("Game over!")
            print("Winner:", next(iter(set(self.players) - self.bust_players)))
            print("Final state:")
            print(self.state.get_cli_repr())
        else:
            self.play_round(print_state=print_state, sleep=sleep)


if __name__ == "__main__":
    from RandomPlayer import RandomPlayer

    players = [RandomPlayer(), RandomPlayer()]
    game_manager = GameManager(players)
    game_manager.play_round(print_state=True, sleep=0.1)
