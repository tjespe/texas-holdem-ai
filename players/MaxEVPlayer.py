from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Iterable, Literal, Union
import numpy as np
import pandas as pd
from State import State
from cpp_poker.cpp_poker import CardCollection, CheatSheet, Oracle
from PlayerABC import Player
from hidden_state_model.helpers import get_observer_with_all_data
from hidden_state_model.observer import Observer
from helpers import combine_probabilities
from state_management import add_cards, generate_successor_states, place_bet


log_file = open("stats/MaxEVPlayer.log", "a")

time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
persistent_observer = Observer(
    f"hidden_state_model/data/maxevplayer-{time_str}.parquet"
)


def debug_print(*args, **kwargs):
    print(" ", end="", flush=True)
    print(*args, **kwargs, file=log_file, flush=True)


class RandomResult:
    probs: np.ndarray
    values: np.ndarray

    def __init__(self, outcomes: Iterable[tuple[float, Union[float, "RandomResult"]]]):
        probs = []
        values = []
        for prob, value in outcomes:
            if isinstance(value, RandomResult):
                probs.extend(value.probs * prob)
                values.extend(value.values)
            else:
                probs.append(prob)
                values.append(value)
        self.probs = np.array(probs)
        self.values = np.array(values)
        assert len(self.probs) == len(self.values)
        assert np.all(self.probs >= 0)
        assert np.isclose(
            np.sum(self.probs), 1
        ), f"Sum of probabilities: {np.sum(self.probs)}"

    @property
    def ev(self):
        return np.dot(self.probs, self.values)

    @property
    def variance(self):
        return np.dot(self.probs, (self.values - self.ev) ** 2)

    @property
    def std(self):
        return np.sqrt(self.variance)

    @property
    def semi_variance(self):
        """Calculates the semi-variance (downside risk) as the variance of outcomes below the mean."""
        mean = self.ev
        downside_values = self.values[self.values < mean]
        downside_probs = self.probs[self.values < mean]
        if len(downside_values) == 0:
            return 0  # No downside outcomes
        semi_variance = np.dot(downside_probs, (downside_values - mean) ** 2)
        return semi_variance

    @property
    def semi_std(self):
        """Calculates the semi-standard deviation (downside risk) as the square root of the semi-variance."""
        return np.sqrt(self.semi_variance)

    @property
    def VaR_95(self):
        """
        Calculates Value at Risk (VaR) at 95% confidence level, meaning the value
        at the 5th percentile of the distribution, counting from the lowest value.
        A negative value means that there is a 5% chance of losing at least that much.
        A positive value means that there is a 95% chance of winning at least that much.
        """
        sorted_indices = np.argsort(self.values)
        sorted_values = self.values[sorted_indices]
        sorted_probs = self.probs[sorted_indices]
        cumulative_probs = np.cumsum(sorted_probs)
        var_index = np.searchsorted(cumulative_probs, 0.20)
        return sorted_values[var_index]

    @property
    def CVaR_95(self):
        """
        Calculates Conditional Value at Risk (CVaR) at 95% confidence level (expected shortfall).
        """
        var = self.VaR_95
        losses = self.values[self.values <= var]
        losses_probs = self.probs[self.values <= var]
        return np.dot(losses_probs, losses) / np.sum(losses_probs)

    def __repr__(self) -> str:
        return f"RandomResult({dict(zip(self.probs, self.values))})"

    def __str__(self) -> str:
        return f"{self.ev:.2f} ± {self.std:.2f}"

    def __mul__(self, other: float):
        return RandomResult((p, v * other) for p, v in zip(self.probs, self.values))


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
    risk_aversion: float
    title = "Tardy"

    def __init__(
        self,
        name: str = "Max Mekker",
        rel_weight_player_in_reg=2,
        rel_weight_opponent_in_reg=2,
        risk_aversion=1,
    ):
        super().__init__()
        self.name = name
        self.player_names = None
        self.observer = get_observer_with_all_data()
        self.player_probs = None
        self.predicted_ranks = None
        self.rel_weight_player_in_reg = rel_weight_player_in_reg
        self.rel_weight_opponent_in_reg = rel_weight_opponent_in_reg
        self.risk_aversion = risk_aversion

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
        print(".", end="", flush=True)
        res = self.predictor.predict_for_row(
            attribute,
            df_row,
            player_name,
            self.rel_weight_player_in_reg,
            self.name,
            self.rel_weight_opponent_in_reg,
            probabilities=probabilities,
        )
        print("_", end="", flush=True)
        return res

    def prefit_model(
        self,
        attribute: Literal["prob", "rank", "action", "raise"],
        player_name: str,
        fit_async=False,
    ):
        self.predictor.prefit_model(
            attribute,
            player_name,
            self.rel_weight_player_in_reg,
            self.name,
            self.rel_weight_opponent_in_reg,
            async_fit=fit_async,
        )

    def prefit_all_models(self, fit_async=False):
        for attribute in ["prob", "rank", "action", "raise"]:
            for player_name in self.player_names:
                if player_name == self.name:
                    continue
                self.prefit_model(attribute, player_name, fit_async)

    def get_to_know_each_other(self, players: list[Player]):
        self.player_names = [p.name for p in players]
        self.player_types = [p.__class__.__name__ for p in players]
        self.player_probs = np.ones(len(self.player_names)) / len(self.player_names)
        self.predicted_ranks = np.zeros(len(self.player_names))
        self.prefit_all_models(fit_async=True)

    def round_over(self, state: State, prev_state: State):
        self.player_probs = np.array(state.player_is_active) / np.sum(
            state.player_is_active
        )
        self.predicted_ranks = np.zeros(len(state.player_is_active))

    def observe_bet(
        self, from_state: State, bet: int, to_state: State, was_blind=False
    ):
        # Don't do anything if we have folded
        if from_state.player_is_folded[self.index]:
            return
        if was_blind:
            return
        player_i = from_state.current_player_i
        if player_i == self.index:
            return
        player_name = self.player_names[player_i]
        player_type = self.player_types[player_i]
        debug_print("Observing bet from", player_name, "of", bet)
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
        if len(generate_successor_states(from_state)) > 1:
            self.player_probs[player_i] = self.predict("prob", df_row, player_name)
            debug_print(
                f"Predicted prob for {self.player_names[player_i]}:",
                self.player_probs[player_i],
            )
            self.predicted_ranks[player_i] = self.predict("rank", df_row, player_name)
        else:
            debug_print("There was only one possible action, so not updating beliefs")

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
        observer: Union[Observer, None] = None,
        print_prefix: str = "",
    ) -> RandomResult:
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

        Returns:
            RandomResult: Object representing all simulated outcomes and their probabilities.
        """
        if observer is None:
            # Generate an observer with only the necessary data
            relevant_states = []
            s = state
            while s is not None:
                relevant_states.append(s.id)
                s = s.prev_state
            observer = self.observer.clone_with_filtered_df(
                lambda df: df[df.index.isin(relevant_states)]
            )
        # Handle game over
        if state.is_terminal:
            bet_in_simulation = state.bet_in_game[self.index] - bet_before_simulation
            if state.player_is_folded[self.index]:
                # In this case, we lose everything we have bet since the beginning of the simulation
                value = -bet_in_simulation
                debug_print(print_prefix, f"End: we folded, value:", value)
                return RandomResult([(1, value)])
            if sum(state.player_is_active) == 1:
                # In this case, we win the pot.
                # We don't count anything we have bet during the simulation as a win.
                # The opponent folding gives us a great payoff, but it's a highly risky strategy,
                # and if we use it too often, the opponent will exploit it, thus we make some
                # adjustments here.
                fold_discount = 0.8
                value_if_win = (state.pot - bet_in_simulation) * fold_discount
                result = RandomResult([(1, value_if_win)])
                debug_print(
                    print_prefix, f"End: opponent folded, using result: ", str(result)
                )
                return RandomResult([(1, value_if_win)])
            # In this case, we have a showdown
            winning_prob = combine_probabilities(player_probs, self.index)
            value_if_win = state.pot - bet_in_simulation
            value_if_loss = -bet_in_simulation
            result = RandomResult(
                [
                    (winning_prob, value_if_win),
                    (1 - winning_prob, value_if_loss),
                ]
            )
            debug_print(
                print_prefix,
                f"End: showdown, winning prob: {winning_prob}, value if win: {value_if_win}, value if loss: {value_if_loss}, EV: {result.ev}",
            )
            return result

        # Handle table needs card
        if state.all_players_are_done:
            n_cards = 3 if state.stage == "preflop" else 1
            return self.simulate_ev(
                # Add a card to progress the game although the card should not matter
                add_cards(state, tuple(range(n_cards))),
                bet_before_simulation,
                [*player_probs],
                [*predicted_ranks],
                observer,
                print_prefix,
            )

        # Handle own turn
        if state.current_player_i == self.index:
            bet, result = self._play(
                state,
                player_probs,
                predicted_ranks,
                True,
                bet_before_simulation,
                observer,
                print_prefix,
            )
            debug_print(
                print_prefix,
                "Choosing bet:",
                bet,
                "at stage",
                state.stage,
                "EV:",
                result.ev,
            )
            return result

        # Handle opponent turn
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
        actions, distrib = self.predict(
            "action",
            df_row,
            player_name,
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
        can_check = call_bet == 0
        can_call = call_bet <= max_allowed
        possible_actions = ["fold", "check", "call", "raise"]
        p_per_action = dict(zip(actions, distrib))
        if not can_raise:
            possible_actions.remove("raise")
            raise_p = p_per_action.pop("raise")
            p_per_action["call"] += raise_p
        if not can_check:
            possible_actions.remove("check")
            check_p = p_per_action.pop("check")
            p_per_action["fold"] += 0.5 * check_p
            p_per_action["call"] += 0.5 * check_p
        if not can_call:
            possible_actions.remove("call")
            call_p = p_per_action.pop("call")
            p_per_action["check"] += call_p
        # Always reduce fold chance to avoid relying on the opponent folding
        # as that is a very risky strategy.
        p_per_action["fold"] *= 0.3

        # Set an appropriate threshold for which actions to consider to limit
        # the branching factor of the simulation tree.
        prob_threshold = 0.2
        if state.stage == "river":
            prob_threshold = 0
        if state.stage == "preflop" or state.stage == "flop":
            prob_threshold = 0.4

        # Ensure we get at least 1 non-fold action, because otherwise, we will simulate
        # a fold with 100% probability and no variance, making the path unrealistically good.
        min_prob_thresh = max(
            p for action, p in p_per_action.items() if action != "fold"
        )
        debug_print(
            print_prefix,
            "Raw actions:",
            actions,
            "Raw distrib:",
            distrib,
            "Modified distrib:",
            p_per_action,
            "Prob threshold:",
            prob_threshold,
            "Min prob thresh:",
            min_prob_thresh,
        )
        if prob_threshold > min_prob_thresh:
            prob_threshold = min_prob_thresh
        debug_print("Adjusted prob threshold:", prob_threshold)
        mapped_actions = []
        mapped_probs = []
        results: list[RandomResult] = []
        for action, prob in p_per_action.items():
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
            elif action == "call":
                bet = call_bet
                if bet not in mapped_actions:
                    mapped_actions.append(bet)
                    mapped_probs.append(prob)
                else:
                    i = mapped_actions.index(bet)
                    mapped_probs[i] += prob
            elif action == "raise":
                amount = int(self.predict("raise", df_row, player_name))
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
        mapped_probs = np.array(mapped_probs)
        mapped_probs /= np.sum(mapped_probs)
        for bet in mapped_actions:
            observer.retrofill_action(state, bet)
            updated_df_row = observer.get_processed_df_row(state.id)
            # If the player had a choice and chose this action, we need to update the
            # probabilities and ranks for the player.
            if len(mapped_actions) > 1:
                player_probs[player_i] = self.predict(
                    "prob", updated_df_row, player_name
                )
                predicted_ranks[player_i] = self.predict(
                    "rank", updated_df_row, player_name
                )
            results.append(
                self.simulate_ev(
                    place_bet(state, bet),
                    bet_before_simulation,
                    [*player_probs],
                    [*predicted_ranks],
                    observer,
                    print_prefix + f">[o{bet}]",
                )
            )
        result = RandomResult(zip(mapped_probs, results))
        debug_print(
            print_prefix,
            "Combined results:",
            dict(zip(mapped_actions, [str(r) for r in results])),
            "with probs:",
            mapped_probs,
            "Result:",
            result,
        )
        return result

    def _play(
        self,
        state: State,
        player_probs: list[float],
        predicted_ranks: list[int],
        in_simulation: bool,
        bet_before_simulation=None,
        observer: Union[Observer, None] = None,
        print_prefix=None,
    ) -> tuple[int, RandomResult]:
        if state.player_is_folded[self.index]:
            return 0
        if bet_before_simulation is None:
            bet_before_simulation = state.bet_in_game[self.index]
        current_bet = state.bet_in_stage[self.index]
        call_bet = max(state.bet_in_stage) - current_bet
        if not in_simulation:
            debug_print("Own hand:", CardCollection(self.hand).str())
            debug_print("Card based prob:", player_probs[self.index])

        max_allowed_bet = Oracle.get_max_bet_allowed(
            state.player_has_played,
            state.current_player_i,
            state.bet_in_stage,
            state.player_piles,
            state.player_is_active,
        )

        possibilities = {0, call_bet}
        min_raise = call_bet + state.big_blind
        can_raise = call_bet < min_raise < max_allowed_bet
        if can_raise:
            raise_ops = 1
            if len(state.public_cards) > 3 and not in_simulation:
                raise_ops = 2
            pot_fractions = np.random.normal(0.5, 0.1, raise_ops)
            for pot_frac in pot_fractions:
                bet = int(pot_frac * state.pot)
                if bet < call_bet:
                    continue
                if bet < min_raise:
                    bet = min_raise
                if bet > max_allowed_bet:
                    bet = max_allowed_bet
                # If it's less than a big blind away from some other bet, don't add it
                if any(abs(bet - b) < state.big_blind for b in possibilities):
                    continue
                possibilities.add(bet)

        if len(possibilities) == 1 and not in_simulation:
            # If there is only one thing to do, and we are not in a simulation, do it
            return possibilities.pop(), None

        if in_simulation:
            results = {
                bet: self.simulate_ev(
                    place_bet(state, bet),
                    bet_before_simulation,
                    [*player_probs],
                    [*predicted_ranks],
                    observer,
                    print_prefix + f">[b{bet}]",
                )
                for bet in possibilities
            }
        else:
            with ThreadPoolExecutor() as executor:
                bcolors = ("\033[95m", "\033[94m", "\033[92m", "\033[93m", "\033[91m")
                futures = {
                    executor.submit(
                        self.simulate_ev,
                        place_bet(state, bet),
                        bet_before_simulation + bet,
                        [*player_probs],
                        [*predicted_ranks],
                        observer,
                        bcolors[i % len(bcolors)] + f"[T{i}] [b{bet}]",
                    ): bet
                    for i, bet in enumerate(possibilities)
                }

                # Gather results
                results = {bet: future.result() for future, bet in futures.items()}
                # Reset terminal color
                debug_print("\033[0m", end="")

        def get_opt_prio(x):
            bet_size: int = x[0]
            result: RandomResult = x[1]
            sd_sensitivity = self.risk_aversion / 2
            bet_size_sensitivity = self.risk_aversion / 2
            return (
                result.ev
                - sd_sensitivity * result.std
                - bet_size_sensitivity * bet_size
            )

        if not in_simulation:
            debug_print("Hand:", CardCollection(self.hand).str())
            debug_print("Card based winning prob:", player_probs[self.index])
            debug_print(
                "Combined winning prob:",
                combine_probabilities(player_probs, self.index),
            )
            stats_df = (
                pd.DataFrame(
                    {
                        "Bet": bet,
                        "Semi SD": result.semi_std,
                        "VaR": result.VaR_95,
                        "CVaR": result.CVaR_95,
                        "SD": result.std,
                        "EV": result.ev,
                        "SD penalty": -result.std * self.risk_aversion * 0.5,
                        "Bet size penalty": -bet * self.risk_aversion * 0.5,
                        "Prio": get_opt_prio((bet, result)),
                    }
                    for bet, result in results.items()
                )
                .set_index("Bet")
                .sort_index()
            )
            debug_print(stats_df)

        bet, result = max(results.items(), key=get_opt_prio)
        return bet, result

    def play(self, state: State) -> int:
        debug_print("\n\n")
        self.prefit_all_models()
        self.risk_aversion = np.random.normal(1, 0.05)
        debug_print("Using risk aversuon", self.risk_aversion)
        # Disable any df processing and fitting while we calculate the bet, because
        # we are not observing anything new anyway and it's just a waste of time.
        self.predictor.disable_fitting = True
        self.player_probs[self.index] = CheatSheet.get_winning_probability(
            CardCollection(self.hand),
            CardCollection(state.public_cards),
            state.player_is_active.sum(),
        )
        bet, _result = self._play(
            state,
            self.player_probs,
            self.predicted_ranks,
            False,
        )
        # Re-enable fitting
        self.predictor.disable_fitting = False
        # Only store observation if it's a heads-up game as this player is not
        # designed to play in multi-player games.
        if len(state.player_is_active) < 3:
            persistent_observer.observe_action(
                state,
                self.name,
                MaxEVPlayer.__name__,
                bet,
                [n for n in self.player_names if n != self.name],
                self.hand,
            )
        return bet


if __name__ == "__main__":
    print("Testing combine_probabilities")
    for case in [[0.3, 0.7], [0.45, 0.55], [0.9, 0.5], [0.99, 0.5]]:
        print("\n\nCase:", case)
        print("Combined prob:", combine_probabilities(case, 1))
