import pandas as pd
from State import State
from StateNode import StateNode
from resolver import resolve
import numpy as np
from cpp_poker.cpp_poker import Hand, Oracle
from datetime import datetime

def generate_data_point(stage: State.StageType, end_stage: State.StageType, stage_of_stage=None):
    """
    Generate training data for a given stage.

    Args:
        stage: The stage at which to generate training data.
    """
    if stage == "preflop":
        n_cards = 0
    elif stage == "flop":
        n_cards = 3
    elif stage == "turn":
        n_cards = 4
    elif stage == "river":
        n_cards = 5
    elif stage == "terminal":
        raise ValueError("No need to generate data for terminal states.")
    else:
        raise ValueError("Invalid stage")
    n_players = 2
    big_blind = 2
    pot = np.random.randint(0, 1000)
    if (pot % 2) == 1:
        pot += 1
    bet_in_game = (pot // 2, pot // 2)
    player_piles = tuple(np.random.randint(0, 1000, n_players))
    if stage_of_stage is None:
        stage_of_stage = np.random.choice(
            ["first_bet", "respond", "respond_to_raise"],
            # More often respond to raise because that is cheaper to simulate
            p=[0.05, 0.1, 0.85],
        )
    if stage_of_stage == "first_bet":
        bet_in_stage = (0, 0)
        player_has_played = (False, False)
        first_better_i = 0  # The first better is the player
    elif stage_of_stage == "respond":
        player_has_played = (False, True)  # The opponent has played
        first_better_i = 1  # The first better was the opponent
        max_raised_by = min(
            pot,
            Oracle.get_max_bet_allowed(
                (False, False),  # No one had played yet when the raise was made
                1,  # The player who raised
                bet_in_game,  # The current bets before the raise
                player_piles,  # The player piles before the raise
                (True, True),  # Both players were active before the raise
            ),
        )
        raised_by = np.random.randint(0, max_raised_by)
        bet_in_stage = (0, raised_by)
        bet_in_game = (pot // 2, pot // 2 + raised_by)
    elif stage_of_stage == "respond_to_raise":
        player_has_played = (True, True)
        first_better_i = 0
        max_initial_bet = min(
            pot,
            Oracle.get_max_bet_allowed(
                (False, False),  # No one had played yet when the raise was made
                0,  # The player who raised
                bet_in_game,  # The current bets before the raise
                player_piles,  # The player piles before the raise
                (True, True),  # Both players were active before the raise
            ),
        )
        initial_bet = np.random.randint(0, max_initial_bet)
        bet_in_stage = (initial_bet, initial_bet)
        bet_in_game = (pot // 2 + initial_bet, pot // 2 + initial_bet)
        max_opp_raise = min(
            pot,
            Oracle.get_max_bet_allowed(
                (
                    True,
                    False,
                ),  # The opponent had not played yet when the raise was made
                1,  # The player who raised
                bet_in_game,  # The current bets before the raise
                player_piles,  # The player piles before the raise
                (True, True),  # Both players were active before the raise
            ),
        )
        if big_blind >= max_opp_raise:
            opp_raise = 0
        else:
            opp_raise = np.random.randint(big_blind, max_opp_raise)
        bet_in_game = (pot // 2 + initial_bet, pot // 2 + initial_bet + opp_raise)
        bet_in_stage = (initial_bet, initial_bet + opp_raise)
    state = State(
        public_cards=tuple(np.random.choice(52, n_cards, replace=False)),
        player_piles=player_piles,
        current_player_i=0,
        bet_in_game=bet_in_game,
        bet_in_stage=bet_in_stage,
        player_has_played=player_has_played,
        folded_players=(False, False),
        first_better_i=first_better_i,
        big_blind=2,
    )
    if state.current_player_i != 0:
        raise ValueError("Wrong state setup, expected current player to be 0.")
    if state.all_players_are_done:
        print(state.get_cli_repr())
        raise ValueError("Wrong state setup, expected not all players to be done.")
    rP = np.random.rand(len(Hand.COMBINATIONS))
    rP /= rP.sum()
    rO = np.random.rand(len(Hand.COMBINATIONS))
    rO /= rO.sum()
    ranges = [rP, rO]
    print("Generating data point for state:")
    print(state.get_cli_repr())
    print("Stage:", stage)
    print("Stage of stage:", stage_of_stage)
    action, child_state, updated_ranges, df_row = resolve(
        state,
        ranges,
        end_stage,
        end_depth=100,  # Not used as end_stage is used instead
        max_successors_at_action_nodes=5,
        max_successors_at_chance_nodes=100,
        max_simulations=1000,
    )
    return df_row


def save_df(data, fname: str):
    df = pd.DataFrame(data, columns=StateNode.get_df_headers())
    df.to_parquet(fname)


def generate_training_data(
    stage: State.StageType, end_stage: State.StageType, n_points: int, stage_of_stage=None
):
    """
    Generate training data for a given stage.

    Args:
        stage: The stage at which to generate training data.
        n_points: The number of data points to generate.
    """
    data = []
    fname = (
        "dfs/df_" + stage + "_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".parquet"
    )
    for i in range(n_points):
        print("Generating data point", i, "of", n_points)
        data.append(generate_data_point(stage, end_stage, stage_of_stage))
        save_df(data, fname)
    save_df(data, fname)


if __name__ == "__main__":
    generate_training_data("river", "terminal", 1000, stage_of_stage="first_bet")
