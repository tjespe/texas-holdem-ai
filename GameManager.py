import time
import pandas as pd
import os
from Deck import Deck
from PlayerABC import Player
from State import State
from players.HumanPlayer import HumanPlayer
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

from cpp_poker.cpp_poker import Oracle


class GameManager:
    players: list[Player]
    deck: Deck
    state: State

    def __init__(self, players: list[Player], buy_in: int = 100, big_blind: int = 2):
        for i, player in enumerate(players):
            player.index = i
        self.players = players
        self.deck = Deck()
        self.state = generate_root_state(len(self.players), buy_in, big_blind)
        self.round = 0
        for player in self.players:
            player.get_to_know_each_other(self.players)

    @property
    def player_names(self):
        return [player.name for player in self.players]

    def play_round(self, print_state: bool = False, sleep=0):
        """
        Play a round of poker.
        """
        print("Starting round")
        # Get a new shuffled deck
        self.deck = Deck()
        # Give all players new cards
        for player in self.players:
            player.hand = self.deck.draw_n(2)
        # Start game loop
        while not self.state.is_terminal:
            if sleep:
                time.sleep(sleep)
            # Allow players to cheat
            for player in self.players:
                player.cheat([player.hand for player in self.players])
            if print_state:
                os.system("clear")
                print(f"Round {self.round}")
                print(self.state.get_cli_repr(self.player_names))
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
                from_state = self.state
                self.state = place_bet(from_state, blind_bet, is_blind=True)
                for player in self.players:
                    player.observe_bet(
                        from_state, blind_bet, self.state, was_blind=True
                    )
            else:
                max_bet = Oracle.get_max_bet_allowed(
                    self.state.player_has_played,
                    self.state.current_player_i,
                    self.state.bet_in_stage,
                    self.state.player_piles,
                    self.state.player_is_active,
                )
                if max_bet == 0:
                    bet = 0
                else:
                    print(f"Requesting bet from {player.name}")
                    bet = player.play(self.state)
                print(f"{player.name} bets {bet}")
                try:
                    from_state = self.state
                    self.state = place_bet(from_state, bet)
                    for player in self.players:
                        player.observe_bet(from_state, bet, self.state)
                except BettingRuleViolation as e:
                    print(
                        "\n@@@@@@@@@@@@@@@@@@@@@@@@\nBetting rules violation:\n@@@@@@@@@@@@@@@@@@@@@@@@\n",
                        e,
                    )
                    player.bet_rejected(from_state, bet, str(e))
        if print_state:
            os.system("clear")
            print(self.state.get_cli_repr(self.player_names))
        showdown = self.state.player_is_active.sum() > 1
        if showdown:
            print("Showdown!")
            for player in self.players:
                player.showdown(
                    self.state,
                    [
                        player.hand if self.state.player_is_active[i] else None
                        for i, player in enumerate(self.players)
                    ],
                )
            if sleep:
                time.sleep(sleep)
        prev_state = self.state
        self.state = end_round(prev_state, self.players, print_result=True)
        self.round += 1
        for player in self.players:
            player.round_over(self.state, prev_state)
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
            print(self.state.get_cli_repr(self.player_names))
            winner_list = get_value("winners")
            if winner_list is None:
                winner_list = []
            winner_list.append(winner.name)
            set_value("winners", winner_list)
            for player in self.players:
                player.game_over(winner, self.state)
            stat_file = open("stats/winners.csv", "a")
            pd.DataFrame([
                [datetime.now().isoformat(), self.player_names, winner]
            ]).to_csv(stat_file, index=False, header=False)
            stat_file.close()
            return

        # Request readiness from all players
        for player in self.players:
            if player not in bust_players:
                player.get_ready()

        # Wait for all players to be ready using the exposed method
        for player in self.players:
            player.wait_for_ready().wait()  # Wait for the event

        print("Starting next round")
        self.play_round(print_state=print_state, sleep=sleep)
