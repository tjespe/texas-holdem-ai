import os
from State import State
import numpy as np
from math import factorial
from typing import Callable, Union
import numpy as np
from scipy.stats import truncnorm
from time import sleep
import matplotlib.pyplot as plt
from time import time


def _copy_and_modify(state: State, **kwargs):
    """
    Creates a new state with the same properties as the given state: State,
    but with the properties in kwargs updated.
    """
    return State(
        kwargs.get("public_cards", state.public_cards),
        kwargs.get("player_piles", state.player_piles),
        kwargs.get("pot", state.pot),
        kwargs.get("current_player_i", state.current_player_i),
        kwargs.get("current_bets", state.current_bets),
        kwargs.get("player_has_played", state.player_has_played),
        kwargs.get("folded_players", state.folded_players),
        kwargs.get("first_better_i", state.first_better_i),
    )


def _generate_possible_draws(state: State, n_cards: int, n_permutations: int = 100):
    """
    Generate possible draws of n_cards cards given a state.
    :param state: The current state
    :param n_cards: The number of cards to draw
    :param n_permutations: The number of permutations to generate (if possible)
    TODO: Should this take the perspective of the current player, and exclude cards that player has on hand?
    """
    result = set()
    possible_cards = set(range(52)) - set(state.public_cards)
    max_possible_permutations = factorial(len(possible_cards)) // factorial(
        len(possible_cards) - n_cards
    )
    permutations = min(n_permutations, max_possible_permutations)
    possible_cards = list(possible_cards)
    while len(result) < permutations:
        np.random.shuffle(possible_cards)
        result.add(tuple(possible_cards[:n_cards]))
    return result


def _get_big_blind():
    big_blind = os.getenv("BIG_BLIND")
    if big_blind is None:
        print(
            "Warning: BIG_BLIND environment variable not set, using default value of 2"
        )
        big_blind = 2
    big_blind = int(big_blind)
    return big_blind


def _generate_general_betting_distribution(state: State):
    """
    Generate a general uninformed distribution for betting.
    """
    current_player_i = state.current_player_i
    current_bet = state.current_bets[current_player_i]
    player_pile = state.player_piles[current_player_i]
    if state.folded_players[current_player_i]:
        return 0
    call_bet = max(state.current_bets) - current_bet
    all_in_bet = player_pile
    distribution = np.ones(all_in_bet + 1)
    # Make higher bets less likely
    likelihood_decay = 0.5  # Higher values make higher bets less likely
    distribution = distribution / (
        (np.arange(distribution.shape[0]) + 1) * likelihood_decay
    )
    # Ensure illegal raises are not made
    distribution[call_bet + 1 : call_bet + 1 + _get_big_blind()] = 0
    # Ensure too low bets are not made
    distribution[:call_bet] = 0
    # Add a chance of folding
    distribution[0] = 1
    # Add a chance of calling
    distribution[call_bet] = 1
    # Ensure sum of distribution is 1
    distribution = distribution / np.sum(distribution)
    # Plotting for debugging
    # plt.plot(
    #     distribution,
    #     label=f"Player {current_player_i}, {len(state.public_cards)} cards",
    # )
    return distribution


def _random_betting_fn(state: State):
    """
    A random betting function, used for generating successor states
    :param state: The current state
    :return: The bet to make
    """
    distribution = _generate_general_betting_distribution(state)
    return np.random.choice(len(distribution), p=distribution)


def _update_tuple(t: tuple, i: int, new_value: any):
    """
    Returns a new tuple where the value at index i is replaced with new_value.
    """
    return t[:i] + (new_value,) + t[i + 1 :]


def all_players_are_done(state: State):
    """
    Checks if the table is ready for more cards.
    This is the case when all players have had their turn, and the bets of the non-folded players are equal.
    """
    return (
        np.all(state.player_has_played)
        and len(set(np.array(state.current_bets)[~np.array(state.folded_players)])) == 1
    )


def generate_successor_states(
    state: State,
    max_successors=100,
    betting_fn: Callable[["State"], int] = _random_betting_fn,
) -> list["State"]:
    """
    Generate possible successor states from the given state.
    If the current state is a state where a player has to make a decision, then the number of successor states
    will be limited by max_successors.
    :param state: The current state
    :param max_successors: The maximum number of successor states to generate
    :param relative_bet_distribution: The distribution to sample from when generating bets
    """
    active_players = ~np.array(state.folded_players)
    if np.sum(active_players) == 1:
        # Only one player left, no more decisions to be made
        return []
    elif np.any(np.array(state.player_piles)[active_players] == 0):
        # A player has gone all in, no more decisions to be made, go to showdown
        return []
    elif all_players_are_done(state):
        # It is time for more cards or to go to showdown
        if state.public_cards == ():
            return [
                add_cards(state, draw)
                for draw in _generate_possible_draws(state, 3, max_successors)
            ]
        elif len(state.public_cards) < 5:
            return [
                add_cards(state, draw)
                for draw in _generate_possible_draws(state, 1, max_successors)
            ]
        else:
            # Go to showdown (no successor states)
            return []
    else:
        # Check if the current player has folded
        if state.folded_players[state.current_player_i]:
            return [skip_current_player(state)]
        check_bet = max(state.current_bets) - state.current_bets[state.current_player_i]
        # A player has to make a decision, generate `max_successors` possible decisions
        return [
            place_bet(state, bet)
            for bet in set(
                # Ensure folding is one of the options
                [0]
                # Ensure checking is one of the options
                + [check_bet]
                # Generate other random bets
                + [betting_fn(state) for _ in range(max_successors)]
            )
        ]


def add_cards(state: State, cards: tuple[int], skip_integrity_check=False) -> State:
    if not skip_integrity_check and not all_players_are_done(state):
        raise Exception("Cannot add cards when players have not finished betting")
    return _copy_and_modify(
        state,
        public_cards=state.public_cards + cards,
        current_bets=tuple(0 for _ in range(state.n_players)),
        current_player_i=state.first_better_i,
        player_has_played=tuple(False for _ in range(state.n_players)),
    )


def fold_current_player(state: State) -> State:
    return _copy_and_modify(
        state,
        current_player_i=state.next_player,
        folded_players=_update_tuple(
            state.folded_players, state.current_player_i, True
        ),
        player_has_played=_update_tuple(
            state.player_has_played, state.current_player_i, True
        ),
    )


def place_bet(state: State, bet: int):
    min_required_bet = (
        max(state.current_bets) - state.current_bets[state.current_player_i]
    )
    if bet == 0 and min_required_bet > 0:
        return fold_current_player(state)
    if bet < min_required_bet:
        raise Exception("Bet is too low")
    big_blind = os.getenv("BIG_BLIND")
    if big_blind is None:
        print(
            "Warning: BIG_BLIND environment variable not set, using default value of 2"
        )
        big_blind = 2
    big_blind = int(big_blind)
    if bet > min_required_bet and bet < min_required_bet + big_blind:
        print(
            "Warning: Raising by less than the big blind is not allowed. Treating as a call instead."
        )
        bet = min_required_bet
    player_pile = state.player_piles[state.current_player_i]
    if bet > player_pile:
        raise Exception("Bet is higher than the player's pile")
    return _copy_and_modify(
        state,
        current_player_i=state.next_player,
        current_bets=_update_tuple(
            state.current_bets,
            state.current_player_i,
            state.current_bets[state.current_player_i] + bet,
        ),
        pot=state.pot + bet,
        player_has_played=_update_tuple(
            state.player_has_played, state.current_player_i, True
        ),
        player_piles=_update_tuple(
            state.player_piles,
            state.current_player_i,
            player_pile - bet,
        ),
    )


def skip_current_player(state: State):
    if not state.folded_players[state.current_player_i]:
        raise Exception("Only folded players can be skipped")
    return _copy_and_modify(
        state,
        current_player_i=state.next_player,
        player_has_played=_update_tuple(
            state.player_has_played, state.current_player_i, True
        ),
    )


if __name__ == "__main__":
    state = State.generate_root_state(3)
    while state:
        print(state.get_cli_repr())
        successors = generate_successor_states(state, max_successors=1)
        if not successors:
            print("No more successors")
            break
        state = np.random.choice(successors)
        sleep(1)
    # plt.legend()
    # plt.show()
