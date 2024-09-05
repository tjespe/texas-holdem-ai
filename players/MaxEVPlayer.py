from typing import Literal, Union
import numpy as np
from State import State
from cpp_poker.cpp_poker import CardCollection, CheatSheet, Oracle
from PlayerABC import Player
from hidden_state_model.helpers import get_observer_with_all_data
from hidden_state_model.observer import Observer
from players.CheatingPlayer import combine_probabilities
from state_management import add_cards, place_bet


log_file = open("stats/MaxEVPlayer.log", "a")


def debug_print(indentation: int, *args, **kwargs):
    print(".", end="", flush=True)
    print((indentation * "  ") + "- ", *args, **kwargs, file=log_file, flush=True)


class MaxEVPlayer(Player):
    """
    Player that regresses the opponent's winning probability based on historical data.
    """

    rel_weight_player_in_reg: float
    rel_weight_opponent_in_reg: float
    observer: Observer
    player_names: Union[list[str], None]
    player_types: Union[list[str], None]
    player_probs: Union[np.ndarray, None]
    predicted_ranks: Union[np.ndarray, None]

    def __init__(
        self,
        name: str = "Max Mekker",
        rel_weight_player_in_reg=2,
        rel_weight_opponent_in_reg=2,
    ):
        super().__init__()
        self.name = name
        self.called_bluff = False
        self.is_bluffing = False
        self.player_names = None
        self.observer = get_observer_with_all_data()
        self.player_probs = None
        self.predicted_ranks = None
        self.rel_weight_player_in_reg = rel_weight_player_in_reg
        self.rel_weight_opponent_in_reg = rel_weight_opponent_in_reg

    @property
    def predictor(self):
        return self.observer.predictor

    def predict(
        self,
        attribute: Literal["prob", "rank", "action", "raise"],
        df_row,
        player_name,
        probabilities=False,
    ):
        return self.predictor.predict_for_row(
            attribute,
            df_row,
            player_name,
            self.rel_weight_player_in_reg,
            self.name,
            self.rel_weight_opponent_in_reg,
            probabilities=probabilities,
        )

    def get_to_know_each_other(self, players: list[Player]):
        self.player_names = [p.name for p in players]
        self.player_types = [p.__class__.__name__ for p in players]
        self.player_probs = np.ones(len(self.player_names)) / len(self.player_names)
        self.predicted_ranks = np.zeros(len(self.player_names))

    def round_over(self, state: State):
        self.called_bluff = False
        self.is_bluffing = False
        self.player_probs = np.array(state.player_is_active) / np.sum(
            state.player_is_active
        )
        self.predicted_ranks = np.zeros(len(state.player_is_active))

    def observe_bet(self, from_state: State, bet: int):
        player_i = from_state.current_player_i
        if player_i == self.index:
            return
        player_name = self.player_names[player_i]
        player_type = self.player_types[player_i]
        debug_print(0, "Observing bet from", player_name, "of", bet)
        self.observer.observe_action(
            from_state,
            player_name,
            player_type,
            bet,
            [n for n in self.player_names if n != player_name],
            None,
        )
        df_row = self.observer.get_processed_df_row(from_state.id).drop(
            ["excess_rank", "p", "relative_ev"]
        )
        self.player_probs[player_i] = self.predict("prob", df_row, player_name)
        debug_print(0, "Predicted prob:", self.player_probs[player_i])
        self.predicted_ranks[player_i] = self.predict("rank", df_row, player_name)

    def showdown(self, state: State, all_hands: list[Union[tuple[int, int], None]]):
        for i, hand in enumerate(all_hands):
            if hand is None:
                continue
            if i == self.index:
                continue
            relevant_states = []
            s = state
            while s is not None:
                if s.current_player_i == i:
                    relevant_states.append(s)
                s = s.prev_state
            self.observer.retrofill_hand_stats(relevant_states, hand)

    def simulate_ev(
        self,
        state: State,
        bet_before_simulation: int,
        player_probs: list[float],
        predicted_ranks: list[int],
        observer: Observer,
        print_indentation: int,
        discount_factor: float = 0.95,
    ) -> int:
        """
        Simulates game to end and calculates the expected value of the game, defined as
        the pot won at the end minus any bets made from the beginning of the simulation.
        Bets made before the simulation are included as positive EV because they are
        sunk costs.

        Args:
            state: The current state of the game.
            bet_before_simulation: The total amount bet before the simulation.
            player_probs: The probabilities of each player winning.
            predicted_ranks: The predicted ranks of each player.
            observer: The observer object.
            print_indentation: The indentation level for debug prints.
            discount_factor: The discount factor for future rewards. This is used to
                account for the fact that the simulation is not perfect and that the
                future is uncertain. The payoff of the game is discounted by this factor
                for each step into the future, making payoffs far into the future less
                valuable. The discount factor should be between 0 and 1.

        Returns:
            The expected value of the game.
        """
        # Handle game over
        if state.is_terminal:
            debug_print(print_indentation, "[terminal]")
            bet_in_simulation = state.bet_in_game[self.index] - bet_before_simulation
            if state.player_is_folded[self.index]:
                # In this case, we lose everything we have bet since the beginning of the simulation
                debug_print(
                    print_indentation,
                    f"END: we fold at {state.stage} after having betted {bet_in_simulation} extra (pot size: {state.pot}, value: {-bet_in_simulation})",
                )
                return -bet_in_simulation
            if sum(state.player_is_active) == 1:
                # In this case, we win the pot.
                # We don't count anything we have bet during the simulation as a win.
                # The opponent folding gives us a great payoff, but it's a highly risky strategy,
                # and if we use it too often, the opponent will exploit it, thus we multiply the
                # payoff by a fold discount factor.
                fold_discount_factor = 0.7
                debug_print(
                    print_indentation,
                    f"END: opponent has folded and we win pot {state.pot} (value: {(state.pot - bet_in_simulation)*fold_discount_factor})",
                )
                return state.pot - bet_in_simulation
            # In this case, we have a showdown
            winning_prob = combine_probabilities(player_probs, self.index)
            value_if_win = state.pot - bet_in_simulation
            value_if_loss = -bet_in_simulation
            ev = value_if_win * winning_prob + value_if_loss * (1 - winning_prob)
            debug_print(
                print_indentation,
                f"END: showdown, winning prob: {winning_prob}, value if win: {value_if_win} ({state.pot} - {bet_in_simulation}), value if loss: {value_if_loss}, ev: {ev}",
            )
            return ev

        # Handle table needs card
        if state.all_players_are_done:
            debug_print(print_indentation, "[need cards]")
            n_cards = 3 if state.stage == "preflop" else 1
            debug_print(print_indentation, f"Adding {n_cards} card(s)")
            return (
                self.simulate_ev(
                    # Add a card to progress the game although the card should not matter
                    add_cards(state, tuple(range(n_cards))),
                    bet_before_simulation,
                    player_probs,
                    predicted_ranks,
                    observer,
                    print_indentation + 1,
                    discount_factor,
                )
                * discount_factor
            )

        # Handle own turn
        if state.current_player_i == self.index:
            debug_print(print_indentation, "[our turn]")
            bet, ev = self._play(
                state,
                player_probs,
                predicted_ranks,
                observer,
                print_indentation + 1,
                True,
                bet_before_simulation,
            )
            return ev

        # Handle opponent turn
        debug_print(print_indentation, "[opponent turn]")
        player_i = state.current_player_i
        player_name = self.player_names[player_i]
        observer.observe_state(
            state,
            player_name,
            self.player_types[player_i],
            [name for i, name in enumerate(self.player_names) if i != player_i],
            None,
        )
        df_row = observer.get_processed_df_row(state.id).copy()
        df_row["p"] = player_probs[player_i]
        df_row["excess_rank"] = predicted_ranks[player_i]
        df_row["relative_ev"] = state.pot * player_probs[player_i] / state.game_size
        action = self.predict(
            "action",
            df_row,
            player_name,
        )
        max_allowed = Oracle.get_max_bet_allowed(
            state.player_has_played,
            player_i,
            state.bet_in_stage,
            state.player_piles,
            state.player_is_active,
        )
        call_bet = max(state.bet_in_stage) - state.bet_in_stage[player_i]
        min_raise = call_bet + state.big_blind
        can_raise = call_bet < min_raise < max_allowed
        amount = 0
        if action == "call" or (action == "raise" and not can_raise):
            amount = call_bet
        elif action == "raise":
            amount = int(self.predict("raise", df_row, player_name))
            if amount < min_raise:
                amount = min_raise
            if amount > max_allowed:
                amount = max_allowed
        observer.retrofill_action(state, amount)
        updated_df_row = observer.get_processed_df_row(state.id)
        player_probs = [*player_probs]
        predicted_ranks = [*predicted_ranks]
        player_probs[player_i] = self.predict("prob", updated_df_row, player_name)
        predicted_ranks[player_i] = self.predict("rank", updated_df_row, player_name)
        debug_print(print_indentation, f"Op. bet {amount} at", state.stage)
        return self.simulate_ev(
            place_bet(state, amount),
            bet_before_simulation,
            player_probs,
            predicted_ranks,
            observer,
            print_indentation + 1,
            discount_factor,
        )

    def _play(
        self,
        state: State,
        player_probs: list[float],
        predicted_ranks: list[int],
        observer: Observer,
        indentation: int,
        in_simulation: bool,
        bet_before_simulation=None,
    ) -> int:
        if state.player_is_folded[self.index]:
            return 0
        if bet_before_simulation is None:
            bet_before_simulation = state.bet_in_game[self.index]
        current_bet = state.bet_in_stage[self.index]
        call_bet = max(state.bet_in_stage) - current_bet
        if not in_simulation:
            player_probs[self.index] = CheatSheet.get_winning_probability(
                CardCollection(self.hand),
                CardCollection(state.public_cards),
                state.player_is_active.sum(),
            )
        if not in_simulation:
            debug_print(indentation, "Own hand:", CardCollection(self.hand).str())

        max_allowed_bet = Oracle.get_max_bet_allowed(
            state.player_has_played,
            state.current_player_i,
            state.bet_in_stage,
            state.player_piles,
            state.player_is_active,
        )

        possibilities = {0, call_bet}
        for pot_frac in [0.4, 0.8]:
            bet = int(pot_frac * state.pot)
            if bet > call_bet + state.big_blind and bet < max_allowed_bet:
                possibilities.add(bet)

        if len(possibilities) == 1 and not in_simulation:
            # If there is only one thing to do, and we are not in a simulation, do it
            return possibilities.pop(), None

        evs = {}
        for bet in possibilities:
            if bet not in evs:
                evs[bet] = self.simulate_ev(
                    place_bet(state, bet),
                    bet_before_simulation,
                    player_probs,
                    predicted_ranks,
                    observer.clone(),
                    indentation + 1,
                )

        bet, ev = max(evs.items(), key=lambda x: x[1])
        return bet, ev

    def play(self, state: State) -> int:
        bet, _ev = self._play(
            state,
            self.player_probs,
            self.predicted_ranks,
            self.observer,
            0,
            False,
        )
        return bet


if __name__ == "__main__":
    print("Testing combine_probabilities")
    for case in [[0.3, 0.7], [0.45, 0.55], [0.9, 0.5], [0.99, 0.5]]:
        print("\n\nCase:", case)
        print("Combined prob:", combine_probabilities(case, 1))
