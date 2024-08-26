import math
import numpy as np
from State import State
from cpp_poker.cpp_poker import CardCollection, CheatSheet, Oracle, Card
from PlayerABC import Player
from helpers import get_random_betting_distribution

log_file = open("AwareRationalPlayer.log", "a")


def debug_print(*args, **kwargs):
    # print(*args, **kwargs)
    print(*args, **kwargs, file=log_file, flush=True)


class AwareRationalPlayer(Player):
    """
    Similar to RationalPlayer, but bases winning probability on a combination of
    cards and bets from other players.

    :param name: Name of the player
    :param randomness: The probability of making a random move
    :param alpha: How much the card based winning probability decay as the pot grows (0-1, higher is more decay)
    """

    def __init__(
        self, name: str = "Rasmus", randomness=0.1, alpha=0.3, aggression_sensitivity=1
    ):
        super().__init__()
        self.name = name
        self.raises_per_player = None
        self.implied_winning_probs = None
        self.randomness = randomness
        self.alpha = alpha
        # Used for registering the number of aggressive actions per player per game
        # Dimensions: n_games x n_players
        self.aggression_matrix = None
        # Used for registering the number of total actions per player
        # Dimensions: n_games x n_players
        self.actions_matrix = None
        self.aggression_sensitivity = aggression_sensitivity
        self.called_bluff = False

    def _ensure_vars_initialized(self, n_players):
        if self.raises_per_player is None:
            # Start with a small number (1) to avoid division by zero
            self.raises_per_player = np.ones(n_players)
        if self.implied_winning_probs is None:
            self.implied_winning_probs = np.full(n_players, fill_value=np.nan)
        if self.aggression_matrix is None:
            self.aggression_matrix = np.zeros((1, n_players))
        if self.actions_matrix is None:
            self.actions_matrix = np.zeros((1, n_players))

    def round_over(self, state: State):
        self.raises_per_player = None
        self.implied_winning_probs = None
        self._ensure_vars_initialized(state.n_players)
        # Add row of zeros to the action matrices to allow for values for next game
        self.aggression_matrix = np.vstack(
            [self.aggression_matrix, np.zeros(state.n_players)]
        )
        self.actions_matrix = np.vstack(
            [self.actions_matrix, np.zeros(state.n_players)]
        )
        self.called_bluff = False

    def get_relative_aggression(self, player_i):
        total_games = self.actions_matrix.shape[0]
        weight = np.arange(total_games)[:, np.newaxis]
        weight = weight / total_games
        weighted_actions_matrix = self.actions_matrix * weight
        weighted_aggression_matrix = self.aggression_matrix * weight
        actions_this_game = weighted_actions_matrix[-1, player_i]
        if not actions_this_game:
            return 1.0
        aggression_this_game = weighted_aggression_matrix[-1, player_i] / (
            actions_this_game
        )
        debug_print(f"Calculating relative aggression of player {player_i}")
        debug_print(
            f"Total aggression this game: {weighted_aggression_matrix[-1, player_i]}"
        )
        debug_print(f"Total actions this game: {actions_this_game}")
        debug_print(f"Aggressiveness this game: {aggression_this_game}")
        aggression_all_games = weighted_aggression_matrix[:, player_i].sum() / (
            weighted_actions_matrix[:, player_i].sum()
        )
        debug_print(
            f"Total aggression all games: {weighted_aggression_matrix[:, player_i].sum()}"
        )
        debug_print(
            f"Total actions all games: {weighted_actions_matrix[:, player_i].sum()}"
        )
        debug_print(f"Aggressiveness all games: {aggression_all_games}")
        rel_aggression = aggression_this_game / aggression_all_games
        debug_print(f"Relative aggression: {rel_aggression}")
        return rel_aggression

    def get_aggression_index(self, state: State):
        # Calculate an aggression index based on how aggressive the opponent's have been
        # in the current game compared to their average aggression
        relative_aggression_per_player = []
        for player_i in range(state.n_players):
            if player_i == state.current_player_i:
                continue
            if state.player_is_folded[player_i]:
                continue
            relative_aggression_per_player.append(
                self.get_relative_aggression(player_i)
            )
        if not relative_aggression_per_player:
            return 0
        return np.mean(relative_aggression_per_player)

    def classify_action(self, state: State, bet: int):
        """
        Classify aggression of action based on the size of the bet.
        Definitions:
        - Fold: 0
        - Call: 0.5
        - Bets: 0.5-1.5 (based on size)
        """
        call_bet = max(state.bet_in_stage) - state.bet_in_stage[state.current_player_i]
        if bet < call_bet:  # i.e. fold
            return 0
        if bet == call_bet:
            return 0.5
        coef = bet / state.pot
        debug_print(f"Bet: {bet}, pot: {state.pot}, coef: {coef}")
        return min(1.5, 0.5 + coef)

    def observe_bet(self, from_state: State, bet: int):
        self._ensure_vars_initialized(from_state.n_players)
        player_i = from_state.current_player_i
        call_bet = max(from_state.bet_in_stage) - from_state.bet_in_stage[player_i]
        if bet > call_bet:
            self.raises_per_player[player_i] += bet - call_bet
        implied_winning_prob = bet / from_state.pot
        if self.implied_winning_probs[player_i]:
            self.implied_winning_probs[player_i] = 0
        self.implied_winning_probs[player_i] = max(
            self.implied_winning_probs[player_i], implied_winning_prob
        )
        aggression = self.classify_action(from_state, bet)
        self.aggression_matrix[-1, player_i] += aggression
        self.actions_matrix[-1, player_i] += 1

    def get_winning_prob_based_on_raises(self, state: State):
        # Simple model assuming a 1-1 relationship between raises and winning probability
        self._ensure_vars_initialized(state.n_players)
        winning_probs = self.raises_per_player / self.raises_per_player.sum()
        debug_print(f"Raises per player: {self.raises_per_player}")
        debug_print(f"Raise based winning probs: {winning_probs}")
        return winning_probs[state.current_player_i]

    def get_implied_winning_prob(self, state: State):
        self._ensure_vars_initialized(state.n_players)
        winning_probs = self.implied_winning_probs / np.nansum(
            self.implied_winning_probs
        )
        return winning_probs[state.current_player_i]

    def evaluate_bluff_chance(self, self_i):
        # Attempt to calculate the chance that the other players are bluffing
        chances = []
        for player_i, implied_prob in enumerate(self.implied_winning_probs):
            if player_i == self_i:
                continue
            if np.isnan(implied_prob):
                continue
            debug_print(f"Player {player_i} has implied prob: {implied_prob}")
            # Cap probabilty at 130% to avoid too high bluff chances
            implied_prob = min(implied_prob, 1)
            # Estimate a chance for bluffing based on the implied probability
            bluff_chance = 0.9 - 0.7 * (1 - implied_prob) ** 0.1
            debug_print(f"Player {player_i} has implied prob: {implied_prob}")
            debug_print(f"Player {player_i} has bluff chance: {bluff_chance}")
            # Cap bluff chance at 0%
            bluff_chance = max(bluff_chance, 0)
            debug_print(f"Player {player_i} has bluff chance: {bluff_chance}")
            chances.append(bluff_chance)
        if not chances:
            return 0
        return np.nanmax(chances)

    def play(self, state: State) -> int:
        debug_print(state.get_cli_repr())
        current_player_i = state.current_player_i
        if state.player_is_folded[current_player_i]:
            return 0
        current_bet = state.bet_in_stage[current_player_i]
        call_bet = max(state.bet_in_stage) - current_bet
        card_based_winning_prob = CheatSheet.get_winning_probability(
            CardCollection(self.hand),
            CardCollection(state.public_cards),
            state.player_is_active.sum(),
        )
        winning_prob = card_based_winning_prob
        debug_print(f"Card based winning prob: {winning_prob}")
        # Put less weight on card_winning_prob the more is in the pot
        pot_factor = (state.pot - 2 * state.big_blind) / state.big_blind
        winning_prob = winning_prob / (1 + self.alpha * np.log(1 + pot_factor))
        debug_print(f"Adjusted card based winning prob: {winning_prob}")
        raise_based_winning_prob = self.get_winning_prob_based_on_raises(state)
        debug_print(f"Raise based winning prob: {raise_based_winning_prob}")
        # Only adjust winning prob based on raises if it's lower than card based
        if raise_based_winning_prob < winning_prob:
            winning_prob = np.nanmean([winning_prob, raise_based_winning_prob])
        debug_print(f"Winning prob adjusted for raises: {winning_prob}")
        aggression_index = self.get_aggression_index(state)
        over_aggression = max(aggression_index - 1, 0)
        debug_print(f"Aggression index: {aggression_index}")
        debug_print(f"Over-aggression: {over_aggression}")
        # Subtract over-aggression from winning prob
        winning_prob = max(
            winning_prob - over_aggression * self.aggression_sensitivity, 0
        )
        debug_print(f"Winning probability adjusted for aggression: {winning_prob}")
        debug_print(
            f"Machine hand: {str(Card(self.hand[0]))} {str(Card(self.hand[1]))}"
        )
        rational_max = winning_prob * state.pot
        debug_print(f"Rational max: {rational_max}")
        avg_forced_loss = (state.big_blind + state.small_blind) / state.n_players
        rational_max += avg_forced_loss
        debug_print(f"Rational max adjusted for blinds: {rational_max}")
        if call_bet > rational_max:
            opponent_bluff_chance = self.evaluate_bluff_chance(current_player_i)
            debug_print(f"Opponent bluff chance: {opponent_bluff_chance}")
            rand_threshold = opponent_bluff_chance * card_based_winning_prob
            debug_print(
                f"Rand threshold for responding despite exceeding rational: {rand_threshold}"
            )
            # Randomize whether to call or fold based on bluff chance
            if np.random.rand() < rand_threshold:
                debug_print("Assuming bluff")
                self.called_bluff = True
                return call_bet
            if self.called_bluff and card_based_winning_prob > 0.5:
                debug_print("Assuming continued bluff and calling")
                return call_bet
            debug_print("Assuming rational")
            return 0

        if math.isinf(rational_max):
            # Don't know why this happens, but it does
            rational_max = 0

        max_allowed_bet = Oracle.get_max_bet_allowed(
            state.player_has_played,
            state.current_player_i,
            state.bet_in_stage,
            state.player_piles,
            state.player_is_active,
        )
        max_bet = min(int(rational_max), max_allowed_bet)
        # Randomize what to do based personal bluff inclination
        if np.random.rand() < self.randomness:
            debug_print("Random move")
            max_bet = min(state.pot, max_allowed_bet)

        # Return random int between call_bet and rational_max
        distribution = get_random_betting_distribution(
            call_bet, max_bet, state.big_blind, always_add_fold_chance=False
        )
        for i, d in enumerate(distribution):
            debug_print(f"Bet: {i}, prob: {d}")
        return np.random.choice(len(distribution), p=distribution)
