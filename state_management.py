import os
from PlayerABC import Player
from RandomPlayer import RandomPlayer
from State import State
import numpy as np
from math import factorial
from typing import Callable
import numpy as np
from time import sleep

import oracle


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
        kwargs.get("big_blind", state.big_blind),
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


def _update_tuple(t: tuple, i: int, new_value: any):
    """
    Returns a new tuple where the value at index i is replaced with new_value.
    """
    return t[:i] + (new_value,) + t[i + 1 :]


def generate_root_state(
    n_players: int, pile_size: int = 100, big_blind: int = 2, first_better_i: int = 0
):
    return State(
        public_cards=(),
        player_piles=tuple(pile_size for _ in range(n_players)),
        pot=0,
        current_player_i=first_better_i,
        current_bets=tuple(0 for _ in range(n_players)),
        folded_players=tuple(False for _ in range(n_players)),
        first_better_i=first_better_i,
        player_has_played=tuple(False for _ in range(n_players)),
        big_blind=big_blind,
    )


def generate_successor_states(
    state: State,
    max_successors=100,
    betting_fn: Callable[["State"], int] = RandomPlayer().play,
) -> list["State"]:
    """
    Generate possible successor states from the given state.
    If the current state is a state where a player has to make a decision, then the number of successor states
    will be limited by max_successors.
    :param state: The current state
    :param max_successors: The maximum number of successor states to generate
    :param relative_bet_distribution: The distribution to sample from when generating bets
    """
    if state.is_terminal:
        return []
    elif state.all_players_are_done:
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
    if not skip_integrity_check and not state.all_players_are_done:
        raise Exception("Cannot add cards when players have not finished betting")
    return _copy_and_modify(
        state,
        public_cards=state.public_cards + tuple(cards),
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
    if bet > min_required_bet and bet < min_required_bet + state.big_blind:
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
    if (
        not state.folded_players[state.current_player_i]
        and state.player_piles[state.current_player_i] >= state.big_blind
    ):
        raise Exception("Only bust or folded players can be skipped")
    return _copy_and_modify(
        state,
        current_player_i=state.next_player,
        player_has_played=_update_tuple(
            state.player_has_played, state.current_player_i, True
        ),
    )


def end_round(state: State, players: list[Player]):
    """
    End the round and distribute the pot to the winner(s).
    """
    if not state.is_terminal:
        raise Exception("The round is not over yet")
    winners = oracle.find_winner(state.public_cards, players, state.folded_players)
    pot_per_winner = state.pot // len(winners)
    new_piles = tuple(
        state.player_piles[i] + (pot_per_winner if player in winners else 0)
        for i, player in enumerate(players)
    )
    bust_players = set()
    for i, pile in enumerate(new_piles):
        if pile < state.big_blind:
            bust_players.add(players[i])
    new_state = _copy_and_modify(
        generate_root_state(len(players)), player_piles=new_piles
    )
    return new_state, bust_players


if __name__ == "__main__":
    state = generate_root_state(3)
    while state:
        print(state.get_cli_repr())
        successors = generate_successor_states(state, max_successors=1)
        if not successors:
            print("Round over")
            break
        state = np.random.choice(successors)
        sleep(1)
    # plt.legend()
    # plt.show()
