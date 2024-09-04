from typing import Union
import numpy as np
from State import State
from cpp_poker.cpp_poker import CardCollection, CheatSheet, Oracle
from PlayerABC import Player
from helpers import get_random_betting_distribution
from hidden_state_model.helpers import get_observer_with_all_data
from hidden_state_model.observer import Observer
from state_management import add_cards, place_bet


log_file = open("stats/ProbSimPlayer.log", "a")


def debug_print(indentation: int, *args, **kwargs):
    print(".", end="", flush=True)
    print((indentation * "  ") + "- ", *args, **kwargs, file=log_file, flush=True)


def combine_probabilities(
    probs: list[float], player_i: int, print_indentation: Union[int, None] = None
) -> float:
    """
    Combine probabilities of winning for all players except player_i.
    """
    # Map each probability into the probability that they win and no opponents
    # win, then sum them up
    if print_indentation is not None:
        debug_print(print_indentation, "Probs:", probs)
    mapped_probs = [
        # Probability of player i winning
        probs[i]
        # Probability of no other player winning
        * np.prod(1 - np.array([p for j, p in enumerate(probs) if i != j]))
        for i in range(len(probs))
    ]
    if print_indentation is not None:
        debug_print(print_indentation, "Mapped probs:", mapped_probs)
    mapped_probs = np.array(mapped_probs) / np.sum(mapped_probs)
    if print_indentation is not None:
        debug_print(print_indentation, "Mapped probs normalized:", mapped_probs)
    return mapped_probs[player_i]


class Simulator:
    def __init__(self, players: list[Player]) -> None:
        self.players = players

    def simulate_game(self, state: State) -> int:
        if state.all_players_are_done:
            pass


class ProbSimPlayer(Player):
    """
    Player that regresses the opponent's winning probability based on historical data.
    """

    bluff_prob: float
    rel_weight_player_in_reg: float
    called_bluff: bool
    is_bluffing: bool
    observer: Observer
    player_names: Union[list[str], None]
    player_types: Union[list[str], None]
    player_probs: Union[np.ndarray, None]
    predicted_ranks: Union[np.ndarray, None]

    def __init__(
        self, name: str = "Regine", bluff_prob=0.08, rel_weight_player_in_reg=2
    ):
        super().__init__()
        self.name = name
        self.bluff_prob = bluff_prob
        self.called_bluff = False
        self.is_bluffing = False
        self.player_names = None
        self.observer = get_observer_with_all_data()
        self.player_probs = None
        self.predicted_ranks = None
        self.rel_weight_player_in_reg = rel_weight_player_in_reg

    @property
    def predictor(self):
        return self.observer.predictor

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
        print("Observing bet from", player_name, "of", bet)
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
        self.player_probs[player_i] = self.observer.predictor.predict_for_row(
            "prob", df_row, player_name, self.rel_weight_player_in_reg
        )
        self.predicted_ranks[player_i] = self.observer.predictor.predict_for_row(
            "rank", df_row, player_name, self.rel_weight_player_in_reg
        )

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
        # print("Simulate EV called with probs:", player_probs)
        """
        Simulates game to end and calculates the expected value of the game, defined as
        the pot won at the end minus any bets made from the beginning of the simulation.
        Bets made before the simulation are included as positive EV because they are
        sunk costs.
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
                # In this case, we win the pot
                # We don't count anything we have bet during the simulation as a win
                debug_print(
                    print_indentation,
                    f"END: opponent has folded and we win pot {state.pot} (value: {state.pot - bet_in_simulation})",
                )
                return state.pot - bet_in_simulation
            # In this case, we have a showdown
            winning_prob = combine_probabilities(
                player_probs, self.index, print_indentation=None
            )
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
            bet = self._play(
                state,
                player_probs,
                predicted_ranks,
                observer,
                print_indentation + 1,
                bet_before_simulation,
                in_simulation=True,
            )
            debug_print(print_indentation, f"We bet {bet} at {state.stage}")
            return (
                self.simulate_ev(
                    place_bet(state, bet),
                    bet_before_simulation,
                    [*player_probs],
                    predicted_ranks,
                    observer,
                    print_indentation + 1,
                    discount_factor,
                )
                * discount_factor
            )

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
        df_row = observer.get_processed_df_row(state.id)
        df_row["p"] = player_probs[player_i]
        df_row["excess_rank"] = predicted_ranks[player_i]
        df_row["relative_ev"] = state.pot * player_probs[player_i] / state.game_size
        actions, distrib = self.predictor.predict_for_row(
            "action",
            df_row,
            player_name,
            self.rel_weight_player_in_reg,
            probabilities=True,
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
        player_probs = [*player_probs]
        predicted_ranks = [*predicted_ranks]
        prob_threshold = 0.6  # at preflop
        if state.stage == "flop":
            prob_threshold = 0.5
        elif state.stage == "turn":
            prob_threshold = 0.4
        elif state.stage == "river":
            prob_threshold = 0
        if prob_threshold > max(distrib):
            prob_threshold = max(distrib)
        mapped_actions = []
        mapped_probs = []
        evs = []
        for action, prob in zip(actions, distrib):
            if prob < prob_threshold:
                # Skip actions with low probability
                continue
            if action == "fold" or action == "check":
                bet = 0
                if bet not in mapped_actions:
                    mapped_actions.append(bet)
                    mapped_probs.append(prob)
                else:
                    i = mapped_actions.index(bet)
                    mapped_probs[i] += prob
            elif action == "call" or (action == "raise" and not can_raise):
                bet = call_bet
                if bet not in mapped_actions:
                    mapped_actions.append(bet)
                    mapped_probs.append(prob)
                else:
                    i = mapped_actions.index(bet)
                    mapped_probs[i] += prob
            elif action == "raise":
                amount = int(
                    self.observer.predictor.predict_for_row(
                        "raise",
                        df_row,
                        player_name,
                        self.rel_weight_player_in_reg,
                    )
                )
                if amount < min_raise:
                    amount = min_raise
                if amount > max_allowed:
                    amount = max_allowed
                if amount not in mapped_actions:
                    mapped_actions.append(amount)
                    mapped_probs.append(prob)
                else:
                    i = mapped_actions.index(amount)
                    mapped_probs[i] += prob
            else:
                raise ValueError(f"Unknown action: {action}")
        for bet in mapped_actions:
            observer.retrofill_action(
                state,
                bet,
            )
            player_probs = [*player_probs]
            updated_df_row = observer.processor.get_df_row(state.id)
            player_probs[player_i] = self.predictor.predict_for_row(
                "prob", updated_df_row, player_name, self.rel_weight_player_in_reg
            )
            predicted_ranks[player_i] = self.predictor.predict_for_row(
                "rank",
                updated_df_row,
                player_name,
                self.rel_weight_player_in_reg,
            )
            debug_print(print_indentation, f"Op. bet {bet} at", state.stage)
            evs.append(
                self.simulate_ev(
                    place_bet(state, bet),
                    bet_before_simulation,
                    player_probs,
                    predicted_ranks,
                    observer,
                    print_indentation + 1,
                    discount_factor,
                )
            )
        result = np.dot(mapped_probs, evs) / sum(mapped_probs)
        if np.isnan(result):
            print("NaN result in simulate_ev")
            print("mapped_probs:", mapped_probs)
            print("evs:", evs)
            print("dot:", np.dot(mapped_probs, evs))
            print("prob sum:", sum(mapped_probs))
            print("prob threshold:", prob_threshold)
        return result

    def _play(
        self,
        state: State,
        player_probs: list[float],
        predicted_ranks: list[int],
        observer: Observer,
        indentation: int,
        bet_before_simulation: int,
        in_simulation: bool,
    ) -> int:
        if state.player_is_folded[self.index]:
            return 0
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
        winning_prob = combine_probabilities(
            player_probs,
            self.index,
            print_indentation=indentation if not in_simulation else None,
        )
        if not in_simulation:
            debug_print(indentation, "Combined winning prob:", winning_prob)
        is_bluffing = self.is_bluffing
        continue_ev = self.simulate_ev(
            place_bet(state, call_bet),
            bet_before_simulation,
            player_probs,
            predicted_ranks,
            observer.clone(),
            indentation + 1,
        )
        if not in_simulation:
            debug_print(indentation, "EV of continuing:", continue_ev)
        # Reset is_bluffing to what it was before the simulation in case it was changed
        self.is_bluffing = is_bluffing
        can_bluff = not place_bet(state, call_bet).is_terminal
        if can_bluff and (is_bluffing or np.random.rand() < self.bluff_prob):
            continue_ev *= 2
            self.is_bluffing = True
            if not in_simulation:
                debug_print(indentation, "Bluffing, so increasing ev to:", continue_ev)
        rational_max = continue_ev
        if not in_simulation:
            debug_print(indentation, "Rational max:", rational_max)
        if call_bet > rational_max:
            # If the other player was irrational, join based on winning chance
            pot_before_bet = state.pot - call_bet
            if call_bet > pot_before_bet:
                if not in_simulation:
                    debug_print(
                        indentation,
                        "Call bet is higher than pot before bet, evaluating whether to call",
                    )
                if np.random.rand() < winning_prob:
                    if not in_simulation:
                        debug_print(indentation, "Calling")
                    return call_bet
            if not in_simulation:
                debug_print(indentation, "Folding")
            return 0

        max_allowed_bet = Oracle.get_max_bet_allowed(
            state.player_has_played,
            state.current_player_i,
            state.bet_in_stage,
            state.player_piles,
            state.player_is_active,
        )
        max_bet = min(int(rational_max), max_allowed_bet)
        if not in_simulation:
            debug_print(indentation, "Max allowed bet:", max_allowed_bet)
            debug_print(indentation, "Max bet:", max_bet)

        # Return random int between call_bet and rational_max
        likelihood_decay = 0.5 - 0.3 * len(state.public_cards) / 5
        if winning_prob > 0.65 and state.stage == "river":
            # If we have a good hand, try to get more in the pot
            likelihood_decay = 0.05
        distribution = get_random_betting_distribution(
            call_bet,
            max_bet,
            state.big_blind,
            always_add_fold_chance=False,
            likelihood_decay=likelihood_decay,
        )
        if not in_simulation:
            for i, d in enumerate(distribution):
                debug_print(indentation, f"Bet: {i}, prob: {d}")
        return np.random.choice(len(distribution), p=distribution)

    def play(self, state: State) -> int:
        current_bet = state.bet_in_stage[self.index]
        call_bet = max(state.bet_in_stage) - current_bet
        bet_before_simulation = state.bet_in_game[self.index] + call_bet
        return self._play(
            state,
            self.player_probs,
            self.predicted_ranks,
            self.observer,
            0,
            bet_before_simulation,
            in_simulation=False,
        )


if __name__ == "__main__":
    print("Testing combine_probabilities")
    for case in [[0.3, 0.7], [0.45, 0.55], [0.9, 0.5], [0.99, 0.5]]:
        print("\n\nCase:", case)
        print("Combined prob:", combine_probabilities(case, 1))
